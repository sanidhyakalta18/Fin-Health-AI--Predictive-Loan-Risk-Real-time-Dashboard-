"""
Load persisted credit-risk artifacts and run single-row inference.

Uses the first **matching pair** found under ``models/``:

1. ``risk_model.pkl`` + ``scaler.pkl`` (written by ``src/train_model.py``)
2. ``credit_risk_random_forest.pkl`` + ``credit_risk_scaler.pkl`` (legacy names)

Both artifacts must come from the same training run (same scaler fit).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.core.config import get_config
from src.ml.artifacts import load_artifacts, resolved_artifact_paths
from src.ml.preprocessing import FEATURE_COLUMNS, raw_feature_matrix

ROOT = get_config().data_dir.parent

_load_artifacts = load_artifacts

__all__ = (
    "FEATURE_COLUMNS",
    "ROOT",
    "predict_risk",
    "raw_feature_matrix",
    "resolved_artifact_paths",
)


def predict_risk(input_data: dict[str, Any]) -> dict[str, Any]:
    """
    Scale one applicant row and return a human-readable risk label plus score.

    ``input_data`` may use training column names (e.g. ``Annual_Income``) or
    common aliases (``Income``, ``Credit Score``, ``Debt`` / ``DTI``, etc.).

    Returns
    -------
    dict with keys:
        ``prediction`` — ``\"Low Risk\"`` or ``\"High Risk\"`` (class 0 / 1).
        ``probability_score`` — model-estimated probability of class **1**
        (default / high risk), in ``[0, 1]`` when ``predict_proba`` exists.
    """
    model, scaler = _load_artifacts()
    X = raw_feature_matrix(input_data)
    X_scaled = scaler.transform(pd.DataFrame(X, columns=FEATURE_COLUMNS))

    pred_arr = model.predict(X_scaled)
    pred_class = int(np.asarray(pred_arr).ravel()[0])

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X_scaled)[0]
        classes = np.asarray(getattr(model, "classes_", np.arange(len(proba))))
        pos_idx = np.flatnonzero(classes == 1)
        if pos_idx.size:
            prob_high = float(proba[int(pos_idx[0])])
        elif len(proba) >= 2:
            prob_high = float(proba[1])
        else:
            prob_high = float(proba[0])
    else:
        prob_high = float(pred_class == 1)

    label = "High Risk" if pred_class == 1 else "Low Risk"
    return {"prediction": label, "probability_score": prob_high}
