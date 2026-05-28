-- gold_vat_summary.sql
-- Monthly VAT input tax summary for SARS VAT201 submissions.
-- One row per calendar month.
--
-- Key rule: SARS cash accounting basis — input VAT is claimable only on invoices
-- that have actually been PAID within the VAT period. Accrual-basis would overstate
-- the claimable amount and create a SARS compliance risk.

WITH invoices AS (
    SELECT *
    FROM {{ ref('silver_invoices') }}
    WHERE vat_validation_status = 'VALID'  -- Only include invoices with correct VAT
),

monthly_vat AS (
    SELECT
        FORMAT(invoice_date, 'yyyy-MM')              AS year_month,
        YEAR(invoice_date)                            AS year,
        MONTH(invoice_date)                           AS month,
        COUNT(*)                                       AS invoice_count,
        SUM(amount_excl_vat)                           AS total_excl_vat,
        SUM(vat_amount)                                AS total_vat_input_tax,
        SUM(amount_incl_vat)                           AS total_incl_vat,
        COUNT(CASE WHEN invoice_status = 'PAID'    THEN 1 END) AS paid_count,
        COUNT(CASE WHEN invoice_status = 'OVERDUE' THEN 1 END) AS overdue_count,
        SUM(CASE WHEN invoice_status = 'OVERDUE' THEN amount_incl_vat ELSE 0 END)
            AS overdue_amount_zar,
        -- Cash-basis claimable VAT: only on paid invoices
        SUM(CASE WHEN invoice_status = 'PAID' THEN vat_amount ELSE 0 END)
            AS claimable_vat_input_tax
    FROM invoices
    GROUP BY
        FORMAT(invoice_date, 'yyyy-MM'),
        YEAR(invoice_date),
        MONTH(invoice_date)
)

SELECT
    year_month,
    year,
    month,
    invoice_count,
    ROUND(total_excl_vat, 2)          AS total_excl_vat,
    ROUND(total_vat_input_tax, 2)     AS total_vat_input_tax,
    ROUND(total_incl_vat, 2)          AS total_incl_vat,
    paid_count,
    overdue_count,
    ROUND(overdue_amount_zar, 2)      AS overdue_amount_zar,
    -- This is the figure you key into SARS eFiling (input tax claimable)
    ROUND(claimable_vat_input_tax, 2) AS claimable_vat_input_tax
FROM monthly_vat
ORDER BY year_month
