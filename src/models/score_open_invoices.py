# -*- coding: utf-8 -*-
"""
score_open_invoices.py

Scores all PENDING invoices with the trained payment delay model.
Run daily by Airflow after dbt Gold models are built.
"""

import os
import sys
import pandas as pd
import mlflow
import mlflow.sklearn

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.features.build_features import engineer_features
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def get_data_dir():
    """
    Resolve the data directory correctly on both Windows (local) and
    Linux (inside the Airflow container).

    - Inside the container: AIRFLOW_HOME=/opt/airflow (Linux path) -> OK
    - On Windows locally:   AIRFLOW_HOME is not set, so fall back to the
                            project root derived from this file's location.
    """
    airflow_home = os.environ.get("AIRFLOW_HOME", "")

    # Only trust AIRFLOW_HOME if it looks like a Linux absolute path.
    # On Windows the env var may be unset or a Windows path which breaks
    # os.path.join when mixed with forward-slash segments.
    if airflow_home and airflow_home.startswith("/"):
        return os.path.join(airflow_home, "data", "synthetic")

    # Fallback: project root is three levels up from this file
    # finadmin360/src/models/score_open_invoices.py  ->  finadmin360/
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(project_root, "data", "synthetic")


def load_best_model():
    """Load the best GradientBoosting model from the MLflow tracking store."""
    client = mlflow.tracking.MlflowClient()

    experiment = client.get_experiment_by_name("payment-delay-prediction")
    if experiment is None:
        raise ValueError(
            "MLflow experiment 'payment-delay-prediction' not found. "
            "Run python src/models/train.py first."
        )

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="params.model_type = 'GradientBoosting'",
        order_by=["metrics.test_auc DESC"],
        max_results=1,
    )

    if not runs:
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["metrics.test_auc DESC"],
            max_results=1,
        )

    if not runs:
        raise ValueError("No MLflow runs found. Run train.py first.")

    best_run = runs[0]
    run_id = best_run.info.run_id
    auc = best_run.data.metrics.get("test_auc", 0)
    logger.info(f"Loading model from run {run_id} (test_auc={auc:.4f})")

    return mlflow.sklearn.load_model(f"runs:/{run_id}/model")


def score_open_invoices():
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "./mlruns")
    mlflow.set_tracking_uri(tracking_uri)
    logger.info(f"MLflow tracking URI: {tracking_uri}")

    data_dir = get_data_dir()
    logger.info(f"Data directory: {data_dir}")

    invoices = pd.read_csv(
        os.path.join(data_dir, "sa_invoices.csv"),
        parse_dates=["invoice_date"],
    )
    suppliers = pd.read_csv(os.path.join(data_dir, "sa_suppliers.csv"))
    df = invoices.merge(suppliers, on="supplier_id", how="left")

    pending = df[df["invoice_status"] == "Pending"].copy()
    logger.info(f"Found {len(pending)} PENDING invoices to score")

    if len(pending) == 0:
        logger.info("No pending invoices to score")
        return

    model = load_best_model()

    X = engineer_features(pending)

    # Align feature columns to exactly what the model was trained on.
    # Pending invoices may not include all supplier categories — get_dummies
    # only creates columns for categories present in the current batch.
    # reindex adds missing columns with 0 and drops unexpected extra columns.
    if hasattr(model, "feature_names_in_"):
        expected_cols = list(model.feature_names_in_)
        X = X.reindex(columns=expected_cols, fill_value=0)
        logger.info(f"Feature matrix aligned to {len(expected_cols)} columns")

    pending = pending.copy()
    pending["late_probability"] = model.predict_proba(X)[:, 1]
    pending["risk_tier"] = pending["late_probability"].apply(
        lambda p: "HIGH" if p >= 0.5 else ("MEDIUM" if p >= 0.3 else "LOW")
    )

    output_path = os.path.join(data_dir, "invoice_risk_scores.csv")
    pending[
        [
            "invoice_id",
            "supplier_id",
            "due_date",
            "amount_incl_vat",
            "late_probability",
            "risk_tier",
        ]
    ].to_csv(output_path, index=False)

    logger.info(f"Scores written to {output_path}")
    logger.info(f"HIGH risk:   {(pending['risk_tier'] == 'HIGH').sum()}")
    logger.info(f"MEDIUM risk: {(pending['risk_tier'] == 'MEDIUM').sum()}")
    logger.info(f"LOW risk:    {(pending['risk_tier'] == 'LOW').sum()}")


if __name__ == "__main__":
    score_open_invoices()
