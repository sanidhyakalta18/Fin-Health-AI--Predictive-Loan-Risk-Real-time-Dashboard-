"""
SQLite-backed applicant analysis history.

This stores completed risk-analysis runs locally under ``data/applicant_history.db``.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from src.core.config import get_config

DB_PATH = get_config().history_db_path


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_history_db() -> None:
    """Create the applicant history table if needed."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applicant_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                created_at TEXT NOT NULL,
                age REAL NOT NULL,
                annual_income REAL NOT NULL,
                credit_score REAL NOT NULL,
                loan_amount REAL NOT NULL,
                debt_to_income REAL NOT NULL,
                employment_years REAL NOT NULL,
                prediction TEXT NOT NULL,
                probability_score REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_applicant_analyses_created_at
            ON applicant_analyses(created_at DESC)
            """
        )


def add_analysis(
    *,
    user_email: str | None,
    input_data: dict[str, Any],
    result: dict[str, Any],
) -> int:
    """Persist one completed applicant risk analysis and return its row id."""
    init_history_db()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO applicant_analyses (
                user_email,
                created_at,
                age,
                annual_income,
                credit_score,
                loan_amount,
                debt_to_income,
                employment_years,
                prediction,
                probability_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_email,
                _now_iso(),
                float(input_data["Age"]),
                float(input_data["Income"]),
                float(input_data["Credit Score"]),
                float(input_data["Loan"]),
                float(input_data["Debt"]),
                float(input_data["Employment Years"]),
                str(result["prediction"]),
                float(result["probability_score"]),
            ),
        )
        return int(cur.lastrowid)


def load_analyses(*, user_email: str | None = None, limit: int = 100) -> pd.DataFrame:
    """Return recent analyses as a DataFrame, newest first."""
    init_history_db()
    query = "SELECT * FROM applicant_analyses"
    params: list[Any] = []
    if user_email:
        query += " WHERE user_email = ?"
        params.append(user_email)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(int(limit))
    with _connect() as conn:
        return pd.read_sql_query(query, conn, params=params)


def delete_analysis(analysis_id: int, *, user_email: str | None = None) -> bool:
    """Delete one analysis row. Returns ``True`` if a row was removed."""
    init_history_db()
    query = "DELETE FROM applicant_analyses WHERE id = ?"
    params: list[Any] = [int(analysis_id)]
    if user_email:
        query += " AND user_email = ?"
        params.append(user_email)
    with _connect() as conn:
        cur = conn.execute(query, params)
        return cur.rowcount > 0


def clear_history(*, user_email: str | None = None) -> int:
    """Delete visible history rows and return the number removed."""
    init_history_db()
    query = "DELETE FROM applicant_analyses"
    params: list[Any] = []
    if user_email:
        query += " WHERE user_email = ?"
        params.append(user_email)
    with _connect() as conn:
        cur = conn.execute(query, params)
        return int(cur.rowcount)


def delete_history_database() -> bool:
    """Remove the SQLite history database file. It will be recreated on next use."""
    if not DB_PATH.exists():
        return False
    DB_PATH.unlink()
    return True


def history_summary(*, user_email: str | None = None) -> dict[str, Any]:
    """Small KPI summary for the history dashboard."""
    df = load_analyses(user_email=user_email, limit=10_000)
    if df.empty:
        return {
            "total": 0,
            "high_risk": 0,
            "avg_probability_pct": None,
            "latest_at": None,
        }
    high_risk = int((df["prediction"] == "High Risk").sum())
    return {
        "total": int(len(df)),
        "high_risk": high_risk,
        "avg_probability_pct": float(df["probability_score"].mean() * 100.0),
        "latest_at": str(df.iloc[0]["created_at"]),
    }
