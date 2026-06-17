# FinAdmin360 — Finance Intelligence Platform

> Transforming a South African finance administrator's manual spreadsheet workflow
> into an automated, insight-driven data platform — built end to end on Azure.

[![CI](https://github.com/Ntsikelelo-N/finadmin360/actions/workflows/ci.yml/badge.svg)](https://github.com/Ntsikelelo-N/finadmin360/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![dbt](https://img.shields.io/badge/dbt-1.8-orange.svg)](https://www.getdbt.com)
[![Azure](https://img.shields.io/badge/cloud-Azure-0078D4.svg)](https://azure.microsoft.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 1. The problem

A South African finance administrator was managing supplier invoices, bank
reconciliations, VAT submissions, and CIPC returns entirely through Excel
spreadsheets. This created four concrete risks: 15+ hours per month lost to manual
copy-paste workflows, no early warning system for late-paying suppliers, manual
SARS VAT201 preparation with no automated validation on R25M+ of annual input tax,
and zero real-time visibility for the CFO into cash flow, overdue balances, or
supplier performance.

FinAdmin360 replaces that workflow with an automated pipeline that ingests raw
invoice and bank data, validates and transforms it through a Medallion
architecture, scores open invoices for late-payment risk with a machine learning
model, and serves the result through a daily-refreshed Power BI dashboard.

## 2. Results

| Outcome | Result |
|---|---|
| Total spend tracked (24 months) | R193,146,040 across 2,000 invoices |
| VAT input tax validated | R25,192,962 — 0 mismatches detected |
| Late payment rate identified | 19.9% (398 of 2,000 invoices) |
| Late payment value exposure | R46,503,680 |
| Currently overdue | 271 invoices, R73.6M outstanding |
| dbt schema and data quality tests | PASS=12, ERROR=0 |
| ML model (GradientBoosting) | Test AUC 0.610, selected over RandomForest (AUC 0.647) for usable recall on the Late class |
| Airflow pipeline | 6 tasks, daily run at 06:00 SAST, completes in under 12 minutes |
| Models compared in MLflow | 3 (GradientBoosting, RandomForest, LogisticRegression) |

## 3. Architecture
![Architecture diagram](finadmin360_architecture.png)

Bronze ingestion lands raw CSV files in ADLS Gen2 via Azure Data Factory. Synapse
Serverless SQL exposes the Bronze files as external tables. dbt Core transforms
Bronze into validated Silver views and business-ready Gold KPI views (VAT summary,
supplier scorecard, monthly cash flow). A GradientBoosting classifier scores open
invoices for late-payment probability, tracked in MLflow. Apache Airflow
orchestrates the full pipeline daily inside Docker. Power BI serves the final
dashboard to stakeholders, with a local CSV export path available when the Azure
subscription is inactive.

## 4. Screenshots

### Power BI dashboard
![Power BI dashboard](image.png)

### dbt lineage graph
![dbt lineage](image-3.png)

### MLflow experiment comparison
![MLflow runs](image-2.png)

### Airflow DAG — all tasks green
![Airflow DAG](image-1.png)

## 5. Tech stack

| Layer | Tools |
|---|---|
| Cloud infrastructure | Azure (ADLS Gen2, Synapse Analytics Serverless SQL, Azure ML, Key Vault, ADF), provisioned via Terraform |
| Data transformation | dbt Core 1.8 with the dbt-synapse adapter. All models use `+materialized: view` because Synapse Serverless cannot create physical tables |
| Orchestration | Apache Airflow 2.9, running in Docker via docker-compose |
| Machine learning | scikit-learn (GradientBoostingClassifier), MLflow for experiment tracking and model comparison |
| BI / reporting | Power BI Desktop, connected to Synapse Gold views or local CSV exports |
| CI/CD | GitHub Actions — lint and test on every pull request, deploy to Azure on merge to main |
| Languages | Python 3.11, SQL, Windows Git Bash |
| Version control | GitHub — [github.com/Ntsikelelo-N/finadmin360](https://github.com/Ntsikelelo-N/finadmin360) |

**Authentication note:** dbt connects to Synapse using
`ActiveDirectoryServicePrincipal`. Personal Microsoft accounts (including Gmail
federated accounts) cannot use interactive or SQL password authentication against
Synapse Serverless — a registered service principal is required.

## 6. Quick start

**Prerequisites:** Python 3.11, Docker Desktop, an Azure account (optional — see
note below)

```bash
git clone https://github.com/Ntsikelelo-N/finadmin360.git
cd finadmin360
python -m venv .venv
cp .env.example .env
source activate.sh
python src/ingestion/generate_synthetic_data.py
python src/ingestion/upload_to_bronze.py
docker-compose up -d
```

**Important:** Before running dbt, create the Bronze external tables in Synapse
Studio. See [docs/setup_guide.md](docs/setup_guide.md) for the full SQL setup
script (master key, credential, data source, file format, and three external
tables, each run as a separate statement).

**No active Azure subscription?** Run the Gold layer locally instead and connect
Power BI to the resulting CSV files:

```bash
python src/utils/export_gold_to_csv.py
```

## 7. Project structure

```
finadmin360/
├── dags/                     Airflow DAG definitions
├── dbt/                      dbt project — Silver and Gold models, schema tests
│   ├── models/silver/        Cleaned, validated views over Bronze sources
│   ├── models/gold/          Business KPI views (VAT, scorecard, cash flow)
│   └── tests/                Custom singular tests
├── docs/                     Architecture decisions, data dictionary, model card,
│                             WM04 evidence map, screenshots
├── notebooks/                EDA, operational research, benchmarking (Jupyter)
├── reports/                  Final capstone report
├── presentations/            Management presentation slides
├── src/
│   ├── ingestion/            Synthetic data generation, Bronze upload
│   ├── features/             Feature engineering for the ML model
│   ├── models/                Training and scoring scripts
│   └── utils/                 Shared logging, Azure client, Gold CSV export
├── terraform/                 Azure infrastructure as code
├── tests/                      Unit tests (pytest)
├── dashboards/                  Power BI .pbix file
└── activate.sh                  One-command environment setup for Git Bash
```

## 9. Author and licence

Built by **Ntsikelelo Nicholas Jantjie** , June 2026.

Contributions and feedback are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
Licensed under the [MIT License](LICENSE).

Connect on [LinkedIn](https://www.linkedin.com/in/ntsikelelo-jantjie/) or open an issue on this repository
to get in touch.
