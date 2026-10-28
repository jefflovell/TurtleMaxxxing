"""Fictional demo data, for trying the app and for manual testing.

`turtlemaxxxing --demo` runs the app on a throwaway data folder filled with
this data. It never touches your real data folder. All names and amounts are
made up.
"""

import sqlite3
from datetime import date, timedelta

from .budget import ledger, reviews


def _month_start(today: date, months_back: int) -> date:
    index = today.year * 12 + today.month - 1 - months_back
    return date(index // 12, index % 12 + 1, 1)


def seed(conn: sqlite3.Connection, today: date) -> None:
    opened = _month_start(today, 0).isoformat()
    accounts = [
        ("Checking", "checking", 284000, opened, None),
        ("HSA", "hsa", 410000, _month_start(today, 1).isoformat(), 30),
        ("401(k)", "retirement", 3820000, opened, 90),
        ("Brokerage", "brokerage", 120000, opened, None),
        ("Kid A 529", "education", 615000, opened, None),
        ("Kid B 529", "education", 402000, opened, None),
    ]
    ids = {}
    for name, kind, cents, opening, checkin in accounts:
        cur = conn.execute(
            "INSERT INTO accounts (name, kind, opening_balance_cents, opening_date, checkin_every_days) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, kind, cents, opening, checkin),
        )
        ids[name] = cur.lastrowid

    first = _month_start(today, 0)

    def rule(kind, name, cents, start, frequency="monthly", review=None):
        cur = conn.execute(
            "INSERT INTO rules (kind, name, amount_cents, account_id, frequency, start_date, review_every_months) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (kind, name, cents, ids["Checking"], frequency, start.isoformat(), review),
        )
        return cur.lastrowid

    paycheck = rule("income", "Paycheck", 245000, first + timedelta(days=1), "biweekly")
    for account, cents in [("HSA", 12739), ("401(k)", 32258), ("Brokerage", 2500),
                           ("Kid A 529", 5000), ("Kid B 529", 5000)]:
        conn.execute(
            "INSERT INTO rule_splits (rule_id, account_id, amount_cents, label) VALUES (?, ?, ?, ?)",
            (paycheck, ids[account], cents, account),
        )
    rule("bill", "Rent", 165000, first)
    rule("bill", "Car payment", 38900, first + timedelta(days=11))
    rule("bill", "Electric", 12000, first + timedelta(days=17))
    rule("bill", "Internet", 7000, first + timedelta(days=21))
    rule("subscription", "Streaming", 1599, _month_start(today, 3) + timedelta(days=4), review=3)
    rule("subscription", "Music", 1099, first + timedelta(days=8), review=3)
    conn.commit()

    ledger.post_due(conn, today)
    reviews.generate(conn, today)
