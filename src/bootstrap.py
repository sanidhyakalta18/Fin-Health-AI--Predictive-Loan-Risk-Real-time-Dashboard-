"""Deployment bootstrap helpers for demo data and model artifacts."""

from __future__ import annotations

import logging

from src.core.config import get_config
from src.ml.artifacts import resolved_artifact_paths

logger = logging.getLogger(__name__)


def ensure_demo_assets() -> list[str]:
    """
    Create synthetic data/model artifacts when a fresh deployment has none.

    Streamlit Cloud and Render start from a clean checkout. The repo intentionally
    does not commit generated CSVs or model binaries, so this keeps the demo
    beginner-friendly while preserving production-style artifact paths.
    """
    config = get_config()
    actions: list[str] = []

    if not config.loan_data_path.is_file():
        from src.generate_data import main as generate_data

        generated_path = generate_data()
        actions.append(f"Generated synthetic loan data at {generated_path}")
        logger.info(actions[-1])

    if resolved_artifact_paths() is None:
        from src.train_model import train_credit_risk_model

        metrics = train_credit_risk_model()
        actions.append(
            "Trained credit-risk model "
            f"(accuracy={metrics['accuracy']:.3f}, "
            f"precision={metrics['precision']:.3f}, "
            f"fpr={metrics['false_positive_rate']:.3f})"
        )
        logger.info(actions[-1])

    return actions

