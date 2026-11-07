-- 07 — Signup-month cohorts: first vs repeat purchase.
-- The pattern to learn: cohort = the month a customer signed up
-- (strftime('%Y-%m', signup_date)). For each cohort, count who
-- bought in their signup month, who first bought in a later
-- month, who never bought, and how many came back for a second
-- order. A cohort that converts late is a different story from
-- one that never converts at all.
WITH firsts AS (
    SELECT customer_id,
           MIN(order_date) AS first_order_date,
           COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
)
SELECT strftime('%Y-%m', c.signup_date) AS signup_month,
       COUNT(*) AS customers_signed_up,
       SUM(CASE WHEN f.first_order_date IS NULL THEN 1 ELSE 0 END)
           AS never_ordered,
       SUM(CASE WHEN f.first_order_date IS NOT NULL
                     AND strftime('%Y-%m', f.first_order_date)
                         = strftime('%Y-%m', c.signup_date)
                THEN 1 ELSE 0 END) AS first_order_same_month,
       SUM(CASE WHEN f.first_order_date IS NOT NULL
                     AND strftime('%Y-%m', f.first_order_date)
                         > strftime('%Y-%m', c.signup_date)
                THEN 1 ELSE 0 END) AS first_order_later_month,
       SUM(CASE WHEN f.order_count > 1 THEN 1 ELSE 0 END)
           AS repeat_customers
FROM customers AS c
LEFT JOIN firsts AS f ON f.customer_id = c.customer_id
GROUP BY signup_month
ORDER BY signup_month;
