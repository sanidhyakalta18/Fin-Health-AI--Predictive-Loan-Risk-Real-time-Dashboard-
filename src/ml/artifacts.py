"""Model artifact discovery and loading."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from src.core.config import get_config


def resolved_artifact_paths() -> tuple[Path, Path] | None:
    """Return the first existing model+scaler path pair."""
    for model_path, scaler_path in get_config().artifact_pairs:
        if model_path.is_file() and scaler_path.is_file():
            return model_path, scaler_path
    return None


@lru_cache(maxsize=1)
def load_artifacts() -> tuple[Any, Any]:
    """Load the configured credit-risk model and scaler."""
    import joblib

    paths = resolved_artifact_paths()
    if paths:
        model_path, scaler_path = paths
        return joblib.load(model_path), joblib.load(scaler_path)

    config = get_config()
    tried = " | ".join(f"{model.name}+{scaler.name}" for model, scaler in config.artifact_pairs)
    raise FileNotFoundError(
        f"No complete model+scaler pair under {config.models_dir}. Tried: {tried}. "
        "Run `python -m src.generate_data`, then `python -m src.train_model` from the project root."
    )
