# Mini #8 — SQL Date & Time Analysis Pack

**SAMPLE / DEMO data only.** Fictional Lahore café "ChaiPoint",
fictional customers, fictional orders. Never claimed as real
client or real business data.

The date-and-time half of the SQL test, after Mini #1's window
functions and Mini #3's CTEs and joins: `strftime` month/weekday
extraction, `julianday` arithmetic, date spines that keep
zero-sales months and days visible, running totals, and rolling
averages. One business question per file, one pattern named
per file.

## Demo dataset

Fictional café, Jan–Dec 2025: 24 customers (2 never ordered) ·
250 orders · PKR 50,340 total revenue · one zero-sales month
(February 2025 — closed for renovation) · 175 zero-sales days
out of 365 · 12 unpaid orders worth PKR 24,660 · a 2024 monthly
baseline (PKR 44,850) for the year-over-year comparison.
Schema: `data/schema.sql` · CSVs: `data/*.csv` (generated
deterministically, seed 20251107) · Dictionary: `data/README.md` ·
Built database: `data/demo.db` (rebuild any time with
`python3 src/run_queries.py`, which also verifies every query).

## How to run (3 steps)

1. `cd mini8-sql-date-time-analysis`
2. `python3 src/run_queries.py` — generates `data/*.csv`, builds
   `data/demo.db`, runs all 10 queries, writes `outputs/*.txt`,
   and asserts the checks below
3. Run any query by hand, e.g.
   `sqlite3 -header -column data/demo.db < sql/01_monthly_revenue_mom_growth.sql`

Requires Python 3.10+ and SQLite (standard library only, no
packages to install). Verified on Python 3.12.3, SQLite 3.45.1.

## Queries

| File | Business question | Teaches | Verified output |
|---|---|---|---|
| `sql/01_monthly_revenue_mom_growth.sql` | How did each month do vs the month before? | Month spine + `LAG()`; NULL growth when the previous month earned 0 | 12 rows; best Aug PKR 5,940 (+12.71%); Feb 0 (−100.0%); Mar MoM NULL (prev = 0) |
| `sql/02_yoy_comparison.sql` | Did 2025 beat the same month in 2024? | Join on month number across years | 12 rows; 2025 PKR 50,340 vs 2024 PKR 44,850 (+12.2%); every trading month up 14.86–25.0% |
| `sql/03_running_total.sql` | How did the year's revenue accumulate? | Window `SUM() OVER (ORDER BY month)` | 12 rows; crossed PKR 25,000 in Jul (27,130); final = 50,340 |
| `sql/04_weekday_seasonality.sql` | Which weekday earns most? | `strftime('%w')` + CASE day names | 7 rows; #1 Thursday PKR 9,110 (18.10%, 45 orders); worst Tuesday PKR 4,790 (9.52%) |
| `sql/05_month_spine_zero_months.sql` | What did each month earn, including dead months? | 12-month spine + LEFT JOIN + COALESCE | 12 rows; Feb 2025 = 0; months sum to 50,340 |
| `sql/06_days_since_last_order.sql` | Who has gone quiet, and how long is the usual gap? | `LAG()` per customer + `julianday` difference vs 2025-12-31 | 24 rows; most lapsed: Ali Haider, 128 days; most active: Ayesha Khan, 35 orders, last order 2025-12-31 |
| `sql/07_signup_month_cohorts.sql` | Do customers buy in their signup month, later, or never? | Cohort = `strftime('%Y-%m', signup_date)` | 14 cohorts; 19 of 22 buyers first ordered in their signup month; 18 repeat buyers |
| `sql/08_quarterly_summary.sql` | How did each quarter do vs the last? | Quarter arithmetic `(month−1)/3+1` + `LAG()` | 4 rows; Q1 7,490 · Q2 14,370 (+91.86%) · Q3 15,500 (+7.86%) · Q4 12,980 (−16.26%) |
| `sql/09_aging_buckets.sql` | How old is the unpaid money? | `julianday` overdue days + CASE buckets | 5 buckets; 90+ days is the biggest: PKR 5,900 (3 orders); total pending PKR 24,660 |
| `sql/10_best_worst_days_rolling_avg.sql` | Best/worst days, and the 7-day trend? | Recursive 365-day spine + rolling `AVG() OVER (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` | 365 rows; best day 2025-08-14, PKR 1,000; 175 zero-sales days; rolling 7-day avg on 2025-01-07 = 98.57 |

## Key findings (from the verified run)

- **Growth despite a lost month:** 2025 revenue PKR 50,340 beat
  2024's PKR 44,850 by 12.2%, even with February earning 0 —
  every trading month grew 14.86–25.0% year over year.
- **The closure is visible, not hidden:** February shows 0 in
  the month spine, −100.0% month over month, and the running
  total stays flat at PKR 2,990 across it; March's MoM growth
  is honestly NULL (you cannot divide by a zero month).
- **Weekends are not the peak:** Thursday is the best weekday
  (PKR 9,110, 18.10%), ahead of Monday (PKR 8,340); Tuesday is
  the weakest (PKR 4,790, 9.52%) — the quiet-day promo belongs
  on Tuesday, not Saturday.
- **Retention is strong where it exists:** 18 of the 22 ordering
  customers came back for a second order, and 19 of 22 bought
  in their signup month. The risk is at the edges: Ali Haider
  has not ordered in 128 days, and 2 December signups never
  ordered at all.
- **Unpaid money is aging:** PKR 5,900 of the PKR 24,660 pending
  is 90+ days overdue — the largest bucket — while only
  PKR 4,200 is not yet due.
- **Daily sales are lumpy:** the best day (2025-08-14) took
  PKR 1,000 while 175 of 365 days took 0; the rolling 7-day
  average is the number to watch, not any single day.

## Verification (done before delivery)

- All 10 files execute against `data/demo.db` with no errors.
- **29 checks pass on every run** (`python3 src/run_queries.py`,
  exit 0): base counts (250 orders, 24 customers, 12 pending,
  12 baseline rows); data quality (no NULLs, no duplicate
  order_id, total = qty × unit_price on every row, no order
  before its customer's signup, no February 2025 orders);
  reconciliation — the PKR 50,340 grand total comes out of
  queries 01, 02, 03, 04, 05 and 08 independently; month
  spine = 12 months with February 0; running total ends at the
  grand total and never falls; weekday shares sum to 100.01%
  (rounding only, check allows ±0.05); cohorts sum to 24
  customers; aging buckets sum to 12 orders and PKR 24,660;
  query 10 covers all 365 days with ≥20 zero-sales days and
  its rolling 7-day average on 2025-01-07 (98.57) matches an
  independent recomputation.
- One real data bug found and fixed during verification: the
  first 2024 baseline was ~5× the 2025 scale (PKR 256,900),
  which made every YoY figure a meaningless −75% to −84%.
  The baseline was rebuilt at the same scale as 2025
  (PKR 44,850 total), so the YoY comparison now tells the real
  story (+12.2% overall).
- Verified outputs are saved in `outputs/` (one `.txt` per
  query); `src/run_queries.py` re-asserts all of the above on
  every run.

## Limits

- SAMPLE / DEMO data only — fictional café, Jan–Dec 2025,
  SQLite only. One row per order, one item per order; a real
  café's multi-item tickets would need an order-lines table.
- All aging and "days since last order" figures use the fixed
  reference date 2025-12-31, so the numbers are reproducible —
  on a live dataset that date would be "today".
- Query 04's per-weekday shares are rounded to 2 decimals, so
  the displayed shares sum to 100.01%; the unrounded shares
  sum to exactly 100%.
- Query 06's `avg_gap_days` is NULL for one-order customers
  (there is no gap to average yet), and `days_since_last_order`
  is NULL for the 2 never-ordered customers.

## Note for the publisher

No GitHub repo was created and nothing was pushed, per the task —
the GitHub App cannot create repos, so this mini stays built
locally, verified and ready until its repo exists.
