"""
Data pipeline: load raw synthetic or production-like data, clean, and emit
processed datasets for modeling.
"""

from pathlib import Path

import pandas as pd

from src.core.config import get_config
from src.ml.preprocessing import validate_feature_columns


def load_raw(filename: str, **read_csv_kwargs) -> pd.DataFrame:
    """Load a CSV from ``data/raw/``."""
    path = get_config().raw_data_dir / filename
    return pd.read_csv(path, **read_csv_kwargs)


def save_processed(df: pd.DataFrame, filename: str) -> Path:
    """Write a processed table to ``data/processed/``."""
    processed_dir = get_config().data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    out = processed_dir / filename
    df.to_csv(out, index=False)
    return out


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder feature step: duplicate with your domain features
    (ratios, bureau flags, tenure bins, etc.).
    """
    validate_feature_columns(df, include_target=False)
    return df.copy()
