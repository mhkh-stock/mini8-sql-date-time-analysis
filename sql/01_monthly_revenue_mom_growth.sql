-- 01 — Monthly revenue trend with month-over-month growth.
-- The pattern to learn: build a 12-month "spine" in a CTE first,
-- then LEFT JOIN real revenue onto it, so a zero-sales month
-- (February 2025 — café closed for renovation) still appears.
-- LAG() gives the previous month; growth is NULL when there is
-- no previous month, or when the previous month earned 0
-- (dividing by zero would be meaningless, not "infinite growth").
WITH months(month) AS (
    VALUES ('2025-01'), ('2025-02'), ('2025-03'), ('2025-04'),
           ('2025-05'), ('2025-06'), ('2025-07'), ('2025-08'),
           ('2025-09'), ('2025-10'), ('2025-11'), ('2025-12')
),
monthly AS (
    SELECT strftime('%Y-%m', order_date) AS month,
           SUM(total) AS revenue
    FROM orders
    GROUP BY month
),
with_prev AS (
    SELECT m.month,
           COALESCE(mo.revenue, 0) AS revenue_pkr,
           LAG(COALESCE(mo.revenue, 0)) OVER (ORDER BY m.month) AS prev_pkr
    FROM months AS m
    LEFT JOIN monthly AS mo ON mo.month = m.month
)
SELECT month,
       revenue_pkr,
       prev_pkr,
       CASE WHEN prev_pkr IS NULL THEN NULL
            WHEN prev_pkr = 0 THEN NULL
            ELSE ROUND(100.0 * (revenue_pkr - prev_pkr) / prev_pkr, 2)
       END AS mom_growth_pct
FROM with_prev
ORDER BY month;
