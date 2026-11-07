# Mini #8 — data dictionary (SAMPLE / DEMO only)

Fictional Lahore café "ChaiPoint", Jan–Dec 2025. One row per
order, one item per order (a chai café's typical single-item
ticket). Generated deterministically by `src/run_queries.py`
(seed 20251107) — re-running the script rebuilds byte-identical
CSVs and the same database.

## customers (24 rows)
- `customer_id` — PK, 1–24
- `name` — fictional person
- `area` — Lahore neighbourhood (Gulberg, DHA, Model Town,
  Johar Town, Faisal Town)
- `signup_date` — ISO date; 2 in late 2024, the rest across 2025.
  Customers 23 (Waqar Ahmed) and 24 (Amna Khalid) signed up in
  Nov/Dec 2025 and never ordered — queries 06 and 07 need them.

## orders (250 rows)
- `order_id` — PK, 1–250; `customer_id` → customers
- `order_date` — ISO date, Jan–Dec 2025. **No February 2025
  orders**: the café closed that month for renovation, so the
  month-spine queries (01, 03, 05) must show February as 0.
  175 of 365 days have no sales at all.
- `item`, `category` — 12-item menu: Hot Drinks (Doodh Patti
  Chai 120, Elaichi Chai 150, Kashmiri Chai 180, Green Tea 100),
  Food (Bun Kebab 220, Anda Paratha 150, Samosa 60, Fries 180),
  Cold Drinks (Cold Coffee 280, Sweet Lassi 160), Bakery
  (Cake Slice 250, Biscuits 40). Prices in PKR.
- `qty` — 1–3; `unit_price` — PKR; `total` = qty × unit_price.
- No order predates its customer's signup date (asserted on
  every run).

## pending_orders (12 rows)
- `pending_id` — PK; `customer_id` → customers
- `total_pkr` — amount still unpaid; `due_date` — ISO date;
  `status` — always 'unpaid'
- Due dates straddle the fixed reference date 2025-12-31 so
  every aging bucket in query 09 is populated: 2 current,
  3 at 1–30 days, 2 at 31–60, 2 at 61–90, 3 at 90+ days.

## baseline_2024 (12 rows)
- `month` — '2024-01' .. '2024-12'; `revenue_pkr` — that
  month's total revenue (SAMPLE), same scale as 2025 so the
  year-over-year comparison in query 02 is meaningful.
  2024 total PKR 44,850.

## Totals (verified)
- 250 orders, PKR 50,340 — the same total comes out of queries
  01, 02, 03, 04, 05 and 08 independently (asserted on every run).
- 2024 baseline PKR 44,850; pending/unpaid PKR 24,660.
