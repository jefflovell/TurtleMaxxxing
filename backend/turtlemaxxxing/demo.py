"""Fictional demo data, for trying the app and for manual testing.

`turtlemaxxxing --demo` runs the app on a throwaway data folder filled with
this data. It never touches your real data folder. All names and amounts are
made up.
"""

import json
import sqlite3
from datetime import date, datetime, timedelta

from .budget import ledger, reviews


def _month_start(today: date, months_back: int) -> date:
    index = today.year * 12 + today.month - 1 - months_back
    return date(index // 12, index % 12 + 1, 1)


def seed(conn: sqlite3.Connection, today: date, now: datetime | None = None) -> None:
    seed_budget(conn, today)
    seed_tasks(conn, today, now or datetime.combine(today, datetime.now().time()))


def seed_tasks(conn: sqlite3.Connection, today: date, now: datetime) -> None:
    label = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM labels")}
    reno = conn.execute("INSERT INTO lists (name, emoji, position) VALUES ('Home reno', '🔨', 1)").lastrowid
    party = conn.execute("INSERT INTO lists (name, emoji, position) VALUES ('Birthday party', '🎂', 2)").lastrowid

    def day(offset: int) -> str:
        return (today + timedelta(days=offset)).isoformat()

    tasks = [
        # title, status, list, due, time, labels, blocked note
        ("Renew car registration", "todo", None, day(-2), None, ["urgent", "money"], None),
        ("Call the plumber about the leak", "todo", reno, day(0), "10:00", ["urgent", "home"], None),
        ("Pick up dry cleaning", "todo", None, day(0), None, [], None),
        ("Review Smith St proposal", "in_progress", None, day(3), "12:00", ["work", "important"], None),
        ("Prep for client meeting", "todo", None, day(5), None, ["work", "private"], None),
        ("Renew passport", "blocked", None, None, None, ["important"], "waiting on new photos"),
        ("Order the cake", "in_progress", party, day(6), None, ["family"], None),
        ("Pick tile for the bathroom", "todo", reno, None, None, ["home"], None),
        ("Look up the code for deck railings", "todo", reno, None, None, ["home"], None),
    ]
    ids = {}
    for position, (title, status, list_id, due, at, names, blocked) in enumerate(tasks):
        ids[title] = conn.execute(
            "INSERT INTO tasks (title, status, list_id, due_date, due_time, blocked_note, position) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, status, list_id, due, at, blocked, position),
        ).lastrowid
        for name in names:
            conn.execute("INSERT INTO task_labels VALUES (?, ?)", (ids[title], label[name]))

    done = conn.execute(
        "INSERT INTO tasks (title, status, completed_at, due_date) VALUES ('Pay the water bill', 'done', ?, ?)",
        (now.isoformat(timespec="seconds"), day(0)),
    ).lastrowid
    conn.execute("INSERT INTO task_labels VALUES (?, ?)", (done, label["money"]))

    # One reminder already due, so the demo shows a reminder pop-up right away.
    conn.execute(
        "INSERT INTO task_reminders (task_id, remind_at) VALUES (?, ?)",
        (ids["Call the plumber about the leak"], (now - timedelta(minutes=5)).isoformat(timespec="minutes")),
    )
    # Contacts, linked to the tasks they're about.
    people = [
        # name, organization, role, email, phone, location, labels, tasks
        ("Mr. Anderson", "Smith Agency", "Client contact", "anderson@example.com", "555-0100",
         "Smith Agency, 2nd floor", ["work"], ["Review Smith St proposal", "Prep for client meeting"]),
        ("Pat Rivera", "Leak Busters Plumbing", "Plumber", "", "555-0142",
         "", ["home"], ["Call the plumber about the leak"]),
        ("Sam (bakery)", "Corner Bakery", "", "", "555-0177",
         "Corner Bakery, Main St", ["family"], ["Order the cake"]),
        ("Jordan Lee", "Smith Agency", "Project manager", "jordan@example.com", "",
         "", ["work", "private"], []),
    ]
    for name, org, role, email, phone, where, names, task_titles in people:
        contact = conn.execute(
            "INSERT INTO contacts (name, organization, role, email, phone, location) VALUES (?, ?, ?, ?, ?, ?)",
            (name, org, role, email, phone, where),
        ).lastrowid
        for label_name in names:
            conn.execute("INSERT INTO contact_labels VALUES (?, ?)", (contact, label[label_name]))
        for title in task_titles:
            conn.execute("INSERT INTO task_contacts VALUES (?, ?)", (ids[title], contact))

    # Saved filters pinned in the sidebar.
    for position, (name, emoji, filters) in enumerate([
        ("Fires", "🔥", {"label_ids": [label["critical"], label["urgent"]], "statuses": ["todo", "in_progress", "blocked"]}),
        ("Home reno board", "🔨", {"scope": reno, "view": "board"}),
    ]):
        conn.execute(
            "INSERT INTO saved_filters (name, emoji, filters, position) VALUES (?, ?, ?, ?)",
            (name, emoji, json.dumps(filters), position),
        )
    conn.commit()


def seed_budget(conn: sqlite3.Connection, today: date) -> None:
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
