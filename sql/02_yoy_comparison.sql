-- 02 — Year-over-year comparison: 2025 vs the 2024 baseline.
-- The pattern to learn: join this year's monthly revenue to a
-- prior-year table on the month number (substr(..., 6, 2)), so
-- each month is compared with the same month a year earlier.
-- February 2025 earned 0 against February 2024's baseline, which
-- is a real -100% — the café was closed that month, not missing data.
WITH monthly AS (
    SELECT strftime('%Y-%m', order_date) AS month,
           SUM(total) AS revenue_2025
    FROM orders
    GROUP BY month
)
SELECT '2025-' || substr(b.month, 6, 2) AS month,
       b.revenue_pkr AS revenue_2024_pkr,
       COALESCE(m.revenue_2025, 0) AS revenue_2025_pkr,
       ROUND(100.0 * (COALESCE(m.revenue_2025, 0) - b.revenue_pkr)
             / b.revenue_pkr, 2) AS yoy_growth_pct
FROM baseline_2024 AS b
LEFT JOIN monthly AS m
       ON substr(m.month, 6, 2) = substr(b.month, 6, 2)
ORDER BY b.month;
