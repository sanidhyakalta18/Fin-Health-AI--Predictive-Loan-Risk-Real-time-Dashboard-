"""Feature definitions and preprocessing helpers for credit-risk modeling."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "Age",
    "Annual_Income",
    "Credit_Score",
    "Loan_Amount",
    "Debt_to_Income_Ratio",
    "Employment_Years",
]
TARGET_COLUMN = "Default"

FEATURE_ALIASES: dict[str, str] = {
    "income": "Annual_Income",
    "loan": "Loan_Amount",
    "loan_amount": "Loan_Amount",
    "credit_score": "Credit_Score",
    "credit score": "Credit_Score",
    "debt": "Debt_to_Income_Ratio",
    "dti": "Debt_to_Income_Ratio",
    "debt_to_income": "Debt_to_Income_Ratio",
    "employment_years": "Employment_Years",
    "employment years": "Employment_Years",
}


def normalize_feature_key(key: str) -> str:
    return key.strip().lower().replace(" ", "_").replace("-", "_")


def alias_lookup() -> dict[str, str]:
    lookup = {normalize_feature_key(column): column for column in FEATURE_COLUMNS}
    for alias, canonical in FEATURE_ALIASES.items():
        lookup.setdefault(normalize_feature_key(alias), canonical)
    return lookup


def validate_feature_columns(df: pd.DataFrame, *, include_target: bool = False) -> None:
    required = list(FEATURE_COLUMNS)
    if include_target:
        required.append(TARGET_COLUMN)
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")


def clean_training_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return complete model features and integer target labels."""
    validate_feature_columns(df, include_target=True)
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].astype(int)
    mask = X.notna().all(axis=1) & y.notna()
    return X.loc[mask], y.loc[mask]


def raw_feature_matrix(input_data: dict[str, Any]) -> np.ndarray:
    """Convert UI/API input into one row ordered like the training features."""
    aliases = alias_lookup()
    canonical: dict[str, float] = {}
    for raw_key, value in input_data.items():
        column = aliases.get(normalize_feature_key(str(raw_key)))
        if column is None:
            continue
        try:
            canonical[column] = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Feature {raw_key!r} must be numeric; got {value!r}") from exc

    missing = [column for column in FEATURE_COLUMNS if column not in canonical]
    if missing:
        raise ValueError(
            "Missing required features after aliases: "
            f"{missing}. Expected columns {FEATURE_COLUMNS} or common labels such as "
            "Income, Credit Score, Debt, Loan Amount, Age, and Employment Years."
        )
    return np.asarray([[canonical[column] for column in FEATURE_COLUMNS]], dtype=np.float64)

