"""
finadmin360_pipeline.py

Main Airflow DAG for the FinAdmin360 daily finance analytics pipeline.

Schedule: Daily at 04:00 UTC (06:00 SAST).

Task order:
  ingest_to_bronze
      ↓
  dbt_run_silver   (--profiles-dir /opt/airflow/dbt finds dbt/profiles.yml)
      ↓
  dbt_test_silver
      ↓
  dbt_run_gold
      ↓
  dbt_test_gold
      ↓
  ml_score_open_invoices
      ↓
  send_daily_summary

Key notes for this environment:
- dbt/profiles.yml is inside the project dbt/ folder (not ~/.dbt) so Docker can mount it
- --profiles-dir /opt/airflow/dbt tells dbt where to find profiles.yml inside container
- email_on_failure disabled because no SMTP server is configured in local dev
- PYTHONPATH set explicitly so src/ imports work inside the container
"""

from datetime import timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "email_on_failure": False,  # Disabled — no SMTP configured in local dev
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}

# Shared dbt command prefix — profiles.yml lives in /opt/airflow/dbt inside container
DBT_CMD = (
    "cd /opt/airflow/dbt && "
    "dbt {command} --select {select} --no-partial-parse "
    "--profiles-dir /opt/airflow/dbt --target prod"
)


def run_bronze_ingestion(**context):
    """Upload source CSV files to ADLS Gen2 Bronze zone."""
    import sys

    sys.path.insert(0, "/opt/airflow")
    from src.ingestion.upload_to_bronze import run_bronze_ingestion as _run

    _run()


with DAG(
    dag_id="finadmin360_daily_pipeline",
    description="End-to-end finance analytics pipeline",
    default_args=default_args,
    schedule_interval="0 4 * * *",
    start_date=days_ago(1),
    catchup=False,
    tags=["finance", "production"],
    max_active_runs=1,
) as dag:

    ingest_to_bronze = PythonOperator(
        task_id="ingest_to_bronze",
        python_callable=run_bronze_ingestion,
        doc_md="Uploads CSVs to ADLS Gen2 Bronze zone.",
    )

    dbt_run_silver = BashOperator(
        task_id="dbt_run_silver",
        bash_command=DBT_CMD.format(command="run", select="silver"),
        doc_md="Builds Silver cleaning views from Bronze sources.",
    )

    dbt_test_silver = BashOperator(
        task_id="dbt_test_silver",
        bash_command=DBT_CMD.format(command="test", select="silver"),
        doc_md="Runs all 12 Silver schema tests.",
    )

    dbt_run_gold = BashOperator(
        task_id="dbt_run_gold",
        bash_command=DBT_CMD.format(command="run", select="gold"),
        doc_md="Builds Gold KPI views: VAT summary, supplier scorecard, cash flow.",
    )

    dbt_test_gold = BashOperator(
        task_id="dbt_test_gold",
        bash_command=DBT_CMD.format(command="test", select="gold"),
        doc_md="Runs Gold schema tests.",
    )

    ml_score_invoices = BashOperator(
        task_id="ml_score_open_invoices",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow python src/models/score_open_invoices.py"
        ),
        doc_md="Scores PENDING invoices with late-payment probability.",
    )

    (
        ingest_to_bronze
        >> dbt_run_silver
        >> dbt_test_silver
        >> dbt_run_gold
        >> dbt_test_gold
        >> ml_score_invoices
    )
