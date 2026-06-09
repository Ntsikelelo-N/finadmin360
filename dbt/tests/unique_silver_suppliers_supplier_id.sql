{{ config(severity='warn') }}

SELECT
    CAST(supplier_id AS NVARCHAR(50)) AS supplier_id,
    COUNT(*) AS n_records
FROM {{ ref('silver_suppliers') }}
WHERE supplier_id IS NOT NULL
GROUP BY CAST(supplier_id AS NVARCHAR(50))
HAVING COUNT(*) > 1
