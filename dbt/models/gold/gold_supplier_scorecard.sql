-- gold_supplier_scorecard.sql
-- Supplier performance scorecard used in the Power BI dashboard.
-- Also used as feature input for the ML payment delay model.

WITH invoices  AS (SELECT * FROM {{ ref('silver_invoices') }}),
     suppliers AS (SELECT * FROM {{ ref('silver_suppliers') }}),

supplier_metrics AS (
    SELECT
        i.supplier_id,
        COUNT(*)                                              AS total_invoices,
        ROUND(AVG(i.amount_incl_vat), 2)                     AS avg_invoice_value_zar,
        ROUND(SUM(i.amount_incl_vat), 2)                     AS total_spend_zar,
        ROUND(SUM(i.vat_amount), 2)                          AS total_vat_zar,
        ROUND(AVG(CAST(i.days_past_due AS FLOAT)), 1)        AS avg_days_past_due,
        MAX(i.days_past_due)                                  AS max_days_past_due,
        ROUND(
            100.0 * SUM(CAST(i.is_late AS INT))
                  / NULLIF(COUNT(*), 0),
            1
        )                                                     AS late_payment_pct,
        COUNT(CASE WHEN i.invoice_status = 'OVERDUE' THEN 1 END)
                                                              AS current_overdue_count,
        ROUND(
            SUM(CASE WHEN i.invoice_status = 'OVERDUE'
                     THEN i.amount_incl_vat ELSE 0 END),
            2
        )                                                     AS current_overdue_zar
    FROM invoices i
    GROUP BY i.supplier_id
),

scored AS (
    SELECT
        m.*,
        -- Risk tier used for Power BI conditional formatting (Red / Amber / Green)
        CASE
            WHEN m.late_payment_pct >= 40 THEN 'HIGH'
            WHEN m.late_payment_pct >= 20 THEN 'MEDIUM'
            ELSE 'LOW'
        END AS payment_risk_tier
    FROM supplier_metrics m
)

SELECT
    s.supplier_id,
    s.supplier_name,
    s.category,
    s.city,
    s.payment_terms_days,
    s.cipc_number,
    sc.total_invoices,
    sc.avg_invoice_value_zar,
    sc.total_spend_zar,
    sc.total_vat_zar,
    sc.avg_days_past_due,
    sc.max_days_past_due,
    sc.late_payment_pct,
    sc.current_overdue_count,
    sc.current_overdue_zar,
    sc.payment_risk_tier
FROM scored sc
JOIN suppliers s ON sc.supplier_id = s.supplier_id
ORDER BY sc.late_payment_pct DESC
