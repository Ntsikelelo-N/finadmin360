"""
test_features.py
Unit tests for the feature engineering functions.

If feature calculations are wrong, the model trains on wrong inputs and makes
wrong predictions — silently. These tests catch that before it reaches production.
"""

import pandas as pd
import pytest
import sys

sys.path.insert(0, ".")

from src.features.build_features import engineer_features


@pytest.fixture
def sample_df():
    """Minimal DataFrame that matches the structure engineer_features expects."""
    return pd.DataFrame(
        {
            "invoice_date": pd.to_datetime(["2024-01-15", "2024-12-28", "2024-06-01"]),
            "amount_incl_vat": [11500.00, 50000.00, 500.00],
            "vat_amount": [1500.00, 6521.74, 65.22],
            "avg_invoice_value_zar": [10000.00, 45000.00, 1000.00],
            "late_payment_probability": [0.10, 0.40, 0.05],
            "payment_terms_days": [30, 60, 14],
            "category": ["IT Equipment", "Legal Services", "Office Supplies"],
        }
    )


def test_output_has_correct_row_count(sample_df):
    features = engineer_features(sample_df)
    assert features.shape[0] == 3


def test_log_amount_is_always_positive(sample_df):
    features = engineer_features(sample_df)
    assert (features["log_invoice_amount"] > 0).all()


def test_no_null_values_in_output(sample_df):
    """scikit-learn raises an error on NaN — the feature matrix must be clean."""
    features = engineer_features(sample_df)
    null_total = features.isnull().sum().sum()
    assert null_total == 0, f"Found {null_total} null values in feature matrix"


def test_is_month_end_december(sample_df):
    """28 December should trigger is_month_end = 1"""
    features = engineer_features(sample_df)
    assert features.loc[1, "is_month_end"] == 1, "Dec 28 should be flagged as month-end"


def test_is_not_month_end_january(sample_df):
    """15 January should NOT trigger is_month_end"""
    features = engineer_features(sample_df)
    assert (
        features.loc[0, "is_month_end"] == 0
    ), "Jan 15 should not be flagged as month-end"


def test_q4_flag_december(sample_df):
    """December should be Q4"""
    features = engineer_features(sample_df)
    assert features.loc[1, "is_q4"] == 1, "December is Q4"


def test_q4_flag_june(sample_df):
    """June should NOT be Q4"""
    features = engineer_features(sample_df)
    assert features.loc[2, "is_q4"] == 0, "June is not Q4"


def test_category_columns_are_binary(sample_df):
    """One-hot encoded category columns must contain only 0 or 1"""
    features = engineer_features(sample_df)
    cat_cols = [c for c in features.columns if c.startswith("cat_")]
    assert len(cat_cols) > 0, "No category columns found"
    for col in cat_cols:
        assert features[col].isin([0, 1]).all(), f"Column {col} has non-binary values"
