-- silver_invoices.sql
-- Cleans and validates raw invoice data from Bronze.
-- Business rules applied here must match the rules described in the data dictionary.

WITH raw_invoices AS (
    -- Pull from Bronze source definition
    SELECT * FROM {{ source('bronze', 'sa_invoices') }}
),

cleaned AS (
    SELECT
        invoice_id,
        supplier_id,

        -- Cast dates safely — TRY_CAST returns NULL instead of erroring on bad dates
        TRY_CAST(invoice_date AS DATE)  AS invoice_date,
        TRY_CAST(due_date AS DATE)      AS due_date,
        TRY_CAST(payment_date AS DATE)  AS payment_date,

        -- Reject negative amounts — a negative invoice would indicate a credit note,
        -- which is handled separately in this version
        CASE WHEN CAST(amount_excl_vat AS DECIMAL(18,2)) > 0
             THEN CAST(amount_excl_vat AS DECIMAL(18,2))
             ELSE NULL
        END AS amount_excl_vat,

        CASE WHEN CAST(vat_amount AS DECIMAL(18,2)) >= 0
             THEN CAST(vat_amount AS DECIMAL(18,2))
             ELSE NULL
        END AS vat_amount,

        CASE WHEN CAST(amount_incl_vat AS DECIMAL(18,2)) > 0
             THEN CAST(amount_incl_vat AS DECIMAL(18,2))
             ELSE NULL
        END AS amount_incl_vat,

        -- VAT validation: VAT should be exactly 15% of excl amount within R0.02 rounding
        CASE
            WHEN ABS(
                CAST(vat_amount AS DECIMAL(18,2)) -
                (CAST(amount_excl_vat AS DECIMAL(18,2)) * 0.15)
            ) < 0.02 THEN 'VALID'
            ELSE 'VAT_MISMATCH'
        END AS vat_validation_status,

        currency,
        category,

        CASE WHEN CAST(payment_terms_days AS INT) > 0
             THEN CAST(payment_terms_days AS INT)
             ELSE NULL
        END AS payment_terms_days,

        CAST(days_past_due AS INT)  AS days_past_due,
        CAST(is_late AS BIT)        AS is_late,
        CAST(is_paid AS BIT)        AS is_paid,

        -- Standardise status to uppercase
        CASE invoice_status
            WHEN 'Paid'    THEN 'PAID'
            WHEN 'Overdue' THEN 'OVERDUE'
            WHEN 'Pending' THEN 'PENDING'
            ELSE 'UNKNOWN'
        END AS invoice_status,

        -- Audit: record when this row entered the Silver layer
        GETDATE()              AS silver_loaded_at,
        '{{ run_started_at }}' AS dbt_run_id

    FROM raw_invoices
    WHERE
        invoice_id IS NOT NULL       -- Every invoice must have an ID
        AND supplier_id IS NOT NULL  -- Cannot reconcile without a supplier
        AND amount_incl_vat > 0      -- Zero-value invoices are invalid
)

SELECT * FROM cleaned
