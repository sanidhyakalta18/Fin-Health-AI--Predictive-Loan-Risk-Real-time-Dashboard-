"""
Portfolio-level views: KPIs, mean default-risk gauge, and credit-score distribution.

Uses the same persisted RandomForest + StandardScaler as ``src/inference.py`` and
scores every row in ``data/raw/loan_data.csv``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.core.config import get_config
from src.ml.artifacts import load_artifacts
from src.ml.preprocessing import FEATURE_COLUMNS, validate_feature_columns

DATA_PATH = get_config().loan_data_path

# FICO-style tier boundaries (left-inclusive for coloring by midpoint).
_TIER_BOUNDS = (300, 580, 670, 740, 800, 850)
_TIER_COLORS = (
    "#dc2626",  # Poor
    "#d97706",  # Fair
    "#ca8a04",  # Good
    "#059669",  # Very good
    "#047857",  # Excellent
)

_CHART_FONT = "Inter, Segoe UI, system-ui, -apple-system, sans-serif"
_INK = "#334155"
_MUTED = "#64748b"
_GRID = "rgba(100, 116, 139, 0.18)"


def load_portfolio_df(path: Path | None = None) -> pd.DataFrame:
    """Load applicant portfolio table (expects training column names)."""
    p = path or DATA_PATH
    if not p.is_file():
        raise FileNotFoundError(
            f"Portfolio data not found at {p}. Run `python -m src.generate_data`."
        )
    df = pd.read_csv(p)
    validate_feature_columns(df)
    return df


def compute_default_probas(
    model: Any, scaler: Any, df: pd.DataFrame
) -> tuple[pd.DataFrame, np.ndarray]:
    """Return ``(df_clean, probs)`` with only complete feature rows and P(default)."""
    X = df[FEATURE_COLUMNS].copy()
    mask = X.notna().all(axis=1)
    df_clean = df.loc[mask].reset_index(drop=True)
    X_clean = df_clean[FEATURE_COLUMNS]
    X_scaled = scaler.transform(pd.DataFrame(X_clean, columns=FEATURE_COLUMNS))
    if not hasattr(model, "predict_proba"):
        raise TypeError("Model must implement predict_proba for portfolio scoring.")
    proba = model.predict_proba(X_scaled)
    classes = np.asarray(getattr(model, "classes_", np.arange(proba.shape[1])))
    pos = int(np.flatnonzero(classes == 1)[0]) if np.any(classes == 1) else min(1, proba.shape[1] - 1)
    probs = np.asarray(proba[:, pos], dtype=float)
    return df_clean, probs


def portfolio_kpis(
    df: pd.DataFrame,
    probs: np.ndarray,
    *,
    high_risk_threshold: float | None = None,
) -> dict[str, Any]:
    """Headline stats for the KPI strip (aligns lengths of df and probs)."""
    if len(df) != len(probs):
        raise ValueError("df and probs must have the same length.")
    threshold = get_config().high_risk_threshold if high_risk_threshold is None else high_risk_threshold
    out: dict[str, Any] = {
        "n_applicants": int(len(df)),
        "median_credit_score": float(df["Credit_Score"].median()),
        "high_risk_count": int((probs >= threshold).sum()),
        "mean_predicted_default_pct": float(np.mean(probs) * 100.0),
    }
    if "Default" in df.columns:
        out["actual_default_rate_pct"] = float(df["Default"].astype(float).mean() * 100.0)
    else:
        out["actual_default_rate_pct"] = None
    return out


def _fico_bar_color(score_mid: float) -> str:
    for i in range(len(_TIER_BOUNDS) - 1):
        lo, hi = _TIER_BOUNDS[i], _TIER_BOUNDS[i + 1]
        if lo <= score_mid < hi or (i == len(_TIER_BOUNDS) - 2 and lo <= score_mid <= hi):
            return _TIER_COLORS[i]
    return _TIER_COLORS[-1]


def build_portfolio_gauge_figure(
    mean_pred_prob: float,
    *,
    threshold_pct: float = 40.0,
    title: str = "Avg predicted default risk",
) -> go.Figure:
    """Gauge: mean model default probability vs portfolio benchmark."""
    value = float(np.clip(mean_pred_prob * 100.0, 0.0, 100.0))
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            number={"suffix": "%", "valueformat": ".1f"},
            delta={"reference": threshold_pct},
            title={"text": title, "font": {"size": 16}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": _MUTED},
                "bar": {"color": "#2563eb", "thickness": 0.22},
                "bgcolor": "rgba(255,255,255,0)",
                "borderwidth": 1,
                "bordercolor": "rgba(100, 116, 139, 0.28)",
                "steps": [
                    {"range": [0, 30], "color": "rgba(5, 150, 105, 0.22)"},
                    {"range": [30, 55], "color": "rgba(202, 138, 4, 0.24)"},
                    {"range": [55, 100], "color": "rgba(220, 38, 38, 0.20)"},
                ],
                "threshold": {
                    "line": {"color": "#0f766e", "width": 4},
                    "thickness": 0.85,
                    "value": threshold_pct,
                },
            },
        )
    )
    fig.update_layout(
        height=390,
        margin=dict(l=24, r=24, t=64, b=24),
        font=dict(family=_CHART_FONT, color=_INK),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def build_credit_score_histogram_figure(
    scores: pd.Series,
    *,
    bin_width: int = 20,
) -> go.Figure:
    """
    Credit score counts by fixed-width bins; each bar colored by FICO-style tier.

    Uses a single ``go.Bar`` with per-bin colors (equivalent to one trace per bin visually).
    Faint vertical bands mark tier boundaries.
    """
    s = pd.to_numeric(scores, errors="coerce").dropna()
    if s.empty:
        raise ValueError("No credit scores to plot.")

    edges = np.arange(300, 850 + bin_width, bin_width)
    counts, _ = np.histogram(s, bins=edges)
    centers = (edges[:-1] + edges[1:]) / 2.0
    colors = [_fico_bar_color(float(m)) for m in centers]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=centers,
            y=counts,
            width=bin_width * 0.92,
            marker_color=colors,
            marker_line_width=0,
            hovertemplate=(
                "Score bin center: %{x:.0f}<br>Count: %{y}<extra></extra>"
            ),
            name="Applicants",
        )
    )

    ymax = float(counts.max()) if len(counts) else 1.0
    y_annotate = min(ymax * 1.12, ymax + max(2.0, ymax * 0.08))

    shapes: list[dict[str, Any]] = []
    for lo, hi in zip(_TIER_BOUNDS[:-1], _TIER_BOUNDS[1:]):
        shapes.append(
            {
                "type": "rect",
                "xref": "x",
                "yref": "paper",
                "x0": float(lo),
                "x1": float(hi),
                "y0": 0,
                "y1": 1,
                "fillcolor": "rgba(100,116,139,0.06)",
                "line": {"width": 0},
                "layer": "below",
            }
        )

    boundary_labels = ("580 Fair", "670 Good", "740 V.Good", "800 Exc.")
    for xb, label in zip(_TIER_BOUNDS[1:-1], boundary_labels):
        shapes.append(
            {
                "type": "line",
                "xref": "x",
                "yref": "paper",
                "x0": float(xb),
                "x1": float(xb),
                "y0": 0,
                "y1": 1,
                "line": {"color": "rgba(100,116,139,0.52)", "width": 1, "dash": "dot"},
                "layer": "below",
            }
        )
        fig.add_annotation(
            x=float(xb),
            y=y_annotate,
            text=label,
            showarrow=False,
            font={"size": 10, "color": _MUTED, "family": _CHART_FONT},
        )

    fig.update_layout(
        title="Credit score distribution",
        xaxis_title="Credit score (bin center)",
        yaxis_title="Applicant count",
        bargap=0.08,
        height=430,
        margin=dict(l=58, r=28, t=78, b=62),
        font=dict(family=_CHART_FONT, color=_INK),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        shapes=shapes,
        showlegend=False,
        xaxis=dict(range=[300, 850], gridcolor=_GRID, zerolinecolor=_GRID),
        yaxis=dict(gridcolor=_GRID),
        hoverlabel=dict(
            bgcolor="#0f172a",
            bordercolor="rgba(255,255,255,0.12)",
            font=dict(color="#f8fafc", family=_CHART_FONT),
        ),
    )
    fig.update_yaxes(zeroline=True, zerolinewidth=1, zerolinecolor=_GRID)
    return fig


def build_portfolio_bundle(
    df: pd.DataFrame | None = None,
    *,
    high_risk_threshold: float | None = None,
    gauge_threshold_pct: float | None = None,
) -> tuple[dict[str, Any], go.Figure, go.Figure]:
    """
    Load data (if needed), score with persisted model, return KPIs + two Plotly figures.
    """
    config = get_config()
    df = load_portfolio_df() if df is None else df
    model, scaler = load_artifacts()
    df_used, probs_used = compute_default_probas(model, scaler, df)

    threshold = config.high_risk_threshold if high_risk_threshold is None else high_risk_threshold
    gauge_threshold = (
        config.portfolio_gauge_threshold_pct
        if gauge_threshold_pct is None
        else gauge_threshold_pct
    )
    kpis = portfolio_kpis(df_used, probs_used, high_risk_threshold=threshold)
    gauge = build_portfolio_gauge_figure(
        kpis["mean_predicted_default_pct"] / 100.0,
        threshold_pct=gauge_threshold,
    )
    hist = build_credit_score_histogram_figure(df_used["Credit_Score"], bin_width=20)
    return kpis, gauge, hist
