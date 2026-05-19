"""
Model engine: train scikit-learn estimators, evaluate business-oriented metrics,
persist ``.pkl`` artifacts under ``models/``, and run inference.
"""

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix

from src.core.config import get_config

MODELS_DIR = get_config().models_dir


def false_positive_rate(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    FPR for binary labels where positive class = 1 (e.g., default / bad).
    FPR = FP / (FP + TN) — among actual negatives, how many were called positive.
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    denom = fp + tn
    return float(fp / denom) if denom else 0.0


def risk_tier_accuracy(y_true: np.ndarray, y_pred_tier: np.ndarray) -> float:
    """
    Accuracy of predicted risk tier vs. true tier (same length, categorical).
    Replace with your tier definitions and calibration checks as needed.
    """
    return float(np.mean(y_true == y_pred_tier))


def save_model(model: Any, filename: str = "credit_risk_model.pkl") -> Path:
    models_dir = get_config().models_dir
    models_dir.mkdir(parents=True, exist_ok=True)
    path = models_dir / filename
    joblib.dump(model, path)
    return path


def load_model(filename: str = "credit_risk_model.pkl") -> Any:
    return joblib.load(get_config().models_dir / filename)


def predict_proba(model: Any, X: pd.DataFrame) -> np.ndarray:
    """Return positive-class probability if available, else decision function."""
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    scores = model.decision_function(X)
    # Min-max to [0, 1] for a simple display score (replace with Platt if needed)
    s_min, s_max = scores.min(), scores.max()
    if s_max > s_min:
        return (scores - s_min) / (s_max - s_min)
    return np.full(len(scores), 0.5)
