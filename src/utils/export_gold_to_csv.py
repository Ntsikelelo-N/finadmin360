"""
export_gold_to_csv.py

Re-creates the three Gold layer KPI tables as local CSV files
using pandas — identical business logic to the dbt SQL models.

Run this instead of dbt when Synapse is unavailable.
Output files land in data/gold/ and are read directly by Power BI.
"""

import os
import pandas as pd
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
SA_VAT_RATE = 0.15


def load_silver(data_dir: str):
    """Load and lightly clean the synthetic data (Silver-equivalent)."""
    invoices = pd.read_csv(
        os.path.join(data_dir, "sa_invoices.csv"),
        parse_dates=["invoice_date", "due_date", "payment_date"],
    )
    suppliers = pd.read_csv(os.path.join(data_dir, "sa_suppliers.csv"))

    # Standardise status to uppercase
    invoices["invoice_status"] = invoices["invoice_status"].str.upper()

    # Validate VAT — flag mismatches
    invoices["vat_validation_status"] = invoices.apply(
        lambda r: (
            "VALID"
            if abs(r["vat_amount"] - r["amount_excl_vat"] * SA_VAT_RATE) < 0.02
            else "VAT_MISMATCH"
        ),
        axis=1,
    )

    return invoices, suppliers


def build_gold_vat_summary(invoices: pd.DataFrame) -> pd.DataFrame:
    """Monthly VAT input tax summary — matches gold_vat_summary dbt model."""
    valid = invoices[invoices["vat_validation_status"] == "VALID"].copy()
    valid["year_month"] = valid["invoice_date"].dt.to_period("M").astype(str)

    summary = (
        valid.groupby("year_month")
        .agg(
            invoice_count=("invoice_id", "count"),
            total_excl_vat=("amount_excl_vat", "sum"),
            total_vat_input_tax=("vat_amount", "sum"),
            total_incl_vat=("amount_incl_vat", "sum"),
            paid_count=("invoice_status", lambda s: (s == "PAID").sum()),
            overdue_count=("invoice_status", lambda s: (s == "OVERDUE").sum()),
            overdue_amount_zar=(
                "amount_incl_vat",
                lambda s: s[valid.loc[s.index, "invoice_status"] == "OVERDUE"].sum(),
            ),
        )
        .reset_index()
    )

    # Cash-basis claimable VAT (paid invoices only)
    paid = valid[valid["invoice_status"] == "PAID"]
    paid_vat = (
        paid.groupby(paid["invoice_date"].dt.to_period("M").astype(str))["vat_amount"]
        .sum()
        .rename("claimable_vat_input_tax")
        .reset_index()
        .rename(columns={"invoice_date": "year_month"})
    )
    summary = summary.merge(paid_vat, on="year_month", how="left").fillna(0)
    summary = summary.round(2).sort_values("year_month")
    return summary


def build_gold_supplier_scorecard(
    invoices: pd.DataFrame, suppliers: pd.DataFrame
) -> pd.DataFrame:
    """Supplier scorecard — matches gold_supplier_scorecard dbt model."""
    metrics = (
        invoices.groupby("supplier_id")
        .agg(
            total_invoices=("invoice_id", "count"),
            avg_invoice_value_zar=("amount_incl_vat", "mean"),
            total_spend_zar=("amount_incl_vat", "sum"),
            total_vat_zar=("vat_amount", "sum"),
            avg_days_past_due=("days_past_due", "mean"),
            max_days_past_due=("days_past_due", "max"),
            late_count=("is_late", "sum"),
            current_overdue_count=("invoice_status", lambda s: (s == "OVERDUE").sum()),
            current_overdue_zar=(
                "amount_incl_vat",
                lambda s: s[invoices.loc[s.index, "invoice_status"] == "OVERDUE"].sum(),
            ),
        )
        .reset_index()
    )

    metrics["late_payment_pct"] = (
        100 * metrics["late_count"] / metrics["total_invoices"]
    ).round(1)

    metrics["payment_risk_tier"] = metrics["late_payment_pct"].apply(
        lambda p: "HIGH" if p >= 40 else ("MEDIUM" if p >= 20 else "LOW")
    )

    scorecard = metrics.merge(
        suppliers[
            [
                "supplier_id",
                "supplier_name",
                "category",
                "city",
                "payment_terms_days",
                "cipc_number",
            ]
        ],
        on="supplier_id",
        how="left",
    ).round(2)

    return scorecard.sort_values("late_payment_pct", ascending=False)


def build_gold_cash_flow_monthly(transactions: pd.DataFrame) -> pd.DataFrame:
    """Monthly cash flow — matches gold_cash_flow_monthly dbt model."""
    transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"])
    transactions["year_month"] = (
        transactions["transaction_date"].dt.to_period("M").astype(str)
    )

    monthly = (
        transactions.groupby("year_month")
        .agg(
            total_credits_zar=("credit_amount", "sum"),
            total_debits_zar=("debit_amount", "sum"),
            net_cash_flow_zar=("balance_impact", "sum"),
            transaction_count=("transaction_id", "count"),
            unreconciled_count=("reconciled", lambda s: (~s.astype(bool)).sum()),
        )
        .reset_index()
        .sort_values("year_month")
    )

    monthly["running_cash_balance_zar"] = monthly["net_cash_flow_zar"].cumsum()
    monthly["prev_month_net_cash_flow"] = monthly["net_cash_flow_zar"].shift(1)
    monthly["mom_growth_rate_pct"] = (
        100
        * (monthly["net_cash_flow_zar"] - monthly["prev_month_net_cash_flow"])
        / monthly["prev_month_net_cash_flow"].abs()
    ).round(1)

    return monthly.round(2)


def main():
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    data_dir = os.path.join(project_root, "data", "synthetic")
    gold_dir = os.path.join(project_root, "data", "gold")
    os.makedirs(gold_dir, exist_ok=True)

    logger.info("Loading Silver data...")
    invoices, suppliers = load_silver(data_dir)

    txn_path = os.path.join(data_dir, "sa_bank_transactions.csv")
    transactions = pd.read_csv(txn_path)

    logger.info("Building Gold: VAT summary...")
    vat = build_gold_vat_summary(invoices)
    vat.to_csv(os.path.join(gold_dir, "gold_vat_summary.csv"), index=False)
    logger.info(f"  gold_vat_summary.csv — {len(vat)} rows")

    logger.info("Building Gold: Supplier scorecard...")
    scorecard = build_gold_supplier_scorecard(invoices, suppliers)
    scorecard.to_csv(os.path.join(gold_dir, "gold_supplier_scorecard.csv"), index=False)
    logger.info(f"  gold_supplier_scorecard.csv — {len(scorecard)} rows")

    logger.info("Building Gold: Cash flow monthly...")
    cashflow = build_gold_cash_flow_monthly(transactions)
    cashflow.to_csv(os.path.join(gold_dir, "gold_cash_flow_monthly.csv"), index=False)
    logger.info(f"  gold_cash_flow_monthly.csv — {len(cashflow)} rows")

    logger.info(f"All Gold CSV files saved to {gold_dir}")
    logger.info("Open Power BI → Get Data → Text/CSV → select each file")


if __name__ == "__main__":
    main()
