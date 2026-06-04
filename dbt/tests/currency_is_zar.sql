-- Custom test: all invoices must have currency = ZAR
SELECT CAST(currency AS NVARCHAR(10)) AS currency
FROM {{ ref('silver_invoices') }}
WHERE CAST(currency AS NVARCHAR(10)) != 'ZAR'
   OR currency IS NULL
