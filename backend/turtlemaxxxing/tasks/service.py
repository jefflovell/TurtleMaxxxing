"""Task logic: reading tasks with their labels and people, privacy, Today view,
board moves and reminders.

Privacy rule (PLAN.md §3): a task or contact is Private if it's flagged
Private OR has any label marked auto-Private. is_private() is the single
place that decides this, for both. Every future AI path (M3) must filter
with it, including the people listed on a task.
"""

import sqlite3
from datetime import date, datetime, timedelta

STATUSES = ("todo", "in_progress", "blocked", "done")
LABEL_COLORS = ("red", "orange", "yellow", "green", "aqua", "blue", "violet", "magenta", "slate")

# Done tasks drop out of default views after this many days.
DONE_VISIBLE_DAYS = 7


# Which link table holds labels for what. Fixed names only, never user input.
_LABEL_LINKS = {"task": ("task_labels", "task_id"), "contact": ("contact_labels", "contact_id")}


def labels_for(conn: sqlite3.Connection, kind: str, ids: list[int]) -> dict[int, list[dict]]:
    """Labels for each task or contact id."""
    if not ids:
        return {}
    table, key = _LABEL_LINKS[kind]
    marks = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT x.{key} AS owner, l.* FROM {table} x JOIN labels l ON l.id = x.label_id "
        f"WHERE x.{key} IN ({marks}) ORDER BY l.position, l.name",
        ids,
    ).fetchall()
    out: dict[int, list[dict]] = {}
    for r in rows:
        out.setdefault(r["owner"], []).append(label_out(r))
    return out


def labels_by_task(conn: sqlite3.Connection, task_ids: list[int]) -> dict[int, list[dict]]:
    return labels_for(conn, "task", task_ids)


def contacts_by_task(conn: sqlite3.Connection, task_ids: list[int]) -> dict[int, list[dict]]:
    """The people on each task, in short form, each with its own is_private."""
    if not task_ids:
        return {}
    marks = ",".join("?" * len(task_ids))
    rows = conn.execute(
        f"SELECT tc.task_id, c.* FROM task_contacts tc JOIN contacts c ON c.id = tc.contact_id "
        f"WHERE tc.task_id IN ({marks}) ORDER BY c.name COLLATE NOCASE",
        task_ids,
    ).fetchall()
    labels = labels_for(conn, "contact", sorted({r["id"] for r in rows}))
    out: dict[int, list[dict]] = {}
    for r in rows:
        out.setdefault(r["task_id"], []).append({
            "id": r["id"], "name": r["name"], "organization": r["organization"],
            "role": r["role"], "location": r["location"],
            "is_private": is_private(r, labels.get(r["id"], [])),
        })
    return out


def reminders_by_task(conn: sqlite3.Connection, task_ids: list[int]) -> dict[int, list[dict]]:
    if not task_ids:
        return {}
    marks = ",".join("?" * len(task_ids))
    rows = conn.execute(
        f"SELECT * FROM task_reminders WHERE task_id IN ({marks}) ORDER BY remind_at", task_ids
    ).fetchall()
    out: dict[int, list[dict]] = {}
    for r in rows:
        out.setdefault(r["task_id"], []).append(
            {"id": r["id"], "remind_at": r["remind_at"], "dismissed": r["dismissed_at"] is not None}
        )
    return out


def label_out(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "color": row["color"],
        "emoji": row["emoji"],
        "favorite": bool(row["favorite"]),
        "auto_private": bool(row["auto_private"]),
        "position": row["position"],
    }


def is_private(item: sqlite3.Row | dict, labels: list[dict]) -> bool:
    """The one rule for privacy, for tasks and contacts alike. Never bypass it."""
    return bool(item["private"]) or any(label["auto_private"] for label in labels)


def tasks_out(conn: sqlite3.Connection, rows: list[sqlite3.Row]) -> list[dict]:
    ids = [r["id"] for r in rows]
    labels = labels_by_task(conn, ids)
    reminders = reminders_by_task(conn, ids)
    people = contacts_by_task(conn, ids)
    out = []
    for r in rows:
        task_labels = labels.get(r["id"], [])
        item = dict(r)
        item["private"] = bool(r["private"])
        item["labels"] = task_labels
        item["reminders"] = reminders.get(r["id"], [])
        item["contacts"] = people.get(r["id"], [])
        item["is_private"] = is_private(r, task_labels)
        out.append(item)
    return out


def get_task(conn: sqlite3.Connection, task_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return tasks_out(conn, [row])[0] if row else None


def search(
    conn: sqlite3.Connection,
    today: date,
    *,
    statuses: list[str] | None = None,
    label_ids: list[int] | None = None,
    list_id: int | None = None,
    inbox: bool = False,
    query: str | None = None,
    include_old_done: bool = False,
    due_from: date | None = None,
    due_to: date | None = None,
) -> list[dict]:
    """Filtered tasks. Labels match ANY of the given ones.

    A due-date range (the calendar) includes done tasks of any age, so a
    past month still shows what got finished."""
    where, args = [], []
    if statuses:
        where.append(f"t.status IN ({','.join('?' * len(statuses))})")
        args += statuses
    if label_ids:
        where.append(
            f"t.id IN (SELECT task_id FROM task_labels WHERE label_id IN ({','.join('?' * len(label_ids))}))"
        )
        args += label_ids
    if inbox:
        where.append("t.list_id IS NULL")
    elif list_id is not None:
        where.append("t.list_id = ?")
        args.append(list_id)
    if query:
        # Also finds tasks by the people on them: "Anderson" or "Smith Agency".
        where.append(
            "(t.title LIKE ? OR t.notes LIKE ? OR t.id IN (SELECT tc.task_id FROM task_contacts tc "
            "JOIN contacts c ON c.id = tc.contact_id WHERE c.name LIKE ? OR c.organization LIKE ?))"
        )
        args += [f"%{query}%"] * 4
    if due_from is not None:
        where.append("t.due_date >= ?")
        args.append(due_from.isoformat())
    if due_to is not None:
        where.append("t.due_date <= ?")
        args.append(due_to.isoformat())
    if not include_old_done and due_from is None and due_to is None:
        cutoff = (today - timedelta(days=DONE_VISIBLE_DAYS)).isoformat()
        where.append("(t.status != 'done' OR substr(t.completed_at, 1, 10) >= ?)")
        args.append(cutoff)
    sql = "SELECT t.* FROM tasks t"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY t.status = 'done', t.due_date IS NULL, t.due_date, t.due_time IS NULL, t.due_time, t.position, t.id"
    return tasks_out(conn, conn.execute(sql, args).fetchall())


def today_view(conn: sqlite3.Connection, today: date) -> dict:
    """The home screen: overdue, today, the next 7 days, and how much got done today."""
    open_rows = conn.execute(
        "SELECT * FROM tasks WHERE status != 'done' AND due_date IS NOT NULL AND due_date <= ? "
        "ORDER BY due_date, due_time IS NULL, due_time, position, id",
        ((today + timedelta(days=7)).isoformat(),),
    ).fetchall()
    tasks = tasks_out(conn, open_rows)
    t = today.isoformat()
    return {
        "today": t,
        "overdue": [x for x in tasks if x["due_date"] < t],
        "due_today": [x for x in tasks if x["due_date"] == t],
        "upcoming": [x for x in tasks if x["due_date"] > t],
        "no_date_count": conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status != 'done' AND due_date IS NULL"
        ).fetchone()[0],
        "done_today_count": conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'done' AND substr(completed_at, 1, 10) = ?", (t,)
        ).fetchone()[0],
    }


def set_status(conn: sqlite3.Connection, task_id: int, status: str, now: datetime) -> None:
    current = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if current is None or current["status"] == status:
        return
    completed = now.isoformat(timespec="seconds") if status == "done" else None
    conn.execute(
        "UPDATE tasks SET status = ?, completed_at = ?, "
        "blocked_note = CASE WHEN ? = 'blocked' THEN blocked_note ELSE NULL END WHERE id = ?",
        (status, completed, status, task_id),
    )


def move(conn: sqlite3.Connection, task_id: int, status: str, before_id: int | None, now: datetime) -> None:
    """Board drag-and-drop: put the task in a column, just above before_id (or at the end)."""
    set_status(conn, task_id, status, now)
    column = conn.execute(
        "SELECT id, position FROM tasks WHERE status = ? AND id != ? ORDER BY position, id",
        (status, task_id),
    ).fetchall()
    ids = [r["id"] for r in column]
    index = ids.index(before_id) if before_id in ids else len(ids)
    ids.insert(index, task_id)
    for position, tid in enumerate(ids):
        conn.execute("UPDATE tasks SET position = ? WHERE id = ?", (position, tid))


def next_position(conn: sqlite3.Connection, status: str) -> float:
    top = conn.execute("SELECT MAX(position) FROM tasks WHERE status = ?", (status,)).fetchone()[0]
    return (top or 0) + 1


def due_reminders(conn: sqlite3.Connection, now: datetime) -> list[dict]:
    """Reminders whose time has come, for tasks that aren't done."""
    rows = conn.execute(
        "SELECT r.id, r.remind_at, r.task_id FROM task_reminders r "
        "JOIN tasks t ON t.id = r.task_id "
        "WHERE r.dismissed_at IS NULL AND r.remind_at <= ? AND t.status != 'done' "
        "ORDER BY r.remind_at",
        (now.isoformat(timespec="minutes"),),
    ).fetchall()
    task_ids = sorted({r["task_id"] for r in rows})
    task_rows = conn.execute(
        f"SELECT * FROM tasks WHERE id IN ({','.join('?' * len(task_ids))})", task_ids
    ).fetchall() if task_ids else []
    tasks = {t["id"]: t for t in tasks_out(conn, task_rows)}
    return [
        {"reminder_id": r["id"], "remind_at": r["remind_at"], "task": tasks[r["task_id"]]}
        for r in rows
    ]
