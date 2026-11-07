-- 10 — Best and worst sales days, with a rolling 7-day average.
-- The pattern to learn: a recursive CTE builds a 365-day spine
-- for 2025, so days with no sales appear as 0 instead of vanishing.
-- AVG() OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
-- is the rolling 7-day average — it smooths the noisy daily
-- numbers into the trend a manager actually reads. Read the best
-- day (MAX revenue) and the worst days (0) off this one table.
WITH RECURSIVE days(day) AS (
    SELECT '2025-01-01'
    UNION ALL
    SELECT date(day, '+1 day') FROM days WHERE day < '2025-12-31'
),
daily AS (
    SELECT d.day,
           COALESCE(SUM(o.total), 0) AS revenue_pkr
    FROM days AS d
    LEFT JOIN orders AS o ON o.order_date = d.day
    GROUP BY d.day
)
SELECT day,
       revenue_pkr,
       ROUND(AVG(revenue_pkr) OVER (
                 ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
             ), 2) AS rolling_7d_avg_pkr
FROM daily
ORDER BY day;
