"""Build demo.db and run + verify all 10 Mini #8 queries.

Run:  python3 src/run_queries.py      (from the project root)
Writes: data/*.csv (deterministic SAMPLE data, seed 20251107),
        data/demo.db, outputs/*.txt (one per query, headers on).
Asserts (exit 1 on failure):
  - base data: 250 orders, 24 customers, 12 pending, 12 baseline rows
  - data quality: no NULLs, no duplicate order_id, total = qty*unit_price,
    every order on/after its customer's signup date, no Feb 2025 orders
  - Q01/Q03/Q05: 12 months each, Feb 2025 = 0, monthly sums = grand total
  - Q01: Jan MoM is NULL, Mar MoM is NULL (prev month earned 0)
  - Q02: 12 rows, 2024 baseline sums to 44850, 2025 column = grand total
  - Q03: final running total = grand total, running total never falls
  - Q04: 7 weekdays, shares sum to 100% (within 0.05), revenue = grand total
  - Q06: 24 rows, 2 never-ordered customers, days-since-last-order >= 0
  - Q07: cohorts sum to 24 customers
  - Q08: 4 quarters, sum = grand total
  - Q09: buckets sum to 12 orders and PKR 24660, 5 buckets present
  - Q10: 365 days, >= 20 zero-sales days, best day = max daily revenue,
    rolling 7-day average on 2025-01-07 matches the recomputed mean
"""
import calendar
import csv
import random
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
SQL = BASE / "sql"
OUT = BASE / "outputs"
SEED = 20251107
AS_OF = "2025-12-31"
fails = []

# ---------------------------------------------------------------- data
MENU = [  # (item, category, unit_price_pkr, weight)
    ("Doodh Patti Chai", "Hot Drinks", 120, 30),
    ("Elaichi Chai", "Hot Drinks", 150, 14),
    ("Kashmiri Chai", "Hot Drinks", 180, 10),
    ("Green Tea", "Hot Drinks", 100, 8),
    ("Bun Kebab", "Food", 220, 10),
    ("Anda Paratha", "Food", 150, 8),
    ("Samosa (2 pc)", "Food", 60, 6),
    ("Fries", "Food", 180, 4),
    ("Cold Coffee", "Cold Drinks", 280, 4),
    ("Sweet Lassi", "Cold Drinks", 160, 4),
    ("Cake Slice", "Bakery", 250, 1),
    ("Biscuits (pack)", "Bakery", 40, 1),
]

# (customer_id, name, area, signup_date, order_weight; 0 = never orders)
CUSTOMERS = [
    (1, "Ayesha Khan", "Gulberg", "2024-11-15", 10),
    (2, "Bilal Ahmed", "DHA", "2024-12-02", 9),
    (3, "Fatima Zahra", "Model Town", "2025-01-05", 8),
    (4, "Usman Tariq", "Johar Town", "2025-01-20", 7),
    (5, "Hira Shah", "Gulberg", "2025-02-10", 8),
    (6, "Ahmed Raza", "DHA", "2025-03-03", 6),
    (7, "Sana Malik", "Model Town", "2025-03-18", 7),
    (8, "Hassan Ali", "Faisal Town", "2025-04-07", 5),
    (9, "Zainab Fatima", "Gulberg", "2025-05-12", 6),
    (10, "Omar Farooq", "DHA", "2025-05-25", 5),
    (11, "Iqra Aziz", "Johar Town", "2025-06-02", 4),
    (12, "Danish Iqbal", "Model Town", "2025-06-19", 5),
    (13, "Rabia Anwar", "Gulberg", "2025-07-08", 4),
    (14, "Ali Haider", "DHA", "2025-07-22", 4),
    (15, "Noor Fatima", "Faisal Town", "2025-08-05", 3),
    (16, "Hamza Yousuf", "Johar Town", "2025-08-27", 3),
    (17, "Sara Ahmed", "Gulberg", "2025-09-11", 3),
    (18, "Kashif Mehmood", "Model Town", "2025-09-28", 3),
    (19, "Nadia Hussain", "DHA", "2025-10-06", 2),
    (20, "Faisal Iqbal", "Gulberg", "2025-10-19", 2),
    (21, "Mahnoor Asif", "Johar Town", "2025-11-03", 2),
    (22, "Talha Siddiqui", "Model Town", "2025-11-17", 2),
    (23, "Waqar Ahmed", "Faisal Town", "2025-11-25", 0),
    (24, "Amna Khalid", "DHA", "2025-12-01", 0),
]

# Orders per month. February = 0 on purpose: the café closed for
# renovation, so the month-spine queries must prove they show it.
MONTHLY_BUDGET = {1: 20, 2: 0, 3: 24, 4: 22, 5: 26, 6: 21,
                  7: 23, 8: 25, 9: 22, 10: 24, 11: 21, 12: 22}

# (customer_id, total_pkr, due_date) — aging measured vs 2025-12-31
PENDING = [
    (1, 2400, "2026-01-10"),   # Current
    (2, 1800, "2026-01-05"),   # Current
    (3, 950, "2025-12-28"),    # 1-30 days
    (5, 3200, "2025-12-15"),   # 1-30 days
    (7, 1500, "2025-12-02"),   # 1-30 days
    (9, 2750, "2025-11-25"),   # 31-60 days
    (11, 1100, "2025-11-10"),  # 31-60 days
    (13, 4200, "2025-10-20"),  # 61-90 days
    (15, 860, "2025-10-02"),   # 61-90 days
    (17, 1950, "2025-09-15"),  # 90+ days
    (19, 2600, "2025-08-20"),  # 90+ days
    (21, 1350, "2025-07-01"),  # 90+ days
]

BASELINE_2024 = [  # (month '2024-MM', revenue_pkr)
    # Same scale as 2025 (monthly ~PKR 2,500–5,000): 2024 total
    # PKR 44,850 vs 2025 PKR 50,340, so YoY tells a real story —
    # 2025 beat 2024 by ~12% despite losing February entirely.
    ("2024-01", 2600), ("2024-02", 2450), ("2024-03", 3600),
    ("2024-04", 3800), ("2024-05", 4800), ("2024-06", 3500),
    ("2024-07", 4500), ("2024-08", 5000), ("2024-09", 3650),
    ("2024-10", 3600), ("2024-11", 3350), ("2024-12", 4000),
]


def _rand_day(rng, year, month, earliest_day=1):
    last = calendar.monthrange(year, month)[1]
    return rng.randint(earliest_day, last)


def generate_orders():
    rng = random.Random(SEED)
    budgets = dict(MONTHLY_BUDGET)
    signup = {c[0]: c[3] for c in CUSTOMERS}
    ordering = [c for c in CUSTOMERS if c[4] > 0]
    orders = []

    def make_order(customer, year, month, day):
        item, cat, price, _ = rng.choices(
            MENU, weights=[m[3] for m in MENU])[0]
        qty = rng.choices([1, 2, 3], weights=[70, 20, 10])[0]
        orders.append({
            "order_date": f"{year}-{month:02d}-{day:02d}",
            "customer_id": customer[0],
            "item": item, "category": cat,
            "qty": qty, "unit_price": price,
            "total": qty * price,
        })

    # One guaranteed first order per ordering customer, in (or just
    # after) their signup month, so exactly 2 customers never order
    # and no order ever predates its customer's signup.
    for c in ordering:
        sm = int(signup[c[0]][5:7])
        sd = int(signup[c[0]][8:10])
        month = sm if budgets.get(sm, 0) > 0 else sm + 1
        while budgets.get(month, 0) <= 0:
            month += 1
        budgets[month] -= 1
        make_order(c, 2025, month, _rand_day(rng, 2025, month, sd if month == sm else 1))

    # Fill the remaining monthly budgets. Date first, then a customer
    # who had already signed up by that date.
    for month in sorted(budgets):
        for _ in range(budgets[month]):
            day = _rand_day(rng, 2025, month)
            date = f"2025-{month:02d}-{day:02d}"
            eligible = [c for c in ordering if signup[c[0]] <= date]
            customer = rng.choices(
                eligible, weights=[c[4] for c in eligible])[0]
            make_order(customer, 2025, month, day)

    orders.sort(key=lambda o: (o["order_date"], o["customer_id"]))
    for i, o in enumerate(orders, start=1):
        o["order_id"] = i
    return orders


def write_csvs(orders):
    with open(DATA / "customers.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["customer_id", "name", "area", "signup_date"])
        for c in CUSTOMERS:
            w.writerow(c[:4])
    with open(DATA / "orders.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "order_date", "customer_id", "item",
                    "category", "qty", "unit_price", "total"])
        for o in orders:
            w.writerow([o["order_id"], o["order_date"], o["customer_id"],
                        o["item"], o["category"], o["qty"],
                        o["unit_price"], o["total"]])
    with open(DATA / "pending_orders.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pending_id", "customer_id", "total_pkr",
                    "due_date", "status"])
        for i, (cid, total, due) in enumerate(PENDING, start=1):
            w.writerow([i, cid, total, due, "unpaid"])
    with open(DATA / "baseline_2024.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["month", "revenue_pkr"])
        w.writerows(BASELINE_2024)


def load_db(con):
    con.executescript((DATA / "schema.sql").read_text())
    for table, path in [("customers", DATA / "customers.csv"),
                        ("orders", DATA / "orders.csv"),
                        ("pending_orders", DATA / "pending_orders.csv"),
                        ("baseline_2024", DATA / "baseline_2024.csv")]:
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
        cols = list(rows[0].keys())
        con.executemany(
            f"INSERT INTO {table} ({','.join(cols)}) "
            f"VALUES ({','.join('?' * len(cols))})",
            [tuple(r[c] for c in cols) for r in rows])
    con.commit()


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}: {name} {detail}")
    if not cond:
        fails.append(name)


def main():
    orders = generate_orders()
    write_csvs(orders)

    db = DATA / "demo.db"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    load_db(con)

    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ["customers", "orders", "pending_orders",
                        "baseline_2024"]}
    check("base data counts", counts == {"customers": 24, "orders": 250,
                                         "pending_orders": 12,
                                         "baseline_2024": 12}, str(counts))
    grand = con.execute("SELECT SUM(total) FROM orders").fetchone()[0]
    check("grand total > 0", grand > 0, f"(PKR {grand})")
    check("no NULLs in orders",
          con.execute("SELECT COUNT(*) FROM orders WHERE order_date IS NULL"
                      " OR customer_id IS NULL OR total IS NULL").fetchone()[0] == 0)
    check("no duplicate order_id",
          con.execute("SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM orders")
          .fetchone()[0] == 0)
    check("total = qty * unit_price on every row",
          con.execute("SELECT COUNT(*) FROM orders WHERE total <> qty * unit_price")
          .fetchone()[0] == 0)
    check("no order before its customer's signup",
          con.execute("SELECT COUNT(*) FROM orders o JOIN customers c "
                      "ON c.customer_id = o.customer_id "
                      "WHERE o.order_date < c.signup_date").fetchone()[0] == 0)
    check("no Feb 2025 orders (closed month)",
          con.execute("SELECT COUNT(*) FROM orders "
                      "WHERE strftime('%Y-%m', order_date) = '2025-02'")
          .fetchone()[0] == 0)

    results = {}
    OUT.mkdir(parents=True, exist_ok=True)
    for path in sorted(SQL.glob("*.sql")):
        cur = con.execute(path.read_text())
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        results[path.stem[:2]] = (cols, rows)
        out = OUT / f"{path.stem[:2]}_{path.stem[3:]}.txt"
        with open(out, "w") as f:
            f.write(" | ".join(cols) + "\n")
            for r in rows:
                f.write(" | ".join(str(v) for v in r) + "\n")
        print(f"ran {path.name}: {len(rows)} rows -> {out.name}")

    q01 = results["01"][1]
    check("Q01 12 months, Feb = 0",
          len(q01) == 12 and dict((r[0], r[1]) for r in q01)["2025-02"] == 0)
    check("Q01 monthly sums to grand total",
          sum(r[1] for r in q01) == grand, f"({sum(r[1] for r in q01)})")
    check("Q01 Jan MoM NULL, Mar MoM NULL (prev month 0)",
          q01[0][3] is None and q01[2][3] is None,
          f"(Jan={q01[0][3]}, Mar={q01[2][3]})")
    q02 = results["02"][1]
    check("Q02 12 rows, 2024 sums to 44850, 2025 sums to grand",
          len(q02) == 12 and sum(r[1] for r in q02) == 44850
          and sum(r[2] for r in q02) == grand,
          f"(2024={sum(r[1] for r in q02)}, 2025={sum(r[2] for r in q02)})")
    q03 = results["03"][1]
    check("Q03 final running total = grand total",
          len(q03) == 12 and q03[-1][2] == grand, f"({q03[-1][2]})")
    check("Q03 running total never falls",
          all(q03[i][2] >= q03[i - 1][2] for i in range(1, 12)))
    q04 = results["04"][1]
    check("Q04 7 weekdays, shares sum to ~100, revenue = grand",
          len(q04) == 7 and abs(sum(r[4] for r in q04) - 100.0) <= 0.05
          and sum(r[3] for r in q04) == grand,
          f"(shares={sum(r[4] for r in q04)})")
    q05 = results["05"][1]
    check("Q05 12 months, Feb = 0, sums to grand total",
          len(q05) == 12
          and dict((r[0], r[2]) for r in q05)["2025-02"] == 0
          and sum(r[2] for r in q05) == grand)
    q06 = results["06"][1]
    check("Q06 24 rows, 2 never ordered, days-since-last >= 0",
          len(q06) == 24
          and sum(1 for r in q06 if r[4] is None) == 2
          and all(r[5] is None or r[5] >= 0 for r in q06))
    q07 = results["07"][1]
    check("Q07 cohorts sum to 24 customers",
          sum(r[1] for r in q07) == 24, f"({sum(r[1] for r in q07)})")
    check("Q07 same+later+never = signed up in every cohort",
          all(r[2] + r[3] + r[4] == r[1] for r in q07))
    q08 = results["08"][1]
    check("Q08 4 quarters, sum = grand total",
          len(q08) == 4 and sum(r[1] for r in q08) == grand,
          f"({sum(r[1] for r in q08)})")
    q09 = results["09"][1]
    check("Q09 5 buckets, 12 orders, PKR 24660",
          len(q09) == 5 and sum(r[1] for r in q09) == 12
          and sum(r[2] for r in q09) == 24660, str(q09))
    q10 = results["10"][1]
    zero_days = sum(1 for r in q10 if r[1] == 0)
    best = max(q10, key=lambda r: r[1])
    check("Q10 365 days, >= 20 zero-sales days",
          len(q10) == 365 and zero_days >= 20, f"(zero days: {zero_days})")
    check("Q10 best day = max daily revenue",
          best[1] == max(r[1] for r in q10), f"({best[0]}: PKR {best[1]})")
    check("Q10 worst days are 0 (zero-sales days exist)",
          min(r[1] for r in q10) == 0)
    daily = {r[0]: r[1] for r in q10}
    jan7 = [daily[f"2025-01-0{d}"] for d in range(1, 8)]
    expected_avg = round(sum(jan7) / 7, 2)
    actual_avg = dict((r[0], r[2]) for r in q10)["2025-01-07"]
    check("Q10 rolling 7d avg on 2025-01-07 matches recomputation",
          actual_avg == expected_avg, f"({actual_avg} vs {expected_avg})")

    con.close()
    print(f"\ngrand total: PKR {grand}")
    print("all checks passed" if not fails else f"\n{len(fails)} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
