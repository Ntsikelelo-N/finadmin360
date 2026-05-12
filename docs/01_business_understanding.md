# Business Understanding and Requirements
## FinAdmin360 — Finance Intelligence Platform

**Author:** Ntsikelelo Nicholas Jantjie


---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Organisational Context](#2-organisational-context)
3. [Business Problem Statement](#3-business-problem-statement)
4. [Root Cause Analysis](#4-root-cause-analysis)
5. [Stakeholder Identification](#5-stakeholder-identification)
6. [Business Objectives](#6-business-objectives)
7. [Data Science Objectives](#7-data-science-objectives)
8. [Constraints](#8-constraints)
9. [Success Criteria](#9-success-criteria)
10. [Risks and Assumptions](#10-risks-and-assumptions)
11. [Alignment Between Business Problem and Data Usage](#11-alignment-between-business-problem-and-data-usage)
12. [Project Scope](#12-project-scope)
13. [Ethical Considerations](#13-ethical-considerations)
---

## 1. Executive Summary

A South African small-to-medium enterprise (SME) finance administrator currently manages
five core financial functions — supplier invoice processing, cashbook maintenance,
bank reconciliations, annual audit file preparation, and monthly VAT submissions — almost
entirely through manual effort in Microsoft Excel. This approach exposes the business to
three significant risks: delayed detection of overdue supplier payments, errors in VAT
calculations, and an inability to forecast cash-flow positions ahead of critical
decision points.

This project designs and builds an end-to-end data analytics platform — **FinAdmin360** —
that automates data collection and cleaning, surfaces actionable KPIs through a live Power BI
dashboard, and deploys a machine learning model that predicts which supplier invoices are at
risk of late payment before they fall due. The platform is built on Microsoft Azure using
tools that are standard in the South African data engineering and data science market:
dbt Core, Apache Airflow, scikit-learn, and MLflow.

The expected outcomes are a reduction of approximately 35 hours per month in manual
processing time, an increase in VAT calculation accuracy to over 99%, and early detection
of 70% or more of late-payment risk invoices before their due date — enabling the finance
administrator to act proactively rather than reactively.

---

## 2. Organisational Context

### 2.1 Organisation profile

The organisation is a South African SME operating in the services sector. It maintains
relationships with approximately 50 active suppliers across ten categories, including
IT Equipment, Legal Services, Accounting Services, Office Supplies, and Cleaning Services.
Monthly supplier spend ranges from ZAR 150,000 to ZAR 800,000 depending on project
activity and seasonal demand.

The finance function consists of a single Finance Administrator who reports to the
Financial Director. There is no dedicated data team or business intelligence function.
All financial reporting is produced manually on a monthly basis.

### 2.2 Current workflow overview

The Finance Administrator performs the following tasks on a regular cycle:

**Daily:**
- Capturing new supplier invoices received by email or post into an Excel spreadsheet
- Logging any payments made to suppliers in the cashbook

**Weekly:**
- Reconciling the cashbook against the bank statement exported from the online banking portal
- Following up on invoices that appear overdue based on manual review of the spreadsheet

**Monthly:**
- Computing the VAT201 return by summing invoice VAT amounts in Excel and cross-checking
  against the bank statement for the SARS submission deadline
- Preparing a payment run by reviewing all outstanding invoices and deciding which to pay
- Submitting the company's CIPC annual return using manually gathered financial figures

**Annually:**
- Compiling the audit file by gathering all invoices, reconciliation sheets, and bank
  statements into a folder for the external auditor

### 2.3 The problem with the current workflow

The entire workflow is driven by a single Excel workbook that has grown organically over
several years. It contains no data validation, no automated reconciliation logic, and no
forecasting capability. The Finance Administrator estimates spending between 35 and 45 hours
per month on tasks that are repetitive and mechanical — time that could be redirected toward
higher-value financial analysis and management reporting.

The business consequence is that management currently makes payment scheduling, budget
allocation, and supplier credit decisions based on information that is always at least
several days out of date, and occasionally contains errors that are only discovered during
the annual audit.

---

## 3. Business Problem Statement

> **The finance team lacks a real-time, reliable view of its supplier payment position,
> VAT liability, and cash-flow trajectory. As a result, the business cannot proactively
> manage overdue invoices, consistently meet SARS submission deadlines without manual
> effort, or make informed month-to-month budget decisions. The estimated cost of this
> information gap is 35–45 hours of manual labour per month and an elevated risk of
> SARS penalties due to VAT calculation errors.**

To make this concrete, the three most pressing questions that the business currently cannot
answer without hours of manual effort are:

1. **Which supplier invoices are most likely to be paid late, and by how many days?**
   The Finance Administrator must manually scan hundreds of rows in Excel to identify
   overdue accounts, with no prioritisation by risk or amount.

2. **What is the business's VAT input tax liability for the current month?**
   The VAT201 calculation is performed manually from the invoice spreadsheet every month,
   with a risk of formula errors and omissions.

3. **Is the business's cash position improving or deteriorating month on month?**
   There is no cash-flow trend view — the Finance Director must request a manual summary
   from the Finance Administrator each time this question is asked.

---

## 4. Root Cause Analysis

Understanding why this problem exists helps clarify what the data solution must address.

### 4.1 Data is fragmented

Invoice data, bank transaction data, and supplier master data each live in separate files
or systems: email inboxes, the banking portal, an Excel cashbook, and a paper filing
cabinet. There is no single integrated data source. Every analysis requires manual
copy-and-paste across these silos.

### 4.2 There is no data pipeline

Data moves from source to report through a human — the Finance Administrator — who types,
copies, and recalculates by hand. This introduces latency (data is only current when the
person does the work) and errors (manual entry is error-prone).

### 4.3 No predictive capability exists

The current system is entirely backward-looking. The Finance Administrator can see which
invoices were paid late last month but has no way to predict which invoices will be paid
late next month. This means action is always reactive — chasing payment after it is
already overdue — rather than proactive.

### 4.4 Reporting is manual and time-consuming

Every management report — monthly cash-flow summary, supplier spend analysis, VAT summary —
is produced from scratch each month by the Finance Administrator. There is no self-service
dashboard, and no report is reproducible without the person who created it.

---

## 5. Stakeholder Identification

The table below identifies every person or group with an interest in the outcome of this
project, what data they need, and what decision they make with that data.

| Stakeholder | Role | Relationship to project | Data needed | Decision made with data |
|---|---|---|---|---|
| Finance Administrator | Primary user and data owner | Uses the platform daily | Invoice status, reconciliation output, VAT summary, high-risk payment alerts | Which invoices to chase today; which payments to include in the next payment run |
| Financial Director | Internal management sponsor | Reviews output monthly; approves scope | Monthly cash-flow position, overdue exposure, KPI trends, budget vs actual spend | Budget allocation, supplier credit term renegotiation, capital planning |
| Chief Executive Officer | Senior management | Receives executive summary only | One-page summary of financial health, key risks, cash-flow trend | Business strategy, resource allocation |
| External Auditor | Annual audit | Uses audit file output | Complete, reconciled transaction history; VAT reconciliation; invoice-to-payment matching | Sign off on the annual financial statements |
| SARS | Regulatory body | Receives VAT returns | Monthly input tax breakdown by invoice; total claimable input VAT | Accept or query the VAT201 return; determine penalties |
| CIPC | Company registration regulator | Receives annual return | Annual financial figures for submission | Record company compliance; flag non-compliant entities |
| Data Science Practitioner (you) | Project builder | Builds and maintains the platform | All of the above, plus raw data for model training | Which tools to use, what to model, what to prioritise |

### 5.1 Stakeholder influence and interest matrix

This matrix helps prioritise how much attention to give each stakeholder during the project.

```
High interest, high influence:  Finance Administrator, Financial Director
High interest, low influence:   External Auditor, SARS
Low interest, high influence:   CEO
Low interest, low influence:    CIPC (receives output, does not interact with platform)
```

**Implication for project design:** The Finance Administrator is the primary user.
Every output — dashboard pages, alert emails, generated reports — must be designed for
someone who is highly skilled in finance but is not a data scientist. Plain language,
familiar formats (matching eFiling and Excel layouts where possible), and actionable
recommendations take priority over technical sophistication.

---

## 6. Business Objectives

The following objectives are stated in measurable business terms. They describe outcomes
for the organisation, not technical deliverables.

### BO1 — Reduce manual processing time

Reduce the time the Finance Administrator spends on repetitive data work from
35–45 hours per month to under 10 hours per month within three months of the
platform going live.

**Why this matters:** Time freed from manual work can be redirected toward
value-adding tasks such as supplier negotiation, budget analysis, and financial planning.

### BO2 — Improve invoice payment visibility

Provide a daily-updated view of all outstanding supplier invoices, ranked by payment risk,
so that the Finance Administrator can prioritise follow-up actions without manually
reviewing the spreadsheet.

**Why this matters:** Late payments damage supplier relationships, may trigger
penalty clauses, and create VAT compliance complications when paid invoices do not
match the VAT return period.

### BO3 — Automate VAT input tax calculation

Produce a monthly VAT input tax summary that the Finance Administrator can use to
complete the SARS VAT201 return directly, without any manual recalculation.

**Why this matters:** Manual VAT calculations are the single highest-risk activity in
the finance function. A calculation error on the VAT201 can result in SARS penalties
and interest, which are reputationally and financially damaging.

### BO4 — Enable proactive cash-flow management

Provide a month-on-month cash-flow trend view that is available to the Financial Director
on demand, without requiring the Finance Administrator to prepare a manual report.

**Why this matters:** Without current cash-flow data, management makes capital and
spending decisions based on lagging information, increasing the risk of cash-flow
shortfalls.

### BO5 — Generate audit-ready output automatically

Produce a structured, reconciled transaction log that can be handed to the external
auditor at year-end with minimal additional preparation by the Finance Administrator.

**Why this matters:** Annual audit preparation currently takes approximately two weeks
of intensive manual work. Automating this output eliminates that cost and reduces
audit risk.

---

## 7. Data Science Objectives

The following objectives translate the business objectives above into specific, measurable
data science tasks.

### DS01 — Build a payment delay prediction model (maps to BO2)

Train a binary classification model that predicts, at the time of invoice receipt,
whether a given invoice will be paid more than 30 days past its due date.

**Target variable:** `is_late` — binary (1 = paid more than 30 days late, 0 = paid on time)

**Minimum performance threshold:** Area Under the ROC Curve (AUC) ≥ 0.80 on a
held-out test set. Below this threshold, the model is not reliable enough to drive
business decisions.

**Why AUC:** AUC measures the model's ability to rank late-payment invoices above
on-time invoices, regardless of the exact probability threshold chosen. This is the
right metric when the cost of a false negative (missing a late invoice) is high.

### DS02 — Build a VAT input tax aggregation pipeline (maps to BO3)

Produce a dbt Gold model (`gold_vat_summary`) that aggregates validated invoice VAT
amounts by calendar month, separated into total input tax and claimable input tax
(invoices actually paid within the period — the cash accounting basis that SARS requires).

**Accuracy target:** The automated VAT summary must match a manually computed figure
within ZAR 0.02 per invoice (rounding tolerance).

### DS03 — Build a cash-flow trend model (maps to BO4)

Produce a dbt Gold model (`gold_cash_flow_monthly`) that computes monthly net cash flow,
running balance, and month-on-month growth rate from bank transaction data.

**Output quality standard:** Running balance must reconcile to the Finance
Administrator's manually maintained cashbook within ZAR 1.00 per month-end period.

### DS04 — Build a supplier performance scorecard (maps to BO2, BO5)

Produce a dbt Gold model (`gold_supplier_scorecard`) that ranks all active suppliers
by payment risk tier (HIGH / MEDIUM / LOW) based on their historical late payment rate,
average days past due, and outstanding invoice value.

### DS05 — Automate data ingestion and transformation (maps to BO1, BO5)

Build a fully automated pipeline (Azure Data Factory + dbt + Apache Airflow) that
ingests raw data daily, applies cleaning and validation rules, and populates the
Gold-layer tables without manual intervention.

---

## 8. Constraints

Constraints are facts about the environment that the project must work within and cannot
change. They are different from risks, which are uncertainties.

### 8.1 Technical constraints

**Cloud region:** All data must be stored and processed within Azure's
`southafricanorth` (Johannesburg) region to comply with the organisation's data
residency policy. This rules out using cheaper regions such as `eastus`.

**Tooling:** The organisation does not have a Power BI Pro licence. The solution must
be deliverable using Power BI Desktop (free), which means the dashboard cannot be
published to the Power BI Service for online access. Dashboard access requires opening
the .pbix file locally.

**No real supplier PII:** This project uses synthetic data generated to match the
structure of real financial data. No real supplier names, VAT numbers, banking details,
or personal information may be used in the training dataset.

**Azure free tier and pay-as-you-go:** The project must remain within the Azure
$200 free credit for the initial build period and cost no more than ZAR 200 per month
during ongoing operation. This constrains the compute options for Azure ML and Synapse.

### 8.2 Data constraints

**Historical depth:** The synthetic dataset covers 24 months of invoice history.
The ML model's predictive accuracy is limited by this depth — supplier behavioural
patterns that take longer than 24 months to emerge will not be captured.

**Minimum invoices per supplier:** The payment delay model requires at least five
prior invoices from a supplier to produce a reliable late-payment probability estimate.
New suppliers with fewer than five invoices will be flagged as "insufficient history"
rather than scored.

**Bank statement format:** The project assumes bank statements are exported as CSV
files from the online banking portal. If the bank changes its export format, the
ingestion script requires updating.

### 8.3 Regulatory constraints

**VAT accounting basis:** The VAT201 computation uses the cash accounting basis —
input tax is claimable only on invoices that have been paid within the VAT period.
The data model must enforce this rule; accrual-basis VAT would overstate the claimable
amount.

**CIPC annual return:** CIPC submissions require figures from the annual financial
statements, which are prepared by the external auditor. This project generates the
supporting data (reconciled transaction history) but does not replace the auditor's
role in producing the signed financials.

---

## 9. Success Criteria

Success criteria are objective, observable conditions that confirm each business
objective has been met. They are evaluated at the end of the project.

| Business objective | Success criterion | How it is measured |
|---|---|---|
| BO1 — Reduce manual time | Finance Administrator spends ≤ 10 hours/month on data tasks that previously took 35–45 hours | Time log comparison: before vs after platform launch |
| BO2 — Payment visibility | ML model detects ≥ 70% of high-risk invoices before their due date (recall ≥ 0.70 on high-risk class) | Model evaluation on held-out test set; recall metric |
| BO2 — Payment visibility | Airflow pipeline runs without manual intervention for 4 consecutive weeks | Airflow run logs; zero manually triggered runs |
| BO3 — VAT accuracy | Automated VAT summary matches manual calculation within ZAR 0.02 per invoice | Three months of back-testing against Finance Administrator's manual figures |
| BO4 — Cash-flow trend | Cash-flow dashboard available to Financial Director within 24 hours of month-end without manual preparation | Time from month-end to dashboard availability |
| BO5 — Audit readiness | Reconciled transaction log handed to external auditor with zero post-hoc corrections | Auditor sign-off; zero material audit adjustments arising from data errors |
| DS01 — Prediction model | AUC ≥ 0.80 on held-out test set; precision ≥ 0.70 on high-risk class | MLflow evaluation metrics logged per run |
| DS02 — VAT pipeline | dbt `gold_vat_summary` passes all schema tests and matches manual figure ± ZAR 0.02 | dbt test results; Finance Administrator sign-off |
| DS03 — Cash flow | Running balance reconciles to cashbook within ZAR 1.00 per month | Month-end reconciliation comparison |
| All dbt models | 100% of dbt schema tests pass on every pipeline run | dbt test results logged in Airflow |

---

## 10. Risks and Assumptions

### 10.1 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Azure costs exceed free tier before project completes | Medium | High | Azure Budget Alert set at ZAR 200/month; use Synapse Serverless (no idle cost) |
| dbt connection to Synapse fails due to firewall rules | Medium | Medium | Add local IP to Synapse firewall rule; document steps in setup guide |
| Synthetic data does not reflect real payment behaviour closely enough | Medium | High | Compare model performance against SA industry benchmarks; flag limitation in model card |
| Finance Administrator changes the Excel cashbook format | Low | Medium | Design ingestion script to be format-agnostic; document expected column names clearly |
| SARS changes the VAT201 form fields | Low | Medium | VAT calculation logic is in dbt Gold model — easily updatable without rebuilding pipeline |
| Jupyter notebook fails to execute due to missing dependencies | Medium | Low | Use `requirements.txt` pinned versions; test notebook execution in CI |

### 10.2 Assumptions

The following assumptions are made in this project. If any prove false, the project scope
or design may need to be revisited.

**A1:** Bank statements are exported monthly as CSV files with consistent column names.

**A2:** All supplier invoices include an invoice date, a due date, and a ZAR amount.
Invoices in foreign currencies are out of scope.

**A3:** The applicable VAT rate is 15% for all invoices in scope. Zero-rated or
VAT-exempt suppliers are not modelled in this version.

**A4:** The Finance Administrator has access to a Windows PC with Power BI Desktop
installed.

**A5:** Azure account access with Contributor role on the resource group is available
for the duration of the project.

**A6:** The organisation's supplier base is relatively stable — supplier onboarding and
offboarding happens no more than once per month on average.

---

## 11. Alignment Between Business Problem and Data Usage

This section demonstrates the logical link between the business problem, the data that
will be collected, and how that data answers the business questions. This alignment is
required for WM04 Activity WA0111.

| Business question | Data source(s) used | How the data answers the question | Output produced |
|---|---|---|---|
| Which invoices will be paid late? | Invoice history (invoice date, due date, payment date), supplier master (historical late payment rate, category, payment terms) | ML classifier trained on historical payment behaviour predicts late-payment probability for each open invoice | `gold_invoice_risk_scores` table; Power BI supplier scorecard page |
| What is the monthly VAT input tax? | Invoice data (amount excl VAT, VAT amount, payment date) | dbt Gold model aggregates paid invoices by month; applies cash-basis VAT rule | `gold_vat_summary` table; Power BI VAT summary page |
| Is the cash position improving? | Bank transaction CSV (date, credit, debit, description) | dbt Gold model computes net monthly cash flow and running balance | `gold_cash_flow_monthly` table; Power BI cash flow line chart |
| Which suppliers carry the most risk? | Invoice history cross-referenced with supplier master | Supplier scorecard aggregates late payment rate, overdue value, and average days past due per supplier | `gold_supplier_scorecard` table; Power BI supplier page |
| Is the data complete and correct? | All sources | Great Expectations validation suite checks completeness, VAT accuracy, and referential integrity at Bronze ingestion | Data quality report logged in Airflow; dbt schema test results |
| Has this data changed since yesterday? | Bronze zone partitioned by ingestion date | Each daily ingestion lands in a new partition; ADF pipeline logs run history | ADLS Gen2 Bronze audit trail; ADF pipeline run history |

---

## 12. Project Scope

### 12.1 In scope

The following are explicitly in scope for this project:

- Ingestion of supplier invoice data, bank transaction data, and supplier master data
  into Azure Data Lake Storage Gen2
- Automated data cleaning and validation using dbt Core (Silver layer)
- Automated KPI aggregation using dbt Core (Gold layer): VAT summary, cash-flow trend,
  supplier scorecard
- A binary classification model predicting invoice late-payment risk
- A Power BI dashboard with three pages: executive overview, supplier scorecard, VAT summary
- A daily Apache Airflow pipeline orchestrating ingestion → transformation → scoring
- GitHub Actions CI/CD pipeline for automated testing and deployment
- Documentation aligned to WM04 Parts 1–8
- A WPE logbook recording hours against WA0101–WA0121

### 12.2 Out of scope

The following are explicitly out of scope and noted here to prevent scope creep:

- Foreign currency invoice processing (all invoices are assumed to be ZAR)
- Integration with live banking APIs (CSV export is used instead)
- Automated SARS eFiling submission (the VAT summary is generated for manual keying)
- General ledger or accounting software integration (e.g. Xero, Sage, QuickBooks)
- Processing of customer invoices (accounts receivable) — this project covers accounts
  payable only
- Real-time dashboard refresh (the pipeline runs once daily)
- Multi-company or multi-entity consolidation

---

## 13. Ethical Considerations

### 13.1 Data privacy

No real supplier personal information, banking details, or individual transaction data
from actual persons is used in this project. All data used for model training is
synthetically generated using the Faker library with the South African locale.
The synthetic data is statistically representative of realistic financial patterns
but contains no real identities, VAT numbers, or bank account details.

### 13.2 Model fairness

The payment delay prediction model is trained on supplier-level aggregate data, not on
any personal characteristics of individuals. It does not use race, gender, geographic
location, or any other protected characteristic as a feature. The model predicts
payment risk based on historical payment behaviour, invoice value, and payment terms only.

### 13.3 Responsible use

The model is designed as a decision-support tool, not an automated decision-maker.
All model predictions are reviewed by the Finance Administrator before any action
is taken. The model must not be used to automatically block payments, penalise suppliers,
or make credit decisions without human oversight.

### 13.4 Data handling practices

Raw data is stored in the Bronze zone and retained for 24 months. Data is not shared
with any third party. Access to Azure resources is controlled via Azure Key Vault and
role-based access control (RBAC) — no credentials are stored in code or version control.
All work follows the ethical data handling standards required by the WM04 capstone brief.

### 13.5 Transparency

The model card (`docs/model_card.md`) documents the model's capabilities, limitations,
and appropriate use cases. Any person affected by a model-driven recommendation has the
right to request a human review of that recommendation.
