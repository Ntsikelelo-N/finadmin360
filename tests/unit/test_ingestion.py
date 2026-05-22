"""
test_ingestion.py
Unit tests for the data generation and ingestion functions.

Why test data generation?
If the generator silently produces wrong data (negative amounts, future dates,
wrong VAT amounts), the ML model trains on bad data and produces bad predictions.
Tests catch this before it reaches production.
"""

import pandas as pd
import pytest
import sys

sys.path.insert(0, ".")

from src.ingestion.generate_synthetic_data import (
    generate_suppliers,
    generate_invoices,
    SA_VAT_RATE,
)


@pytest.fixture(scope="module")
def suppliers():
    return generate_suppliers(10)


@pytest.fixture(scope="module")
def invoices(suppliers):
    return generate_invoices(suppliers, 50)


class TestSupplierGeneration:
    def test_correct_row_count(self, suppliers):
        assert len(suppliers) == 10

    def test_no_null_ids(self, suppliers):
        assert suppliers["supplier_id"].notna().all()

    def test_unique_supplier_ids(self, suppliers):
        assert suppliers["supplier_id"].is_unique

    def test_valid_payment_terms(self, suppliers):
        valid_terms = {7, 14, 30, 60}
        assert set(suppliers["payment_terms_days"].unique()).issubset(valid_terms)

    def test_cipc_format(self, suppliers):
        pattern = r"^\d{4}/\d{6}/\d{2}$"
        assert suppliers["cipc_number"].str.match(pattern).all()

    def test_vat_number_format(self, suppliers):
        assert suppliers["vat_number"].str.startswith("4").all()
        assert (suppliers["vat_number"].str.len() == 10).all()


class TestInvoiceGeneration:
    def test_correct_row_count(self, invoices):
        assert len(invoices) == 50

    def test_no_null_invoice_ids(self, invoices):
        assert invoices["invoice_id"].notna().all()

    def test_unique_invoice_ids(self, invoices):
        assert invoices["invoice_id"].is_unique

    def test_all_amounts_positive(self, invoices):
        assert (invoices["amount_excl_vat"] > 0).all()
        assert (invoices["amount_incl_vat"] > 0).all()

    def test_vat_is_fifteen_percent(self, invoices):
        expected_vat = (invoices["amount_excl_vat"] * SA_VAT_RATE).round(2)
        difference = (invoices["vat_amount"] - expected_vat).abs()
        assert (
            difference < 0.02
        ).all(), "VAT amount deviates from 15% by more than R0.02"

    def test_incl_equals_excl_plus_vat(self, invoices):
        expected = (invoices["amount_excl_vat"] + invoices["vat_amount"]).round(2)
        assert (invoices["amount_incl_vat"] == expected).all()

    def test_due_date_after_invoice_date(self, invoices):
        invoice_dates = pd.to_datetime(invoices["invoice_date"])
        due_dates = pd.to_datetime(invoices["due_date"])
        assert (due_dates >= invoice_dates).all()

    def test_valid_status_values(self, invoices):
        valid_statuses = {"Paid", "Overdue", "Pending"}
        assert set(invoices["invoice_status"].unique()).issubset(valid_statuses)

    def test_currency_is_zar(self, invoices):
        assert (invoices["currency"] == "ZAR").all()

    def test_no_nulls_in_required_columns(self, invoices):
        required_cols = [
            "invoice_id",
            "supplier_id",
            "invoice_date",
            "due_date",
            "amount_incl_vat",
            "currency",
        ]
        for col in required_cols:
            assert invoices[col].notna().all(), f"Null values found in {col}"
