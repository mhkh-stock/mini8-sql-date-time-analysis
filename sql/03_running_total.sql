-- 03 — Running total: cumulative revenue through the year.
-- The pattern to learn: a window SUM() OVER (ORDER BY month)
-- accumulates as it walks the months. The final row must equal
-- the grand total — that is the check that the query is right.
-- The spine keeps February at 0, so the running total is flat
-- across the closed month instead of jumping.
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
)
SELECT m.month,
       COALESCE(mo.revenue, 0) AS revenue_pkr,
       SUM(COALESCE(mo.revenue, 0)) OVER (ORDER BY m.month)
           AS running_total_pkr
FROM months AS m
LEFT JOIN monthly AS mo ON mo.month = m.month
ORDER BY m.month;
