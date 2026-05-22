"""
generate_synthetic_data.py

Generates synthetic South African financial data for FinAdmin360.

Why synthetic data?
- The Kaggle dataset does not have ZAR amounts, SA VAT (15%), or SA supplier names.
- Synthetic data lets us demonstrate SA-specific business logic without using real PII.
- All generated data is random and contains no real personal information.

Run this script once to create the datasets:
    python src/ingestion/generate_synthetic_data.py
"""

import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

from src.utils.logging_config import get_logger

logger = get_logger(__name__)
fake = Faker("en_GB")  # South African locale — SA names, cities, phone formats
np.random.seed(42)  # Reproducibility: same seed produces identical data every run
random.seed(42)

SA_VAT_RATE = 0.15  # Current standard South African VAT rate

SUPPLIER_CATEGORIES = [
    "Office Supplies",
    "IT Equipment",
    "Cleaning Services",
    "Courier Services",
    "Legal Services",
    "Accounting Services",
    "Marketing",
    "Security Services",
    "Maintenance",
    "Catering",
]

# Payment terms in days — 30 appears more often because it is most common
PAYMENT_TERMS = [30, 30, 30, 60, 60, 14, 14, 7]

SA_CITIES = [
    "Johannesburg",
    "Cape Town",
    "Durban",
    "Pretoria",
    "Ekurhuleni",
    "Port Elizabeth",
    "Bloemfontein",
]


def generate_cipc_number() -> str:
    """
    Generate a realistic CIPC (Companies and Intellectual Property Commission)
    registration number in the format YYYY/NNNNNN/NN.
    """
    year = random.randint(1990, 2022)
    number = random.randint(100000, 999999)
    suffix = random.choice(["07", "08", "23"])
    return f"{year}/{number}/{suffix}"


def generate_vat_number() -> str:
    """SA VAT registration numbers are 10 digits and begin with 4."""
    return "4" + "".join([str(random.randint(0, 9)) for _ in range(9)])


def generate_suppliers(n: int = 50) -> pd.DataFrame:
    """Generate a supplier master table with n suppliers."""
    suppliers = []
    for i in range(n):
        payment_term = random.choice(PAYMENT_TERMS)
        avg_invoice_value = random.uniform(500, 150_000)
        # Higher-value suppliers tend to have more leverage and worse payment compliance
        late_payment_prob = 0.10 + (avg_invoice_value / 150_000) * 0.30

        suppliers.append(
            {
                "supplier_id": f"SUP{str(i + 1).zfill(4)}",
                "supplier_name": fake.company(),
                "cipc_number": generate_cipc_number(),
                "vat_number": generate_vat_number(),
                "category": random.choice(SUPPLIER_CATEGORIES),
                "payment_terms_days": payment_term,
                "avg_invoice_value_zar": round(avg_invoice_value, 2),
                "late_payment_probability": round(late_payment_prob, 3),
                "email": fake.email(),
                "city": random.choice(SA_CITIES),
                "created_at": fake.date_time_between(start_date="-5y", end_date="-1y"),
            }
        )

    return pd.DataFrame(suppliers)


def generate_invoices(suppliers_df: pd.DataFrame, n: int = 2000) -> pd.DataFrame:
    """
    Generate invoice records covering 24 months.

    Each invoice has: amount, VAT at 15%, due date, payment date (None if unpaid).
    The is_late column is the target variable for the ML model.
    """
    invoices = []
    start_date = datetime.now() - timedelta(days=730)

    for i in range(n):
        supplier = suppliers_df.sample(1).iloc[0]
        invoice_date = fake.date_time_between(start_date=start_date, end_date="now")

        # Seasonal spend — higher in Q1 and Q4 (year-end)
        month = invoice_date.month
        seasonal_factor = 1.2 if month in [1, 11, 12] else 1.0

        amount_excl_vat = round(
            np.random.lognormal(
                mean=np.log(max(supplier["avg_invoice_value_zar"], 1)),
                sigma=0.6,
            )
            * seasonal_factor,
            2,
        )
        vat_amount = round(amount_excl_vat * SA_VAT_RATE, 2)
        amount_incl_vat = round(amount_excl_vat + vat_amount, 2)

        due_date = invoice_date + timedelta(days=int(supplier["payment_terms_days"]))
        is_late = random.random() < supplier["late_payment_probability"]
        is_paid = random.random() < 0.85

        if is_paid:
            if is_late:
                payment_date = due_date + timedelta(days=random.randint(1, 45))
            else:
                payment_date = due_date - timedelta(days=random.randint(1, 5))
            days_past_due = max(0, (payment_date - due_date).days)
        else:
            payment_date = None
            days_past_due = max(0, (datetime.now() - due_date).days)

        if is_paid:
            status = "Paid"
        elif datetime.now().date() > due_date.date():
            status = "Overdue"
        else:
            status = "Pending"

        invoices.append(
            {
                "invoice_id": f"INV{str(i + 1).zfill(6)}",
                "supplier_id": supplier["supplier_id"],
                "invoice_date": invoice_date.date(),
                "due_date": due_date.date(),
                "payment_date": payment_date.date() if payment_date else None,
                "amount_excl_vat": amount_excl_vat,
                "vat_amount": vat_amount,
                "amount_incl_vat": amount_incl_vat,
                "currency": "ZAR",
                "category": supplier["category"],
                "payment_terms_days": supplier["payment_terms_days"],
                "days_past_due": days_past_due,
                "is_late": is_late and is_paid,
                "is_paid": is_paid,
                "invoice_status": status,
            }
        )

    return pd.DataFrame(invoices)


def generate_bank_transactions(
    invoices_df: pd.DataFrame, n: int = 5000
) -> pd.DataFrame:
    """Generate bank cashbook transactions — some linked to invoices, some independent."""
    transactions = []
    start_date = datetime.now() - timedelta(days=730)

    # Payments that correspond to paid invoices
    paid = invoices_df[invoices_df["is_paid"]]
    for _, inv in paid.iterrows():
        transactions.append(
            {
                "transaction_id": f"TXN{len(transactions) + 1:08d}",
                "transaction_date": inv["payment_date"],
                "description": f"EFT Payment - {inv['invoice_id']}",
                "debit_amount": inv["amount_incl_vat"],
                "credit_amount": 0.0,
                "balance_impact": -inv["amount_incl_vat"],
                "category": "Supplier Payment",
                "invoice_reference": inv["invoice_id"],
                "reconciled": True,
            }
        )

    # Revenue and other credits
    for _ in range(int(n * 0.3)):
        amount = round(random.uniform(5_000, 500_000), 2)
        transactions.append(
            {
                "transaction_id": f"TXN{len(transactions) + 1:08d}",
                "transaction_date": fake.date_between(
                    start_date=start_date.date(), end_date="today"
                ),
                "description": random.choice(
                    [
                        "Customer payment received",
                        "Service revenue",
                        "Grant funding",
                        "Interest received",
                    ]
                ),
                "debit_amount": 0.0,
                "credit_amount": amount,
                "balance_impact": amount,
                "category": "Revenue",
                "invoice_reference": None,
                "reconciled": random.random() > 0.05,
            }
        )

    return (
        pd.DataFrame(transactions)
        .sort_values("transaction_date")
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    os.makedirs("data/synthetic", exist_ok=True)
    logger.info("Starting synthetic SA financial data generation...")

    suppliers = generate_suppliers(50)
    suppliers.to_csv("data/synthetic/sa_suppliers.csv", index=False)
    logger.info(f"Generated {len(suppliers)} suppliers")

    invoices = generate_invoices(suppliers, 2000)
    invoices.to_csv("data/synthetic/sa_invoices.csv", index=False)
    logger.info(f"Generated {len(invoices)} invoices")

    transactions = generate_bank_transactions(invoices, 5000)
    transactions.to_csv("data/synthetic/sa_bank_transactions.csv", index=False)
    logger.info(f"Generated {len(transactions)} bank transactions")

    logger.info("--- Dataset Summary ---")
    logger.info(
        f"Date range: {invoices['invoice_date'].min()} to {invoices['invoice_date'].max()}"
    )
    logger.info(f"Total spend incl VAT: ZAR {invoices['amount_incl_vat'].sum():,.2f}")
    logger.info(f"Total VAT input tax: ZAR {invoices['vat_amount'].sum():,.2f}")
    logger.info(f"Late payment rate: {invoices['is_late'].mean():.1%}")
    logger.info(f"Outstanding (unpaid) invoices: {(~invoices['is_paid']).sum()}")
    logger.info("Done. Files saved to data/synthetic/")
