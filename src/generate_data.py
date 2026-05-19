"""
Generate a synthetic loan applicant dataset with a learnable Default signal.

Default probability increases with worse credit (lower score) and higher DTI
via a logistic latent model plus noise.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.core.config import get_config
from src.core.logging_config import configure_logging

logger = logging.getLogger(__name__)


def main() -> Path:
    configure_logging()
    config = get_config()
    rng = np.random.default_rng(config.random_state)

    applicant_id = np.array([f"APP_{i + 1:04d}" for i in range(config.synthetic_rows)])
    age = rng.integers(22, 66, size=config.synthetic_rows)
    annual_income = rng.integers(28_000, 260_000, size=config.synthetic_rows)
    credit_score = rng.integers(300, 851, size=config.synthetic_rows)
    loan_amount = rng.integers(5_000, 125_000, size=config.synthetic_rows)
    debt_to_income_ratio = rng.uniform(0.05, 0.72, size=config.synthetic_rows).round(4)
    employment_years = rng.integers(0, 41, size=config.synthetic_rows)

    # Higher when credit is low; scaled roughly 0..1 across 300..850
    credit_risk = (850 - credit_score) / 550.0
    # Logistic latent: strong positive weights on credit_risk and DTI
    logit = (
        -2.15
        + 3.6 * credit_risk
        + 4.0 * debt_to_income_ratio
        + rng.normal(0.0, 0.5, size=config.synthetic_rows)
    )
    prob_default = 1.0 / (1.0 + np.exp(-logit))
    default = (rng.random(config.synthetic_rows) < prob_default).astype(np.int8)

    df = pd.DataFrame(
        {
            "Applicant_ID": applicant_id,
            "Age": age,
            "Annual_Income": annual_income,
            "Credit_Score": credit_score,
            "Loan_Amount": loan_amount,
            "Debt_to_Income_Ratio": debt_to_income_ratio,
            "Employment_Years": employment_years,
            "Default": default,
        }
    )

    config.loan_data_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.loan_data_path, index=False)
    logger.info("Wrote %d synthetic rows to %s", config.synthetic_rows, config.loan_data_path)
    return config.loan_data_path


if __name__ == "__main__":
    path = main()
    print(f"Wrote {get_config().synthetic_rows} rows to {path}")
