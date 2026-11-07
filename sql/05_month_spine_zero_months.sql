-- 05 — Month spine: every month of 2025, zero-sales months as 0.
-- The pattern to learn: grouping the orders table alone can never
-- show February, because February has no rows. Build the 12-month
-- spine in a CTE, LEFT JOIN the revenue onto it, COALESCE to 0.
-- Same spine as queries 01 and 03 — the three must agree exactly.
WITH months(month) AS (
    VALUES ('2025-01'), ('2025-02'), ('2025-03'), ('2025-04'),
           ('2025-05'), ('2025-06'), ('2025-07'), ('2025-08'),
           ('2025-09'), ('2025-10'), ('2025-11'), ('2025-12')
),
monthly AS (
    SELECT strftime('%Y-%m', order_date) AS month,
           COUNT(*) AS orders,
           SUM(total) AS revenue
    FROM orders
    GROUP BY month
)
SELECT m.month,
       COALESCE(mo.orders, 0) AS orders,
       COALESCE(mo.revenue, 0) AS revenue_pkr
FROM months AS m
LEFT JOIN monthly AS mo ON mo.month = m.month
ORDER BY m.month;
