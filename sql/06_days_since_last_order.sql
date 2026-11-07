-- 06 — Days since last order per customer, and purchase gaps.
-- The pattern to learn: LAG() over each customer's orders gives
-- the previous order date; julianday() turns two dates into a
-- day count. "Days since last order" is measured against the
-- fixed reference date 2025-12-31, so the answer never drifts.
-- Customers who never ordered show NULL — they are listed, not
-- hidden, because a lapsed customer is the finding.
WITH ordered AS (
    SELECT customer_id,
           order_date,
           LAG(order_date) OVER (
               PARTITION BY customer_id ORDER BY order_date
           ) AS prev_order_date
    FROM orders
),
gaps AS (
    SELECT customer_id,
           MAX(order_date) AS last_order_date,
           COUNT(*) AS order_count,
           AVG(julianday(order_date) - julianday(prev_order_date))
               AS avg_gap_days
    FROM ordered
    GROUP BY customer_id
)
SELECT c.customer_id,
       c.name,
       c.signup_date,
       g.order_count,
       g.last_order_date,
       CAST(julianday('2025-12-31') - julianday(g.last_order_date)
            AS INTEGER) AS days_since_last_order,
       ROUND(g.avg_gap_days, 1) AS avg_gap_days
FROM customers AS c
LEFT JOIN gaps AS g ON g.customer_id = c.customer_id
ORDER BY days_since_last_order DESC;
