-- 09 — Aging buckets for unpaid / pending orders.
-- The pattern to learn: julianday('2025-12-31') - julianday(due_date)
-- is the number of days an order is overdue (negative = not yet
-- due). A CASE sorts each order into a bucket; the bucket totals
-- must sum to the full pending amount — that is the check.
-- Reference date is fixed at 2025-12-31 so the buckets are
-- reproducible on any run.
SELECT CASE
            WHEN julianday('2025-12-31') - julianday(due_date) <= 0
                THEN 'Current (not yet due)'
            WHEN julianday('2025-12-31') - julianday(due_date) <= 30
                THEN '1-30 days overdue'
            WHEN julianday('2025-12-31') - julianday(due_date) <= 60
                THEN '31-60 days overdue'
            WHEN julianday('2025-12-31') - julianday(due_date) <= 90
                THEN '61-90 days overdue'
            ELSE '90+ days overdue'
       END AS aging_bucket,
       COUNT(*) AS orders,
       SUM(total_pkr) AS amount_pkr
FROM pending_orders
GROUP BY aging_bucket
ORDER BY MIN(julianday('2025-12-31') - julianday(due_date));
