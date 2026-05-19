"""
Train a RandomForest credit-risk classifier on loan_data.csv.

Loads raw data, scales numeric features, fits the model, prints resume metrics,
and persists the estimator and StandardScaler with joblib.
"""

import logging

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.core.config import get_config
from src.core.logging_config import configure_logging
from src.ml.preprocessing import FEATURE_COLUMNS, clean_training_frame
from src.model_engine import false_positive_rate

logger = logging.getLogger(__name__)


def train_credit_risk_model() -> dict[str, float]:
    """Train and persist the configured credit-risk model artifacts."""
    config = get_config()
    if not config.loan_data_path.is_file():
        raise FileNotFoundError(
            f"Expected dataset at {config.loan_data_path}. Run `python -m src.generate_data` first."
        )

    logger.info("Loading training data from %s", config.loan_data_path)
    df = pd.read_csv(config.loan_data_path)
    X, y = clean_training_frame(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.training_test_size,
        random_state=config.random_state,
        stratify=y,
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    clf = RandomForestClassifier(
        n_estimators=config.n_estimators,
        max_depth=None,
        random_state=config.random_state,
        class_weight="balanced",
        n_jobs=-1,
    )
    clf.fit(X_train_scaled, y_train)
    y_pred = clf.predict(X_test_scaled)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, pos_label=1, zero_division=0)
    fpr = false_positive_rate(y_test.values, y_pred)

    config.models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, config.primary_model_path)
    joblib.dump(scaler, config.primary_scaler_path)
    logger.info("Saved model to %s", config.primary_model_path)
    logger.info("Saved scaler to %s", config.primary_scaler_path)
    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "false_positive_rate": float(fpr),
    }


def main() -> None:
    configure_logging()
    metrics = train_credit_risk_model()

    print("Credit Risk Model — Test Set Metrics")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}  (positive class = Default=1)")
    print(
        "  FPR:       "
        f"{metrics['false_positive_rate']:.4f}  "
        "(FP / (FP + TN); actual non-defaulters flagged as default)"
    )

    config = get_config()
    print(f"\nSaved model to  {config.primary_model_path}")
    print(f"Saved scaler to {config.primary_scaler_path}")


if __name__ == "__main__":
    main()
