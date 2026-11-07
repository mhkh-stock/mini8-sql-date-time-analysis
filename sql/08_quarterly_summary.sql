-- 08 — Quarterly summary with quarter-over-quarter growth.
-- The pattern to learn: a quarter is arithmetic on the month
-- number — (month - 1) / 3 + 1 — so Q1 = Jan–Mar, Q2 = Apr–Jun,
-- and so on. LAG() over the four quarters gives the previous
-- quarter for the growth calculation, same shape as query 01.
WITH monthly AS (
    SELECT strftime('%Y-%m', order_date) AS month,
           SUM(total) AS revenue
    FROM orders
    GROUP BY month
),
quarterly AS (
    SELECT '2025-Q' || ((CAST(substr(month, 6, 2) AS INTEGER) - 1) / 3 + 1)
               AS quarter,
           SUM(revenue) AS revenue_pkr
    FROM monthly
    GROUP BY quarter
),
with_prev AS (
    SELECT quarter,
           revenue_pkr,
           LAG(revenue_pkr) OVER (ORDER BY quarter) AS prev_q_pkr
    FROM quarterly
)
SELECT quarter,
       revenue_pkr,
       prev_q_pkr,
       CASE WHEN prev_q_pkr IS NULL THEN NULL
            ELSE ROUND(100.0 * (revenue_pkr - prev_q_pkr) / prev_q_pkr, 2)
       END AS qoq_growth_pct
FROM with_prev
ORDER BY quarter;
