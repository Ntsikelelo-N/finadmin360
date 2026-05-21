# Architecture Decisions
## FinAdmin360 — Finance Intelligence Platform

**Author:** Ntsikelelo Nicholas Jantjie
**Date:** May 2026

---

## Purpose of this document

This document records every significant technology choice made during the design
of the FinAdmin360 platform. For each decision it explains what was chosen, what
the alternatives were, why this option was selected, and what trade-offs were
accepted. This is standard practice in professional data engineering teams —
decisions are documented so that future maintainers understand why the system is
built the way it is, and so that the reasoning can be revisited if circumstances change.

---

## System overview

FinAdmin360 is an end-to-end data analytics platform built to serve the finance
function of a South African SME. It ingests supplier invoice data, bank transaction
data, and supplier master data daily, transforms them through a Medallion architecture
(Bronze → Silver → Gold), exposes KPIs through a Power BI dashboard, and runs a
machine learning model that predicts which invoices are at risk of late payment.

The high-level data flow is:

```
Raw source files (CSV)
        ↓
Azure Data Factory (scheduled ingestion)
        ↓
ADLS Gen2 — Bronze zone (raw, partitioned by date)
        ↓
dbt Core — Silver layer (cleaned, validated)
        ↓
dbt Core — Gold layer (business KPIs)
        ↓
Azure Synapse Analytics Serverless SQL (query engine)
        ↓
Power BI Desktop (dashboard) + scikit-learn ML model (scoring)
        ↓
Apache Airflow (orchestration) + GitHub Actions (CI/CD)
```

---

## Decision 1 — Cloud provider: Microsoft Azure over AWS or GCP

### What was chosen
Microsoft Azure, hosted in the `southafricanorth` (Johannesburg) region.

### Alternatives considered
- Amazon Web Services (AWS) — S3, Glue, Redshift, SageMaker
- Google Cloud Platform (GCP) — BigQuery, Dataflow, Vertex AI

### Why Azure was chosen

**Market alignment:** Azure is the dominant cloud platform in South African
enterprise environments. Most large SA corporates (banks, insurers, retailers)
run on Azure due to Microsoft's existing footprint through Office 365, Teams,
and Windows Server. Junior data engineering and data science roles in SA
predominantly require Azure experience over AWS or GCP.

**Certification alignment:** The Azure Data Scientist Associate (DP-100)
certificate is the most frequently listed cloud ML certification in South African
junior data science job advertisements. Building this project on Azure means every
service used — ADLS Gen2, Azure ML, Synapse Analytics, Key Vault — is directly
tested in that exam.

**Data residency:** The `southafricanorth` region (Johannesburg) means all data
stays within South Africa, which aligns with the POPIA (Protection of Personal
Information Act) requirement that personal data should not leave the country without
justification. Although this project uses synthetic data, building with data
residency in mind is a professional habit that matters in real workplaces.

**Free tier credit:** Azure provides $200 credit for 30 days, sufficient to
complete all provisioning steps and run the pipeline for the duration of this project.

### Trade-offs accepted
- Azure services are approximately 10–15% more expensive than equivalent AWS
  services in the same region
- AWS has a larger global ecosystem and more third-party tooling support
- GCP's BigQuery is arguably simpler for ad-hoc SQL analytics than Synapse

---

## Decision 2 — Storage architecture: ADLS Gen2 Medallion over a flat data warehouse

### What was chosen
Azure Data Lake Storage Gen2 with a three-zone Medallion architecture:
Bronze (raw), Silver (clean), Gold (business-ready).

### Alternatives considered
- A single flat Azure SQL Database storing all data in one schema
- Azure Synapse dedicated SQL pool as the primary storage layer
- Storing everything in Azure Blob Storage without a hierarchical structure

### Why the Medallion architecture was chosen

**Auditability:** The Bronze zone stores data exactly as received, with no
modifications. If a downstream model produces wrong results, you can always
trace back to the original raw file and re-derive from it. A flat database
that overwrites data on each load destroys this audit trail.

**Separation of concerns:** Each zone has a single responsibility:
- Bronze is a landing pad. Nothing is transformed here.
- Silver is where business rules are applied. Cleaning decisions are documented in dbt.
- Gold is where data is shaped for consumption. Finance users and Power BI query here only.

This means a bug in a Gold model can be fixed and rerun without touching the raw data.
A bug in a flat database often requires reconstructing the entire dataset from backups.

**WM04 alignment:** The Medallion architecture directly satisfies WM04 Part 2
(data collection and quality) by creating a traceable, auditable data lineage
from source to output — exactly what WA0103, WA0106, and WA0116 require.

**Industry standard:** The Medallion architecture is the de facto standard
for Azure data lake projects. It is taught in the DP-203 (Azure Data Engineer)
exam and referenced in Microsoft's own documentation. Demonstrating knowledge
of it signals professional competence to hiring teams.

### Trade-offs accepted
- More complex than a single database — requires understanding of three layers
- Requires dbt or equivalent tooling to manage transformations between layers
- Data is stored in Parquet files, not tables — querying requires Synapse or
  a similar engine rather than a simple SQL connection

---

## Decision 3 — Transformation tool: dbt Core over PySpark or pandas

### What was chosen
dbt Core (free, open source) with the `dbt-synapse` adapter.

### Alternatives considered
- PySpark via Azure Databricks or Synapse Spark pools
- pandas Python scripts running in Azure Functions or Airflow
- Azure Data Factory mapping data flows (GUI-based transformation)

### Why dbt Core was chosen

**SQL over Python for tabular transformations:** The transformations in this
project (cleaning columns, validating VAT amounts, aggregating by month) are
fundamentally SQL operations. Writing them in SQL with dbt is faster to write,
easier to read, and easier to test than equivalent PySpark code. The rule of
thumb in the industry is: if your data fits in a SQL table, use SQL. PySpark
is appropriate when data is too large for SQL or when you need complex Python
logic (ML, NLP) that SQL cannot express.

**Version control for data models:** dbt models are `.sql` files committed to
Git. Every change to a transformation is tracked, reviewed in a Pull Request,
and reversible. ADF mapping data flows are stored as JSON in Azure and are much
harder to version control and review.

**Built-in testing:** dbt has a native testing framework. `schema.yml` files
define tests (unique, not_null, accepted_values, relationships) that run
automatically on every pipeline execution. This directly produces the data
quality evidence required for WM04 Part 2.

**Automatic lineage documentation:** `dbt docs generate` produces an interactive
lineage graph showing how every table relates to every other table — Bronze sources
through Silver models to Gold outputs. This is the data lineage documentation
required for WM04 Part 2 with no extra work.

**Cost:** dbt Core is completely free and runs anywhere Python runs. Databricks
(the natural home for PySpark) would cost approximately R3,000–8,000 per month
for even the smallest cluster running 8 hours per day — far outside the budget
for a learning project.

**Market demand:** dbt is the most rapidly adopted data transformation tool
in the South African market. It appears in the majority of data engineering
job descriptions posted in 2024–2025 and is the primary transformation tool
at most SA banks, retailers, and consulting firms.

### Trade-offs accepted
- dbt with Synapse requires the ODBC Driver 18 for SQL Server — an additional
  installation step on Windows
- PySpark handles data at any scale; dbt+Synapse Serverless has practical
  limits for very large datasets (hundreds of GB)
- ADF mapping data flows have a visual interface that some users find easier
  to understand than SQL

---

## Decision 4 — Query engine: Synapse Analytics Serverless SQL over a dedicated pool

### What was chosen
Azure Synapse Analytics Serverless SQL Pool (pay-per-query, no cluster).

### Alternatives considered
- Azure Synapse Analytics dedicated SQL pool (always-on, provisioned compute)
- Azure Databricks SQL warehouse
- Azure SQL Database
- DuckDB running locally

### Why Synapse Serverless was chosen

**Cost:** This is the primary driver. A Synapse dedicated pool costs a minimum
of approximately R12,000–15,000 per month running continuously, even at the
smallest DW100c tier. Synapse Serverless charges approximately $5 per terabyte
of data scanned. At the volumes in this project (a few hundred MB), the monthly
cost is measured in cents, not thousands of rands.

**No cluster management:** A dedicated pool or Databricks cluster must be
started, stopped, and sized. Serverless SQL has no cluster — queries execute
on demand and infrastructure is managed entirely by Azure. For a daily pipeline
with no interactive users, there is no benefit to a persistent cluster.

**Native integration with ADLS Gen2:** Synapse Serverless can query Parquet
files directly in ADLS Gen2 using `OPENROWSET` and external tables, without
copying data into a separate database. The Gold layer Parquet files produced
by dbt are queryable immediately.

**DP-100 relevance:** Synapse Analytics is a core service in the Azure Data
Scientist Associate exam. Using it in this project provides hands-on experience
with a service that will be tested.

### Trade-offs accepted
- Serverless SQL has higher query latency than a dedicated pool (15–30 seconds
  vs 1–3 seconds for warm queries). For a daily batch pipeline and Power BI
  Import mode, this is acceptable.
- Serverless SQL does not support INSERT, UPDATE, or DELETE — data must be
  managed through ADLS Gen2 files, not direct table writes. This is the correct
  pattern for a data lake but requires understanding the separation between
  storage (ADLS) and compute (Synapse).
- Databricks SQL is more performant and has a richer ecosystem but costs
  significantly more and is harder to set up for a first project.

---

## Decision 5 — ML framework: scikit-learn over deep learning frameworks

### What was chosen
scikit-learn with a Gradient Boosting Classifier as the primary model.

### Alternatives considered
- TensorFlow or PyTorch neural networks
- XGBoost or LightGBM
- Azure AutoML

### Why scikit-learn was chosen

**Problem type:** The payment delay prediction task is a tabular binary
classification problem with fewer than 100,000 rows and 20–30 features.
This is exactly the problem type for which scikit-learn's tree-based models
are optimal. Deep learning offers no benefit at this scale — it requires
far more data and compute to outperform gradient boosting on structured
tabular data.

**Interpretability:** The finance administrator needs to trust and understand
model outputs. Gradient Boosting provides feature importances that explain
which inputs drive predictions. A neural network is a black box — the finance
administrator cannot explain to management why an invoice was flagged.
Interpretability is not a nice-to-have in a finance context; it is a compliance
and governance requirement.

**Simplicity and maintainability:** scikit-learn has a consistent, well-documented
API. The trained model is a single Python object that can be saved with `joblib`
and loaded anywhere. There are no GPU dependencies, no framework version conflicts,
and no deployment infrastructure beyond a Python environment.

**Speed of iteration:** Training the Gradient Boosting model on 2,000 rows takes
under 30 seconds on a standard laptop. This allows rapid experimentation without
cloud compute costs.

### Why not XGBoost or LightGBM
XGBoost and LightGBM are valid alternatives and often outperform scikit-learn's
GradientBoostingClassifier on larger datasets. For 2,000 rows the performance
difference is negligible. scikit-learn was preferred because it is a standard
library with no additional installation complexity and is the framework most
commonly taught in South African data science programmes.

### Why not Azure AutoML
Azure AutoML automatically trains and compares dozens of models and selects
the best one. It was not chosen for this project because the goal is to
demonstrate understanding of the ML process — feature engineering decisions,
model selection rationale, hyperparameter choices, evaluation methodology.
AutoML produces a result but hides the reasoning, which defeats the purpose
of a portfolio project and WM04 assessment evidence.

### Trade-offs accepted
- scikit-learn's GradientBoostingClassifier is slower to train than XGBoost
  or LightGBM at scale (>100k rows)
- Deep learning models would outperform at very large scale or with
  unstructured data (text, images) — not applicable here

---

## Decision 6 — Experiment tracking: MLflow over Weights & Biases or Neptune

### What was chosen
MLflow (open source, self-hosted locally during development, Azure ML-integrated
for production).

### Alternatives considered
- Weights & Biases (cloud-hosted, free tier available)
- Neptune.ai
- Azure ML experiment tracking only (no MLflow)
- No experiment tracking (logging to CSV manually)

### Why MLflow was chosen

**Azure ML native integration:** Azure Machine Learning has built-in MLflow
support. Models logged to MLflow are automatically visible in the Azure ML
studio and can be registered in the Azure ML Model Registry without any
additional tooling. This is the integration path documented in the DP-100
exam curriculum.

**Open source and self-hostable:** MLflow runs entirely locally with no
account, no API key, and no cost. During development, `mlflow ui` opens a
local tracking server at `localhost:5000`. This works with no internet
connection and no vendor dependency.

**Industry standard:** MLflow is the most widely adopted experiment tracking
tool in enterprise data science. It is vendor-neutral, supported by
Databricks (the company that created it), and integrated with every major
cloud ML platform.

**Reproducibility:** Every MLflow run logs the exact parameters, metrics,
code version (Git commit hash), and model artifact used to produce a result.
This means any run can be reproduced exactly months later — a requirement
for responsible ML practice and a strong signal of professional competence.

### Trade-offs accepted
- Weights & Biases has a richer UI and better collaboration features for teams
- MLflow's local UI is functional but not as polished as commercial alternatives
- Self-hosting MLflow in production requires additional infrastructure

---

## Decision 7 — Orchestration: Apache Airflow over Prefect or Azure Data Factory

### What was chosen
Apache Airflow 2.9 running locally in Docker Compose during development.

### Alternatives considered
- Prefect (modern Python-native orchestrator)
- Azure Data Factory pipelines (the same ADF used for ingestion)
- Azure Logic Apps
- Simple cron jobs or Azure Functions timer triggers

### Why Apache Airflow was chosen

**Market demand:** Apache Airflow is the most frequently required orchestration
tool in South African data engineering job advertisements. It appears in
approximately 70% of data pipeline job postings that specify an orchestrator.
Prefect is growing but is not yet as widely adopted in the SA market.

**DAG-based workflow definition:** Airflow defines pipelines as Python code
(DAGs — Directed Acyclic Graphs). This means pipeline logic is version-controlled,
testable, and reviewable in Pull Requests — the same workflow used for all
other code in this project. ADF pipeline definitions are JSON stored in Azure
and are harder to version-control and review.

**Visibility and monitoring:** The Airflow web UI provides a complete view of
every pipeline run — which tasks succeeded, which failed, how long each took,
and the full log output for any task. This operational visibility is essential
for a production pipeline.

**Retry and alerting logic:** Airflow has built-in retry configuration, failure
alerts, SLA monitoring, and email notifications — all configurable per task
in the DAG definition. Implementing equivalent behaviour with cron jobs or
Azure Functions requires significant custom code.

### Why not Prefect
Prefect has a simpler API and better developer experience than Airflow. It was
not chosen primarily because of its lower market penetration in South Africa.
For a portfolio project, demonstrating Airflow is more valuable signal to a
hiring team than demonstrating Prefect.

### Why not ADF for orchestration
ADF is already used for data ingestion (HTTP source to ADLS Gen2). Using it for
orchestration as well would create a single point of failure and mix concerns —
ingestion and orchestration would be coupled. Airflow orchestrates the full
pipeline including dbt and ML scoring, which are Python-based and do not fit
naturally into ADF's activity model.

### Trade-offs accepted
- Airflow has significant operational overhead — it requires a scheduler,
  webserver, and database running continuously
- Prefect and Dagster have better developer experience and faster iteration cycles
- Running Airflow in Docker Compose locally uses approximately 2GB of RAM

---

## Decision 8 — CI/CD: GitHub Actions over Jenkins or Azure DevOps

### What was chosen
GitHub Actions for both CI (continuous integration) and CD (continuous deployment).

### Alternatives considered
- Azure DevOps Pipelines
- Jenkins (self-hosted)
- CircleCI
- No CI/CD (manual deployment)

### Why GitHub Actions was chosen

**Zero additional infrastructure:** GitHub Actions runs on GitHub's servers
with no setup beyond a YAML file in the repository. Jenkins requires a
self-hosted server. Azure DevOps requires a separate account and project setup.
For a solo portfolio project, GitHub Actions is the obvious choice.

**Free for public repositories:** GitHub Actions provides 2,000 minutes per
month free for public repositories. This project's CI workflow runs in under
3 minutes, meaning approximately 660 free runs per month — far more than needed.

**Integration with the repository:** CI checks appear directly on Pull Requests.
Merging a PR with a failing CI check requires explicit override. This enforces
the discipline that all tests must pass before code is merged — the professional
standard for all software teams.

**Market relevance:** GitHub Actions is now the dominant CI/CD tool for open
source and startup environments. Azure DevOps is common in large enterprise
environments (banks, insurers). Knowledge of both is valuable — GitHub Actions
is the right starting point for a portfolio project because it is visible on
the public repository.

### Trade-offs accepted
- Azure DevOps has deeper integration with Azure services and is more common
  in large SA enterprise environments
- Jenkins is more flexible but requires significant setup and maintenance

---

## Decision 9 — Infrastructure as code: Terraform over Azure Bicep or ARM templates

### What was chosen
Terraform with the AzureRM provider.

### Alternatives considered
- Azure Bicep (Microsoft's native IaC language for Azure)
- ARM (Azure Resource Manager) JSON templates
- Azure CLI scripts (manual provisioning, no state management)
- Azure portal (GUI-based, no code)

### Why Terraform was chosen

**Multi-cloud transferability:** Terraform uses the same language (HCL) and
the same workflow (`init → plan → apply`) regardless of which cloud provider
you are provisioning. Skills learned building Azure infrastructure with Terraform
transfer directly to AWS or GCP projects. Bicep is Azure-only.

**State management:** Terraform maintains a state file that records the exact
current state of every provisioned resource. This means `terraform plan` can
show exactly what will change before any change is made — a critical safety
feature. ARM templates and CLI scripts have no equivalent.

**Market demand:** Terraform is listed as a required or preferred skill in the
majority of cloud-related data engineering job advertisements in South Africa.
Bicep knowledge is valued but is considered more niche.

**Readable plan output:** `terraform plan` produces a human-readable diff of
exactly what will be created, changed, or destroyed. This makes infrastructure
changes reviewable in Pull Requests — the same workflow used for code changes.

### Trade-offs accepted
- Bicep has tighter native integration with Azure services and is sometimes
  supported for new Azure features before the Terraform AzureRM provider
- Terraform state files must be managed carefully — a corrupted or lost state
  file requires manual reconciliation with `terraform import`
- Bicep has a simpler learning curve for Azure-only projects

---

## Decision 10 — Business intelligence: Power BI Desktop over Tableau or Looker

### What was chosen
Power BI Desktop (free).

### Alternatives considered
- Tableau Desktop (requires paid licence)
- Looker Studio (free, Google product)
- Metabase (open source, self-hosted)
- Custom Python dashboard (Plotly Dash or Streamlit)

### Why Power BI Desktop was chosen

**Market dominance in South Africa:** Power BI is the most widely used BI
tool in South African corporate environments. It benefits from Microsoft's
existing enterprise footprint — organisations that already use Office 365 and
Azure naturally adopt Power BI. Tableau is used in some larger corporates but
is less common at SME level.

**Native Azure integration:** Power BI Desktop connects directly to Azure
Synapse Analytics, Azure SQL, and ADLS Gen2 without additional connectors or
configuration. The Gold layer tables produced by dbt are immediately queryable.

**Cost:** Power BI Desktop is completely free to download and use locally.
Tableau Desktop requires a licence costing approximately R15,000–25,000 per
year. For a learning project with no budget, Power BI Desktop is the only
realistic choice among the major commercial BI tools.

**Familiar to finance users:** The finance administrator is likely already
familiar with Microsoft products. A Power BI dashboard that looks and feels
like an Excel workbook is more likely to be adopted than a Looker or Metabase
dashboard that requires learning a new interface.

### Trade-offs accepted
- Power BI Desktop cannot publish to the web or share live dashboards without
  a Power BI Pro licence (R170/user/month). The dashboard can only be opened
  locally by someone with the .pbix file and Power BI Desktop installed.
- Tableau has richer visualisation options and a more powerful calculation engine
- Looker Studio is free and web-based but has weaker Azure connectivity and
  fewer visualisation types
- A custom Streamlit or Dash dashboard would be more flexible and shareable
  but requires significantly more development time

---

## Summary table

| Layer | Tool chosen | Primary reason |
|---|---|---|
| Cloud | Azure (`southafricanorth`) | DP-100 alignment, SA market dominance, POPIA data residency |
| Storage | ADLS Gen2 + Medallion | Auditability, lineage, industry standard for Azure data lakes |
| Transformation | dbt Core | SQL-based, version-controlled, built-in testing and lineage docs |
| Query engine | Synapse Serverless SQL | Near-zero cost at learning volumes, no cluster management |
| ML framework | scikit-learn (GBM) | Right tool for tabular binary classification, interpretable |
| Experiment tracking | MLflow | Open source, Azure ML native, industry standard |
| Orchestration | Apache Airflow (Docker) | Most in-demand orchestrator in SA DE job market |
| CI/CD | GitHub Actions | Free for public repos, integrated with repository |
| IaC | Terraform | Multi-cloud, state management, PR-reviewable plans |
| BI | Power BI Desktop | SA market dominant, free, native Azure integration |
| Language | Python 3.11 | Universal for DE + DS, required by all tools above |

---

*This document was produced as part of the WM04 Capstone Project for the
Occupational Certificate: Data Science Practitioner (SAQA ID 118708, NQF Level 5).
It satisfies the architecture documentation requirement referenced in
WM04 Activity WA0111 (align business problem to technical solution).*
