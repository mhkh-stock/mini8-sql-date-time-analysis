-- Mini #8 — SQL Date & Time Analysis Pack
-- SAMPLE / DEMO data only. Fictional Lahore café "ChaiPoint",
-- fictional customers, fictional orders. Never claimed as real
-- client or real business data.
-- SQLite 3.8.3+ (CTEs + window functions required).
-- Run: python3 src/run_queries.py   (builds data/demo.db from data/*.csv)

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS pending_orders;
DROP TABLE IF EXISTS baseline_2024;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id   INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    area          TEXT NOT NULL,  -- Lahore neighbourhood
    signup_date   TEXT NOT NULL   -- ISO date YYYY-MM-DD
);

CREATE TABLE orders (
    order_id      INTEGER PRIMARY KEY,
    order_date    TEXT NOT NULL,  -- ISO date YYYY-MM-DD, Jan–Dec 2025
    customer_id   INTEGER NOT NULL REFERENCES customers (customer_id),
    item          TEXT NOT NULL,
    category      TEXT NOT NULL,  -- Hot Drinks / Food / Cold Drinks / Bakery
    qty           INTEGER NOT NULL CHECK (qty > 0),
    unit_price    INTEGER NOT NULL CHECK (unit_price > 0),  -- PKR
    total         INTEGER NOT NULL CHECK (total > 0)        -- PKR, = qty * unit_price
);

-- Unpaid / pending orders, for the aging-buckets query (09).
-- All aging is measured against the fixed reference date 2025-12-31
-- so the numbers are reproducible on any run.
CREATE TABLE pending_orders (
    pending_id    INTEGER PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customers (customer_id),
    total_pkr     INTEGER NOT NULL CHECK (total_pkr > 0),
    due_date      TEXT NOT NULL,  -- ISO date YYYY-MM-DD
    status        TEXT NOT NULL   -- 'unpaid'
);

-- 2024 monthly revenue totals (SAMPLE), for the year-over-year
-- comparison in query 02. Same 12 months, one row per month.
CREATE TABLE baseline_2024 (
    month         TEXT PRIMARY KEY,  -- '2024-01' .. '2024-12'
    revenue_pkr   INTEGER NOT NULL CHECK (revenue_pkr >= 0)
);
