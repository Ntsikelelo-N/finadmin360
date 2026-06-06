"""
train.py

Trains the payment delay prediction model and logs everything to MLflow.

This script is the production version of the training logic.
The notebook (notebooks/04_ml_payment_delay.ipynb) shows the exploratory version
with visualisations and detailed commentary.

Run:
    python src/models/train.py
"""

import os

import mlflow
import mlflow.sklearn
import pandas as pd
from dotenv import load_dotenv
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.features.build_features import engineer_features
from src.utils.logging_config import get_logger

load_dotenv()
logger = get_logger(__name__)


def load_data() -> pd.DataFrame:
    """Load and join invoice and supplier data from local synthetic files."""
    invoices = pd.read_csv(
        "data/synthetic/sa_invoices.csv",
        parse_dates=["invoice_date", "due_date"],
    )
    suppliers = pd.read_csv("data/synthetic/sa_suppliers.csv")
    df = invoices.merge(suppliers, on="supplier_id", how="left")
    logger.info(f"Loaded {len(df)} rows, {df.columns.tolist()}")
    return df


def train_and_evaluate() -> None:
    """Train multiple models, log to MLflow, and register the best one."""
    df = load_data()

    # Only train on invoices that have been paid — we know the outcome
    df_paid = df[df["is_paid"]].copy()
    logger.info(f"Training on {len(df_paid)} paid invoices")
    logger.info(f"Late payment rate: {df_paid['is_late'].mean():.1%}")

    X = engineer_features(df_paid)
    y = df_paid["is_late"].astype(int)

    # Stratified split preserves the late-payment ratio in both train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f"Train: {len(X_train)} | Test: {len(X_test)}")

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "./mlruns"))
    mlflow.set_experiment("payment-delay-prediction")

    # Models to compare — we train all three and pick the best by test AUC
    models_to_try = {
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=200,
            max_depth=6,
            random_state=42,
            n_jobs=-1,
        ),
        "LogisticRegression": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(random_state=42, max_iter=1000)),
            ]
        ),
    }

    results = {}
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for model_name, model in models_to_try.items():
        logger.info(f"Training {model_name}...")

        with mlflow.start_run(run_name=model_name):
            # Cross-validation gives a more reliable estimate than a single split
            cv_auc = cross_val_score(
                model, X_train, y_train, cv=cv, scoring="roc_auc", n_jobs=-1
            )

            model.fit(X_train, y_train)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            y_pred = model.predict(X_test)
            test_auc = roc_auc_score(y_test, y_pred_proba)

            # Log all metrics to MLflow — visible in mlflow ui
            mlflow.log_metric("cv_auc_mean", cv_auc.mean())
            mlflow.log_metric("cv_auc_std", cv_auc.std())
            mlflow.log_metric("test_auc", test_auc)
            mlflow.log_param("model_type", model_name)
            mlflow.log_param("n_features", X_train.shape[1])
            mlflow.log_param("n_train_rows", len(X_train))

            # Log the trained model artifact
            mlflow.sklearn.log_model(
                model,
                "model",
                registered_model_name=f"finadmin360-{model_name.lower()}",
            )

            results[model_name] = {
                "cv_auc": cv_auc.mean(),
                "test_auc": test_auc,
                "model": model,
            }

            report = classification_report(
                y_test, y_pred, target_names=["On-time", "Late"]
            )
            logger.info(
                f"\n{model_name} — CV AUC: {cv_auc.mean():.3f} ± "
                f"{cv_auc.std():.3f} | Test AUC: {test_auc:.3f}\n{report}"
            )

    best_name = max(results, key=lambda k: results[k]["test_auc"])
    logger.info(
        f"\nBest model: {best_name} "
        f"(Test AUC = {results[best_name]['test_auc']:.3f})"
    )


if __name__ == "__main__":
    train_and_evaluate()
