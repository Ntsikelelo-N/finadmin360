-- gold_cash_flow_monthly.sql
-- Monthly cash-flow position used for the executive dashboard and management reporting.
-- Running balance tells management whether cash position is improving or deteriorating.

WITH transactions AS (
    SELECT * FROM {{ ref('silver_bank_transactions') }}
),

monthly AS (
    SELECT
        FORMAT(transaction_date, 'yyyy-MM')  AS year_month,
        ROUND(SUM(credit_amount), 2)          AS total_credits_zar,
        ROUND(SUM(debit_amount), 2)           AS total_debits_zar,
        ROUND(SUM(balance_impact), 2)         AS net_cash_flow_zar,
        COUNT(*)                               AS transaction_count,
        SUM(CASE WHEN reconciled = 0 THEN 1 ELSE 0 END) AS unreconciled_count
    FROM transactions
    GROUP BY FORMAT(transaction_date, 'yyyy-MM')
)

SELECT
    year_month,
    total_credits_zar,
    total_debits_zar,
    net_cash_flow_zar,
    transaction_count,
    unreconciled_count,
    -- Running total: cumulative sum of all net cash flows to date
    ROUND(SUM(net_cash_flow_zar)
        OVER (ORDER BY year_month ROWS UNBOUNDED PRECEDING), 2)
        AS running_cash_balance_zar,
    -- Month-on-month comparison
    LAG(net_cash_flow_zar, 1)
        OVER (ORDER BY year_month)
        AS prev_month_net_cash_flow,
    -- Growth rate: positive = cash improved, negative = cash deteriorated
    ROUND(
        100.0 * (
            net_cash_flow_zar
            - LAG(net_cash_flow_zar, 1) OVER (ORDER BY year_month)
        )
        / NULLIF(
            ABS(LAG(net_cash_flow_zar, 1) OVER (ORDER BY year_month)),
            0
        ),
        1
    ) AS mom_growth_rate_pct
FROM monthly
