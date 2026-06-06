import numpy as np
import pandas as pd


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build feature matrix from merged invoice+supplier DataFrame.

    After merging invoices with suppliers on supplier_id, pandas renames
    duplicate columns: payment_terms_days → payment_terms_days_x (invoices)
    and payment_terms_days_y (suppliers). Same for category.
    This function handles both the merged case (_x suffix) and the
    pre-merge case (no suffix) for flexibility.
    """
    features = pd.DataFrame(index=df.index)

    # ── Supplier history features ──────────────────────────────────────
    features["supplier_late_pct"] = df["late_payment_probability"]
    features["supplier_avg_invoice_zar"] = df["avg_invoice_value_zar"]

    # Use _x suffix if present (post-merge), otherwise use plain name
    if "payment_terms_days_x" in df.columns:
        features["payment_terms_days"] = df["payment_terms_days_x"]
    else:
        features["payment_terms_days"] = df["payment_terms_days"]

    # ── Invoice characteristics ────────────────────────────────────────
    features["invoice_amount_zar"] = df["amount_incl_vat"]
    features["log_invoice_amount"] = np.log1p(df["amount_incl_vat"])
    features["vat_amount_zar"] = df["vat_amount"]

    q75 = df["amount_incl_vat"].quantile(0.75)
    features["is_large_invoice"] = (df["amount_incl_vat"] > q75).astype(int)

    # ── Calendar features ──────────────────────────────────────────────
    invoice_dates = pd.to_datetime(df["invoice_date"])
    features["invoice_month"] = invoice_dates.dt.month
    features["invoice_quarter"] = invoice_dates.dt.quarter
    features["invoice_day_of_week"] = invoice_dates.dt.dayofweek
    features["is_month_end"] = (invoice_dates.dt.day >= 25).astype(int)
    features["is_q4"] = (invoice_dates.dt.quarter == 4).astype(int)
    features["is_vat_period_end"] = (
        invoice_dates.dt.month.isin([2, 4, 6, 8, 10, 12])
    ).astype(int)

    # ── Category encoding ──────────────────────────────────────────────
    # Use _x suffix if present (post-merge), otherwise plain name
    category_col = "category_x" if "category_x" in df.columns else "category"
    category_dummies = pd.get_dummies(df[category_col], prefix="cat")
    features = pd.concat([features, category_dummies], axis=1)

    features = features.fillna(0)
    return features
