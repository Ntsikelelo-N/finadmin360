-- silver_suppliers.sql
-- Cleans and standardises the supplier master data.

WITH raw AS (
    SELECT * FROM {{ source('bronze', 'sa_suppliers') }}
)

SELECT
    supplier_id,
    UPPER(TRIM(supplier_name))               AS supplier_name,
    cipc_number,
    vat_number,
    UPPER(TRIM(category))                     AS category,
    CAST(payment_terms_days AS INT)           AS payment_terms_days,
    CAST(avg_invoice_value_zar AS DECIMAL(18,2))  AS avg_invoice_value_zar,
    CAST(late_payment_probability AS DECIMAL(6,4)) AS late_payment_probability,
    LOWER(TRIM(email))                        AS email,
    TRIM(city)                                AS city,
    TRY_CAST(created_at AS DATETIME)          AS created_at,
    GETDATE()                                  AS silver_loaded_at
FROM raw
WHERE
    supplier_id IS NOT NULL
    AND supplier_name IS NOT NULL
