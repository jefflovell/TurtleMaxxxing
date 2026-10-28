"""The ledger: auto-posting, balances, projections and monthly cash flow.

How "a manual starter that becomes automatic" works:
- Rules describe money that moves on a schedule (see schedule.py).
- post_due() writes an *expected* entry for every rule date up to today.
  It is safe to run any number of times; each date is posted once.
- Future dates are never stored. project() computes them on the fly, so
  editing a rule changes the future without touching the past.

An account's opening balance is its balance at the end of its opening date,
so it already includes everything up to then. Only movements *after* the
opening date are posted to it or counted in its balance.
"""

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

from .schedule import occurrences


@dataclass
class Leg:
    """One account movement produced by one rule occurrence."""

    account_id: int
    amount_cents: int
    description: str


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def splits_for(conn: sqlite3.Connection, rule_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM rule_splits WHERE rule_id = ? ORDER BY id", (rule_id,)
    ).fetchall()


def legs_for(rule: sqlite3.Row, splits: list[sqlite3.Row]) -> list[Leg]:
    """Income goes to each split, and the remainder to the rule's account.
    Bills and subscriptions take the amount out of the rule's account."""
    if rule["kind"] != "income":
        return [Leg(rule["account_id"], -rule["amount_cents"], rule["name"])]
    legs = [
        Leg(s["account_id"], s["amount_cents"], f"{rule['name']}: {s['label'] or 'split'}")
        for s in splits
    ]
    remainder = rule["amount_cents"] - sum(s["amount_cents"] for s in splits)
    if remainder:
        legs.append(Leg(rule["account_id"], remainder, rule["name"]))
    return legs


def opening_dates(conn: sqlite3.Connection) -> dict[int, str]:
    return {r["id"]: r["opening_date"] for r in conn.execute("SELECT id, opening_date FROM accounts")}


def rule_dates(rule: sqlite3.Row, window_start: date, window_end: date) -> list[date]:
    return list(
        occurrences(
            rule["frequency"],
            date.fromisoformat(rule["start_date"]),
            window_start,
            window_end,
            end=_d(rule["end_date"]),
            second_day=rule["second_day"],
        )
    )


def post_due(conn: sqlite3.Connection, today: date) -> int:
    """Create expected entries for every rule date up to today. Returns how many."""
    created = 0
    opened = opening_dates(conn)
    for rule in conn.execute("SELECT * FROM rules").fetchall():
        posted = _d(rule["posted_through"])
        window_start = posted + timedelta(days=1) if posted else date.fromisoformat(rule["start_date"])
        if window_start > today:
            continue
        legs = legs_for(rule, splits_for(conn, rule["id"]))
        for when in rule_dates(rule, window_start, today):
            for leg in legs:
                if when.isoformat() <= opened[leg.account_id]:
                    continue  # already part of the account's opening balance
                cur = conn.execute(
                    "INSERT OR IGNORE INTO entries "
                    "(account_id, date, amount_cents, description, status, rule_id, occurrence_date) "
                    "VALUES (?, ?, ?, ?, 'expected', ?, ?)",
                    (leg.account_id, when.isoformat(), leg.amount_cents, leg.description,
                     rule["id"], when.isoformat()),
                )
                created += cur.rowcount
        conn.execute(
            "UPDATE rules SET posted_through = ? WHERE id = ?", (today.isoformat(), rule["id"])
        )
    conn.commit()
    return created


def project(conn: sqlite3.Connection, start: date, end: date, today: date) -> list[dict]:
    """Future (not yet posted) movements between start and end, after today."""
    window_start = max(start, today + timedelta(days=1))
    if window_start > end:
        return []
    events = []
    opened = opening_dates(conn)
    for rule in conn.execute("SELECT * FROM rules").fetchall():
        legs = legs_for(rule, splits_for(conn, rule["id"]))
        for when in rule_dates(rule, window_start, end):
            # Skip dates the user already confirmed early ("paid ahead").
            confirmed = {
                row["account_id"]
                for row in conn.execute(
                    "SELECT account_id FROM entries WHERE rule_id = ? AND occurrence_date = ?",
                    (rule["id"], when.isoformat()),
                )
            }
            for leg in legs:
                if leg.account_id in confirmed or when.isoformat() <= opened[leg.account_id]:
                    continue
                events.append({
                    "entry_id": None,
                    "rule_id": rule["id"],
                    "rule_kind": rule["kind"],
                    "account_id": leg.account_id,
                    "date": when.isoformat(),
                    "amount_cents": leg.amount_cents,
                    "description": leg.description,
                    "status": "projected",
                })
    return events


def balance(conn: sqlite3.Connection, account_id: int, as_of: date) -> int:
    """Opening balance plus every entry after the opening date, up to and including as_of."""
    account = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if account is None:
        raise LookupError(f"account {account_id} not found")
    opening = account["opening_balance_cents"] if account["opening_date"] <= as_of.isoformat() else 0
    total = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) FROM entries "
        "WHERE account_id = ? AND date > ? AND date <= ?",
        (account_id, account["opening_date"], as_of.isoformat()),
    ).fetchone()[0]
    return opening + total


def stored_events(conn: sqlite3.Connection, start: date, end: date) -> list[dict]:
    rows = conn.execute(
        "SELECT e.*, r.kind AS rule_kind FROM entries e LEFT JOIN rules r ON r.id = e.rule_id "
        "WHERE e.date BETWEEN ? AND ? ORDER BY e.date, e.id",
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    return [
        {
            "entry_id": r["id"],
            "rule_id": r["rule_id"],
            "rule_kind": r["rule_kind"],
            "account_id": r["account_id"],
            "date": r["date"],
            "amount_cents": r["amount_cents"],
            "description": r["description"],
            "status": r["status"],
        }
        for r in rows
    ]


def month_bounds(year: int, month: int) -> tuple[date, date]:
    first = date(year, month, 1)
    next_first = date(year + (month == 12), month % 12 + 1, 1)
    return first, next_first - timedelta(days=1)


def events_between(conn: sqlite3.Connection, start: date, end: date, today: date) -> list[dict]:
    events = stored_events(conn, start, end) + project(conn, start, end, today)
    return sorted(events, key=lambda e: (e["date"], e["amount_cents"] < 0))


def cashflow(
    conn: sqlite3.Connection, account_ids: list[int], year: int, month: int, today: date
) -> dict:
    """Daily running balance across a month for the given accounts, with every
    movement on its date. Past days use the ledger; future days add projections."""
    first, last = month_bounds(year, month)
    day_before = first - timedelta(days=1)
    wanted = set(account_ids)

    start_balance = sum(balance(conn, a, day_before) for a in account_ids)
    if day_before > today:
        # The month is in the future: add projected movements from tomorrow until it starts.
        start_balance += sum(
            e["amount_cents"]
            for e in project(conn, today + timedelta(days=1), day_before, today)
            if e["account_id"] in wanted
        )

    opened = opening_dates(conn)
    events = [
        e for e in events_between(conn, first, last, today)
        if e["account_id"] in wanted and e["date"] > opened[e["account_id"]]
    ]
    # An account opened during this month starts its balance on its opening date.
    for account in conn.execute("SELECT * FROM accounts").fetchall():
        if account["id"] in wanted and first.isoformat() <= account["opening_date"] <= last.isoformat():
            events.append({
                "entry_id": None,
                "rule_id": None,
                "rule_kind": None,
                "account_id": account["id"],
                "date": account["opening_date"],
                "amount_cents": account["opening_balance_cents"],
                "description": "Starting balance",
                "status": "opening",
            })
    events.sort(key=lambda e: (e["date"], e["status"] != "opening", e["amount_cents"] < 0))
    by_day: dict[str, list[dict]] = {}
    for e in events:
        by_day.setdefault(e["date"], []).append(e)

    days = []
    running = start_balance
    current = first
    while current <= last:
        todays = by_day.get(current.isoformat(), [])
        money_in = sum(e["amount_cents"] for e in todays if e["amount_cents"] > 0)
        money_out = sum(e["amount_cents"] for e in todays if e["amount_cents"] < 0)
        running += money_in + money_out
        days.append({
            "date": current.isoformat(),
            "balance_cents": running,
            "in_cents": money_in,
            "out_cents": money_out,
            "projected": current > today,
        })
        current += timedelta(days=1)

    low = min(days, key=lambda d: d["balance_cents"])
    return {
        "month": f"{year:04d}-{month:02d}",
        "account_ids": account_ids,
        "start_balance_cents": start_balance,
        "end_balance_cents": running,
        "low_point": {"date": low["date"], "balance_cents": low["balance_cents"]},
        "days": days,
        "events": events,
    }


def confirm_occurrence(conn: sqlite3.Connection, rule_id: int, when: date) -> None:
    """Mark a rule date as happened, whether it was auto-posted already or is
    in the future (e.g. a bill paid early)."""
    rule = conn.execute("SELECT * FROM rules WHERE id = ?", (rule_id,)).fetchone()
    if rule is None:
        raise LookupError(f"rule {rule_id} not found")
    if when not in rule_dates(rule, when, when):
        raise ValueError(f"{when} is not a date for rule {rule_id}")
    for leg in legs_for(rule, splits_for(conn, rule_id)):
        conn.execute(
            "INSERT INTO entries "
            "(account_id, date, amount_cents, description, status, rule_id, occurrence_date) "
            "VALUES (?, ?, ?, ?, 'confirmed', ?, ?) "
            "ON CONFLICT (rule_id, occurrence_date, account_id) WHERE rule_id IS NOT NULL "
            "DO UPDATE SET status = 'confirmed'",
            (leg.account_id, when.isoformat(), leg.amount_cents, leg.description,
             rule_id, when.isoformat()),
        )
    conn.commit()
