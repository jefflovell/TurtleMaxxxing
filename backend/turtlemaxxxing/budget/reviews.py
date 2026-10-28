"""The review inbox: small check-ins that keep the automatic ledger honest.

- Balance check-ins: "your HSA should be about $X. What does it actually say?"
  The answer becomes an adjustment entry, so drift never piles up.
- Subscription reviews: "are you still paying for this?" Keep, cancel or
  change the price.

generate() is safe to run any number of times; it never opens a second
review for something that already has one open.
"""

import sqlite3
from datetime import date

from . import ledger
from .schedule import add_months


def _open_exists(conn: sqlite3.Connection, column: str, value: int) -> bool:
    return conn.execute(
        f"SELECT 1 FROM reviews WHERE status = 'open' AND {column} = ?", (value,)
    ).fetchone() is not None


def generate(conn: sqlite3.Connection, today: date) -> int:
    """Open any reviews that are due. Returns how many were opened."""
    opened = 0
    accounts = conn.execute(
        "SELECT * FROM accounts WHERE archived = 0 AND checkin_every_days IS NOT NULL"
    ).fetchall()
    for account in accounts:
        since = date.fromisoformat(account["last_checkin_date"] or account["opening_date"])
        due = date.fromordinal(since.toordinal() + account["checkin_every_days"])
        if due <= today and not _open_exists(conn, "account_id", account["id"]):
            conn.execute(
                "INSERT INTO reviews (kind, account_id, due_date) VALUES ('balance_checkin', ?, ?)",
                (account["id"], due.isoformat()),
            )
            opened += 1

    subscriptions = conn.execute(
        "SELECT * FROM rules WHERE kind = 'subscription' AND review_every_months IS NOT NULL "
        "AND (end_date IS NULL OR end_date >= ?)",
        (today.isoformat(),),
    ).fetchall()
    for rule in subscriptions:
        since = date.fromisoformat(rule["last_reviewed_date"] or rule["start_date"])
        due = add_months(since, rule["review_every_months"])
        if due <= today and not _open_exists(conn, "rule_id", rule["id"]):
            conn.execute(
                "INSERT INTO reviews (kind, rule_id, due_date) VALUES ('subscription_review', ?, ?)",
                (rule["id"], due.isoformat()),
            )
            opened += 1
    conn.commit()
    return opened


def open_checkin(conn: sqlite3.Connection, account_id: int, today: date) -> int:
    """Open a balance check-in right now ("check balance now"). Returns the review id,
    reusing an already-open one."""
    if conn.execute("SELECT 1 FROM accounts WHERE id = ?", (account_id,)).fetchone() is None:
        raise LookupError(f"account {account_id} not found")
    existing = conn.execute(
        "SELECT id FROM reviews WHERE status = 'open' AND account_id = ?", (account_id,)
    ).fetchone()
    if existing:
        return existing["id"]
    cur = conn.execute(
        "INSERT INTO reviews (kind, account_id, due_date) VALUES ('balance_checkin', ?, ?)",
        (account_id, today.isoformat()),
    )
    conn.commit()
    return cur.lastrowid


def _close(conn: sqlite3.Connection, review_id: int, status: str, resolution: str, today: date) -> None:
    conn.execute(
        "UPDATE reviews SET status = ?, resolution = ?, resolved_at = ? WHERE id = ?",
        (status, resolution, today.isoformat(), review_id),
    )


def _get_open(conn: sqlite3.Connection, review_id: int) -> sqlite3.Row:
    review = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    if review is None:
        raise LookupError(f"review {review_id} not found")
    if review["status"] != "open":
        raise ValueError(f"review {review_id} is already {review['status']}")
    return review


def resolve_checkin(conn: sqlite3.Connection, review_id: int, actual_cents: int, today: date) -> int:
    """Record the real balance. Returns the adjustment made (0 if it matched)."""
    review = _get_open(conn, review_id)
    if review["kind"] != "balance_checkin":
        raise ValueError("not a balance check-in")
    expected = ledger.balance(conn, review["account_id"], today)
    adjustment = actual_cents - expected
    if adjustment:
        conn.execute(
            "INSERT INTO entries (account_id, date, amount_cents, description, status) "
            "VALUES (?, ?, ?, 'Balance check-in adjustment', 'adjustment')",
            (review["account_id"], today.isoformat(), adjustment),
        )
    conn.execute(
        "UPDATE accounts SET last_checkin_date = ? WHERE id = ?",
        (today.isoformat(), review["account_id"]),
    )
    _close(conn, review_id, "done", f"actual {actual_cents}, adjusted {adjustment}", today)
    conn.commit()
    return adjustment


def resolve_subscription(
    conn: sqlite3.Connection,
    review_id: int,
    action: str,
    today: date,
    new_amount_cents: int | None = None,
) -> None:
    """action: 'keep', 'cancel' or 'change_price' (with new_amount_cents)."""
    review = _get_open(conn, review_id)
    if review["kind"] != "subscription_review":
        raise ValueError("not a subscription review")
    rule_id = review["rule_id"]
    if action == "keep":
        resolution = "kept"
    elif action == "cancel":
        conn.execute("UPDATE rules SET end_date = ? WHERE id = ?", (today.isoformat(), rule_id))
        resolution = "cancelled"
    elif action == "change_price":
        if new_amount_cents is None or new_amount_cents < 0:
            raise ValueError("change_price needs a new amount")
        conn.execute("UPDATE rules SET amount_cents = ? WHERE id = ?", (new_amount_cents, rule_id))
        resolution = f"price changed to {new_amount_cents}"
    else:
        raise ValueError(f"unknown action: {action}")
    conn.execute(
        "UPDATE rules SET last_reviewed_date = ? WHERE id = ?", (today.isoformat(), rule_id)
    )
    _close(conn, review_id, "done", resolution, today)
    conn.commit()


def dismiss(conn: sqlite3.Connection, review_id: int, today: date) -> None:
    """Skip this one. It comes back at the next regular interval."""
    review = _get_open(conn, review_id)
    if review["kind"] == "balance_checkin":
        conn.execute(
            "UPDATE accounts SET last_checkin_date = ? WHERE id = ?",
            (today.isoformat(), review["account_id"]),
        )
    else:
        conn.execute(
            "UPDATE rules SET last_reviewed_date = ? WHERE id = ?",
            (today.isoformat(), review["rule_id"]),
        )
    _close(conn, review_id, "dismissed", "dismissed", today)
    conn.commit()
