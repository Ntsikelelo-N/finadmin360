-- silver_bank_transactions.sql
-- Cleans and standardises bank cashbook transaction data.

WITH raw AS (
    SELECT * FROM {{ source('bronze', 'sa_bank_transactions') }}
)

SELECT
    transaction_id,
    TRY_CAST(transaction_date AS DATE)            AS transaction_date,
    TRIM(description)                              AS description,
    CAST(debit_amount AS DECIMAL(18,2))            AS debit_amount,
    CAST(credit_amount AS DECIMAL(18,2))           AS credit_amount,
    CAST(balance_impact AS DECIMAL(18,2))          AS balance_impact,
    UPPER(TRIM(category))                          AS category,
    invoice_reference,
    CAST(reconciled AS BIT)                        AS reconciled,
    GETDATE()                                       AS silver_loaded_at
FROM raw
WHERE
    transaction_id IS NOT NULL
    AND transaction_date IS NOT NULL
    AND (debit_amount > 0 OR credit_amount > 0)  -- Exclude zero-value rows
