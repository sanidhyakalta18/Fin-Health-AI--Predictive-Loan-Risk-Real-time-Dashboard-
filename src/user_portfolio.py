"""
Per-user applicant portfolios persisted as JSON under ``data/user_portfolios/``.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from src.core.config import get_config

from .inference import FEATURE_COLUMNS

logger = logging.getLogger(__name__)
PORTFOLIOS_DIR = get_config().portfolios_dir


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_filename(email: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", email.strip().lower())


def _portfolio_path(email: str) -> Path:
    return PORTFOLIOS_DIR / f"{_safe_filename(email)}.json"


def load_portfolio(email: str) -> dict[str, Any]:
    path = _portfolio_path(email)
    if not path.is_file():
        return {"owner": email, "applicants": [], "updated_at": _now_iso()}
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        logger.exception("Portfolio file is not valid JSON: %s", path)
        raise ValueError(f"Portfolio file at {path} is corrupted.") from exc
    data.setdefault("applicants", [])
    return data


def save_portfolio(email: str, data: dict[str, Any]) -> None:
    PORTFOLIOS_DIR.mkdir(parents=True, exist_ok=True)
    data["owner"] = email
    data["updated_at"] = _now_iso()
    with _portfolio_path(email).open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Saved portfolio for %s with %d applicant(s).", email, len(data.get("applicants", [])))


def applicants_to_dataframe(portfolio: dict[str, Any]) -> pd.DataFrame:
    """Build a model-ready DataFrame from saved applicants (empty if none)."""
    rows: list[dict[str, Any]] = []
    for app in portfolio.get("applicants", []):
        row = {col: app.get(col) for col in FEATURE_COLUMNS}
        if all(v is not None for v in row.values()):
            row["Applicant_Label"] = app.get("label", app.get("id", ""))
            rows.append(row)
    if not rows:
        return pd.DataFrame(columns=FEATURE_COLUMNS)
    return pd.DataFrame(rows)


def add_applicant(
    email: str,
    *,
    label: str,
    age: float,
    annual_income: float,
    credit_score: float,
    loan_amount: float,
    debt_to_income: float,
    employment_years: float,
    notes: str = "",
) -> dict[str, Any]:
    portfolio = load_portfolio(email)
    applicant = {
        "id": str(uuid.uuid4())[:8],
        "label": label.strip() or f"Applicant {len(portfolio['applicants']) + 1}",
        "Age": float(age),
        "Annual_Income": float(annual_income),
        "Credit_Score": float(credit_score),
        "Loan_Amount": float(loan_amount),
        "Debt_to_Income_Ratio": float(debt_to_income),
        "Employment_Years": float(employment_years),
        "notes": notes.strip(),
        "added_at": _now_iso(),
    }
    portfolio["applicants"].append(applicant)
    save_portfolio(email, portfolio)
    return applicant


def remove_applicant(email: str, applicant_id: str) -> bool:
    portfolio = load_portfolio(email)
    before = len(portfolio["applicants"])
    portfolio["applicants"] = [
        a for a in portfolio["applicants"] if a.get("id") != applicant_id
    ]
    if len(portfolio["applicants"]) == before:
        return False
    save_portfolio(email, portfolio)
    return True


def clear_portfolio(email: str) -> None:
    save_portfolio(email, {"owner": email, "applicants": []})
