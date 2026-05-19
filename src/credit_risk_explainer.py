"""
SHAP explanations for the tree-based credit-risk model (scaled feature space).

Uses ``shap.TreeExplainer`` with interventional perturbation when a background
matrix is available, aligned with the same ``StandardScaler`` used at training.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import shap

from src.core.config import get_config
from src.ml.artifacts import load_artifacts
from src.ml.preprocessing import FEATURE_COLUMNS, raw_feature_matrix, validate_feature_columns

DATA_PATH = get_config().loan_data_path
_CHART_FONT = "Inter, Segoe UI, system-ui, -apple-system, sans-serif"
_INK = "#334155"
_GRID = "rgba(100, 116, 139, 0.18)"

# Readable y-axis labels (training columns unchanged in logic).
FEATURE_LABELS: dict[str, str] = {
    "Age": "Age",
    "Annual_Income": "Annual income",
    "Credit_Score": "Credit score",
    "Loan_Amount": "Loan amount",
    "Debt_to_Income_Ratio": "Debt-to-income (DTI)",
    "Employment_Years": "Employment years",
}


def load_background_raw(max_samples: int = 400, random_state: int = 42) -> np.ndarray:
    """
    Sample raw feature rows for interventional SHAP (same columns as training).
    """
    if not DATA_PATH.is_file():
        raise FileNotFoundError(
            f"Background data not found at {DATA_PATH}. "
            "Run `python -m src.generate_data` first."
        )
    df = pd.read_csv(DATA_PATH)
    validate_feature_columns(df)
    df = df[FEATURE_COLUMNS].dropna()
    if len(df) == 0:
        raise ValueError("No complete rows for SHAP background after dropna().")
    n = min(max_samples, len(df))
    df = df.sample(n=n, random_state=random_state)
    return df.to_numpy(dtype=np.float64)


def build_tree_explainer(
    model: Any,
    scaler: Any,
    *,
    background_raw: np.ndarray | None = None,
    max_samples: int = 400,
) -> shap.TreeExplainer:
    """Fit a ``TreeExplainer`` on scaled background data (interventional when supported)."""
    if background_raw is None:
        background_raw = load_background_raw(max_samples=max_samples)
    bg_scaled = scaler.transform(pd.DataFrame(background_raw, columns=FEATURE_COLUMNS))
    try:
        return shap.TreeExplainer(
            model,
            data=bg_scaled,
            feature_perturbation="interventional",
        )
    except TypeError:
        return shap.TreeExplainer(model, data=bg_scaled)


def build_shap_explainer_bundle(max_background_samples: int | None = None) -> tuple[shap.TreeExplainer, Any, Any]:
    """Load artifacts, background sample, and build explainer — suitable for ``st.cache_resource``."""
    config = get_config()
    sample_count = config.shap_background_samples if max_background_samples is None else max_background_samples
    model, scaler = load_artifacts()
    bg = load_background_raw(max_samples=sample_count, random_state=config.random_state)
    explainer = build_tree_explainer(model, scaler, background_raw=bg)
    return explainer, model, scaler


def _parse_shap_binary(
    shap_values: Any,
    expected_value: Any,
    class_index: int,
    row_index: int = 0,
) -> tuple[np.ndarray, float]:
    """Return (phi per feature, base value) for the requested class."""
    if isinstance(shap_values, list):
        arr = np.asarray(shap_values[class_index])
        if arr.ndim == 1:
            phi = arr
        else:
            phi = arr[row_index]
    else:
        arr = np.asarray(shap_values)
        if arr.ndim == 3:
            phi = arr[row_index, :, class_index]
        elif arr.ndim == 2:
            phi = arr[row_index]
        else:
            phi = arr.ravel()

    if isinstance(expected_value, list):
        base_arr = np.asarray(expected_value[class_index]).ravel()
    else:
        base_arr = np.asarray(expected_value).ravel()
    if base_arr.size > class_index:
        base = float(base_arr[class_index])
    else:
        base = float(base_arr[0])
    return phi.astype(float), base


def explain_credit_prediction(
    user_input: dict[str, Any],
    *,
    explainer: shap.TreeExplainer,
    scaler: Any,
    model: Any,
    feature_names: Sequence[str] | None = None,
    top_n: int = 10,
    class_index: int = 1,
) -> go.Figure:
    """
    SHAP explanation for one applicant as a horizontal Plotly bar chart.

    Parameters
    ----------
    user_input
        Same dict style as ``predict_risk`` (aliases allowed).
    explainer
        Pre-built ``TreeExplainer(model, data=scaled_background, ...)``.
    scaler, model
        Same artifacts as inference; model is used for P(default) in the subtitle.
    feature_names
        Defaults to ``FEATURE_COLUMNS``.
    top_n
        Number of features to show (by absolute SHAP value for the chosen class).
    class_index
        Index of the positive (default / high-risk) class in ``model.classes_`` / SHAP lists.
    """
    feats = list(feature_names) if feature_names is not None else list(FEATURE_COLUMNS)
    if len(feats) != len(FEATURE_COLUMNS):
        raise ValueError("feature_names length must match training feature count.")

    X_raw = raw_feature_matrix(user_input)
    X_scaled = scaler.transform(pd.DataFrame(X_raw, columns=FEATURE_COLUMNS))

    shap_out = explainer.shap_values(X_scaled)
    base_combined = explainer.expected_value
    phi, base = _parse_shap_binary(shap_out, base_combined, class_index=class_index, row_index=0)

    raw_row = X_raw.ravel()
    order = np.argsort(np.abs(phi))[::-1][:top_n]
    phi_top = phi[order]
    raw_top = raw_row[order]
    labels_top = [FEATURE_LABELS.get(feats[i], feats[i]) for i in order]
    direction = np.where(phi_top > 0, "Increases default risk", "Lowers default risk")
    colors = np.where(phi_top > 0, "#dc2626", "#2563eb")

    # Strongest impact at the top of the chart
    phi_plot = phi_top[::-1]
    labels_plot = labels_top[::-1]
    raw_plot = raw_top[::-1]
    dir_plot = direction[::-1]
    colors_plot = colors[::-1]
    custom = np.column_stack([raw_plot, dir_plot])

    if hasattr(model, "predict_proba"):
        classes = np.asarray(getattr(model, "classes_", [0, 1]))
        proba_row = model.predict_proba(X_scaled)[0]
        pos = (
            int(np.flatnonzero(classes == 1)[0])
            if np.any(classes == 1)
            else min(1, len(proba_row) - 1)
        )
        p_default = float(proba_row[pos])
    else:
        p_default = float("nan")

    fig = go.Figure(
        go.Bar(
            orientation="h",
            x=phi_plot,
            y=labels_plot,
            marker_color=list(colors_plot),
            customdata=custom,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Raw value: %{customdata[0]:,.4g}<br>"
                "SHAP: %{x:.4f}<br>"
                "%{customdata[1]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=dict(
            text=f"Top {len(phi_plot)} drivers — default class (class {class_index})",
            subtitle=dict(
                text=(
                    f"P(default) = {p_default:.1%} · "
                    f"Expected model output (class {class_index}) = {base:.3f} "
                    "(SHAP output scale matches the underlying forest)."
                )
            ),
        ),
        xaxis_title="SHAP value (contribution toward default class)",
        yaxis_title="",
        margin=dict(l=140, r=24, t=100, b=56),
        font=dict(family=_CHART_FONT, color=_INK),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor="#0f172a",
            bordercolor="rgba(255,255,255,0.12)",
            font=dict(color="#f8fafc", family=_CHART_FONT),
        ),
    )
    fig.update_xaxes(gridcolor=_GRID, zeroline=True, zerolinewidth=1, zerolinecolor=_GRID)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    return fig
