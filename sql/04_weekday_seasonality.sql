-- 04 — Weekday seasonality: revenue by day of the week.
-- The pattern to learn: strftime('%w', date) returns 0 (Sunday)
-- to 6 (Saturday); a CASE turns the number into a readable name.
-- The share column divides each day's revenue by the grand total,
-- so the seven shares must sum to 100% — that is the check.
SELECT CAST(strftime('%w', order_date) AS INTEGER) AS weekday_num,
       CASE CAST(strftime('%w', order_date) AS INTEGER)
            WHEN 0 THEN 'Sunday'
            WHEN 1 THEN 'Monday'
            WHEN 2 THEN 'Tuesday'
            WHEN 3 THEN 'Wednesday'
            WHEN 4 THEN 'Thursday'
            WHEN 5 THEN 'Friday'
            ELSE 'Saturday'
       END AS weekday,
       COUNT(*) AS orders,
       SUM(total) AS revenue_pkr,
       ROUND(100.0 * SUM(total)
             / (SELECT SUM(total) FROM orders), 2) AS share_pct
FROM orders
GROUP BY weekday_num
ORDER BY weekday_num;
