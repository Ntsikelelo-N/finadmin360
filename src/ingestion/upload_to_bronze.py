"""
upload_to_bronze.py

Uploads raw CSV files to the Bronze zone in ADLS Gen2.

The Bronze zone stores data EXACTLY as received — no cleaning, no transformation.
This is the single source of truth. If downstream processing fails, you always
have the original data to re-derive from.

Files are partitioned by ingestion date:
  bronze/sa_invoices/ingested_date=2025-05-01/sa_invoices.csv

This means if the same file is re-ingested tomorrow, it goes into a new partition.
The full ingestion history is preserved as an audit trail.
"""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from src.utils.azure_client import get_adls_client
from src.utils.logging_config import get_logger

load_dotenv()
logger = get_logger(__name__)


def upload_file_to_bronze(local_path: str, dataset_name: str) -> None:
    """
    Upload a single local CSV file to the ADLS Gen2 Bronze zone.

    Args:
        local_path: Path to the local file (e.g. data/synthetic/sa_invoices.csv)
        dataset_name: Folder name in Bronze (e.g. sa_invoices)
    """
    if not os.path.exists(local_path):
        logger.warning(f"File not found, skipping: {local_path}")
        return

    client = get_adls_client()
    container = client.get_file_system_client("bronze")

    today = datetime.now().strftime("%Y-%m-%d")
    filename = Path(local_path).name
    remote_path = f"{dataset_name}/ingested_date={today}/{filename}"

    file_client = container.get_file_client(remote_path)

    with open(local_path, "rb") as f:
        data = f.read()

    file_client.upload_data(data, overwrite=True)
    logger.info(f"Uploaded {local_path} ({len(data):,} bytes) → bronze/{remote_path}")


def run_bronze_ingestion() -> None:
    """Upload all source files to Bronze."""
    files = [
        ("data/synthetic/sa_invoices.csv", "sa_invoices"),
        ("data/synthetic/sa_suppliers.csv", "sa_suppliers"),
        ("data/synthetic/sa_bank_transactions.csv", "sa_bank_transactions"),
        ("data/raw/kaggle_invoices.csv", "kaggle_invoices"),
        ("data/raw/kaggle_transactions.csv", "kaggle_transactions"),
        ("data/raw/sarb_data.csv", "sarb_benchmarks"),
    ]

    logger.info(f"Starting Bronze ingestion — {len(files)} files")
    for local_path, dataset_name in files:
        upload_file_to_bronze(local_path, dataset_name)
    logger.info("Bronze ingestion complete")


if __name__ == "__main__":
    run_bronze_ingestion()
