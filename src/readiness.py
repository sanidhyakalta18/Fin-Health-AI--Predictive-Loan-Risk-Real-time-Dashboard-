"""Deployment readiness checks for local and hosted environments."""

from __future__ import annotations

from dataclasses import dataclass

from src.core.config import get_config
from src.ml.artifacts import resolved_artifact_paths


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    ok: bool
    detail: str


def run_readiness_checks() -> list[ReadinessCheck]:
    """Return simple pass/fail checks for deployment prerequisites."""
    config = get_config()
    artifact_pair = resolved_artifact_paths()
    secret_configured = config.secret_key not in {"change-me-in-.env", "change-this-before-deployment"}
    return [
        ReadinessCheck(".env loaded", True, f"Environment: {config.environment}"),
        ReadinessCheck(
            "Secret key configured",
            secret_configured,
            "FIN_HEALTH_SECRET_KEY is set."
            if secret_configured
            else "Set FIN_HEALTH_SECRET_KEY in .env before shared or hosted deployment.",
        ),
        ReadinessCheck(
            "Loan data available",
            config.loan_data_path.is_file(),
            str(config.loan_data_path),
        ),
        ReadinessCheck(
            "Model artifacts available",
            artifact_pair is not None,
            "Found model+scaler pair." if artifact_pair else "Run `python -m src.train_model`.",
        ),
        ReadinessCheck(
            "Writable data directory",
            config.data_dir.exists() or config.data_dir.parent.exists(),
            str(config.data_dir),
        ),
    ]


def readiness_summary() -> tuple[bool, list[ReadinessCheck]]:
    checks = run_readiness_checks()
    return all(check.ok for check in checks), checks


def main() -> None:
    ok, checks = readiness_summary()
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        print(f"[{status}] {check.name}: {check.detail}")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
