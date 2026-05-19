"""Logging setup shared by CLI scripts and Streamlit."""

from __future__ import annotations

import logging

from .config import get_config
from .paths import LOGS_DIR


def configure_logging() -> None:
    """Configure console and file logging once."""
    config = get_config()
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOGS_DIR / "fin_health.log", encoding="utf-8"),
        ],
        force=False,
    )

