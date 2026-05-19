"""Environment-backed configuration for Fin-Health AI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(path: Path, *_args, **_kwargs) -> bool:
        if not path.is_file():
            return False
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        return True

from .paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT, RAW_DATA_DIR


def _setting(name: str, default: str | None = None) -> str | None:
    """Read env vars first, then Streamlit secrets when running on Community Cloud."""
    value = os.getenv(name)
    if value is not None:
        return value
    try:
        import streamlit as st

        secret_value = st.secrets.get(name)
    except Exception:
        return default
    return str(secret_value) if secret_value is not None else default


def _env_path(name: str, default: Path) -> Path:
    value = _setting(name)
    if not value:
        return default
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _env_int(name: str, default: int) -> int:
    value = _setting(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer; got {value!r}") from exc


def _env_float(name: str, default: float) -> float:
    value = _setting(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number; got {value!r}") from exc


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings loaded from `.env` with beginner-friendly defaults."""

    app_name: str
    model_display_name: str
    model_version: str
    environment: str
    secret_key: str
    log_level: str
    data_dir: Path
    raw_data_dir: Path
    models_dir: Path
    users_dir: Path
    portfolios_dir: Path
    history_db_path: Path
    loan_data_path: Path
    primary_model_path: Path
    primary_scaler_path: Path
    legacy_model_path: Path
    legacy_scaler_path: Path
    random_state: int
    training_test_size: float
    n_estimators: int
    high_risk_threshold: float
    portfolio_gauge_threshold_pct: float
    shap_background_samples: int
    synthetic_rows: int

    @property
    def artifact_pairs(self) -> tuple[tuple[Path, Path], ...]:
        return (
            (self.primary_model_path, self.primary_scaler_path),
            (self.legacy_model_path, self.legacy_scaler_path),
        )


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load `.env` once and return a typed settings object."""
    load_dotenv(PROJECT_ROOT / ".env")

    data_dir = _env_path("FIN_HEALTH_DATA_DIR", DATA_DIR)
    raw_data_dir = _env_path("FIN_HEALTH_RAW_DATA_DIR", data_dir / "raw")
    models_dir = _env_path("FIN_HEALTH_MODELS_DIR", MODELS_DIR)

    return AppConfig(
        app_name=_setting("FIN_HEALTH_APP_NAME", "Fin-Health AI") or "Fin-Health AI",
        model_display_name=_setting("FIN_HEALTH_MODEL_NAME", "Random Forest") or "Random Forest",
        model_version=_setting("FIN_HEALTH_MODEL_VERSION", "v1.0") or "v1.0",
        environment=_setting("FIN_HEALTH_ENV", "local") or "local",
        secret_key=_setting("FIN_HEALTH_SECRET_KEY", "change-me-in-.env") or "change-me-in-.env",
        log_level=_setting("FIN_HEALTH_LOG_LEVEL", "INFO") or "INFO",
        data_dir=data_dir,
        raw_data_dir=raw_data_dir,
        models_dir=models_dir,
        users_dir=_env_path("FIN_HEALTH_USERS_DIR", data_dir / "users"),
        portfolios_dir=_env_path("FIN_HEALTH_PORTFOLIOS_DIR", data_dir / "user_portfolios"),
        history_db_path=_env_path("FIN_HEALTH_HISTORY_DB_PATH", data_dir / "applicant_history.db"),
        loan_data_path=_env_path("FIN_HEALTH_LOAN_DATA_PATH", raw_data_dir / "loan_data.csv"),
        primary_model_path=_env_path("FIN_HEALTH_MODEL_PATH", models_dir / "risk_model.pkl"),
        primary_scaler_path=_env_path("FIN_HEALTH_SCALER_PATH", models_dir / "scaler.pkl"),
        legacy_model_path=_env_path("FIN_HEALTH_LEGACY_MODEL_PATH", models_dir / "credit_risk_random_forest.pkl"),
        legacy_scaler_path=_env_path("FIN_HEALTH_LEGACY_SCALER_PATH", models_dir / "credit_risk_scaler.pkl"),
        random_state=_env_int("FIN_HEALTH_RANDOM_STATE", 42),
        training_test_size=_env_float("FIN_HEALTH_TEST_SIZE", 0.2),
        n_estimators=_env_int("FIN_HEALTH_N_ESTIMATORS", 200),
        high_risk_threshold=_env_float("FIN_HEALTH_HIGH_RISK_THRESHOLD", 0.55),
        portfolio_gauge_threshold_pct=_env_float("FIN_HEALTH_PORTFOLIO_GAUGE_THRESHOLD_PCT", 40.0),
        shap_background_samples=_env_int("FIN_HEALTH_SHAP_BACKGROUND_SAMPLES", 400),
        synthetic_rows=_env_int("FIN_HEALTH_SYNTHETIC_ROWS", 1000),
    )
