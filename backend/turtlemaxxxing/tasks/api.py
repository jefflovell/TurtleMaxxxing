"""HTTP API for tasks: /api/tasks, /api/today, /api/labels, /api/lists, /api/reminders."""

import re
import sqlite3
from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator

from ..deps import get_db, get_now, get_today
from . import service

router = APIRouter(prefix="/api")

Status = Literal["todo", "in_progress", "blocked", "done"]
Color = Literal["red", "orange", "yellow", "green", "aqua", "blue", "violet", "magenta", "slate"]

_TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_REMIND = re.compile(r"^\d{4}-\d{2}-\d{2}T([01]\d|2[0-3]):[0-5]\d$")


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{what} not found")


def _check_reminder(value: str) -> str:
    if not _REMIND.match(value):
        raise ValueError("reminders look like 2026-11-20T09:00")
    datetime.fromisoformat(value)  # rejects impossible dates like Feb 30
    return value


# ---------------------------------------------------------------- labels


class LabelIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    color: Color = "slate"
    emoji: str | None = Field(default=None, max_length=8)
    favorite: bool = False
    auto_private: bool = False


class LabelPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=40)
    color: Color | None = None
    emoji: str | None = Field(default=None, max_length=8)
    favorite: bool | None = None
    auto_private: bool | None = None


def _label(conn: sqlite3.Connection, label_id: int) -> dict:
    row = conn.execute("SELECT * FROM labels WHERE id = ?", (label_id,)).fetchone()
    if row is None:
        raise _not_found("label")
    return service.label_out(row)


@router.get("/labels")
def list_labels(conn=Depends(get_db)):
    """Favorites first, then the rest, each in the user's order."""
    rows = conn.execute("SELECT * FROM labels ORDER BY favorite DESC, position, name").fetchall()
    return [service.label_out(r) for r in rows]


@router.post("/labels", status_code=201)
def create_label(body: LabelIn, conn=Depends(get_db)):
    name = body.name.strip().lower()
    if conn.execute("SELECT 1 FROM labels WHERE name = ?", (name,)).fetchone():
        raise HTTPException(status_code=409, detail=f"there's already a label called {name!r}")
    top = conn.execute("SELECT COALESCE(MAX(position), 0) FROM labels").fetchone()[0]
    cur = conn.execute(
        "INSERT INTO labels (name, color, emoji, favorite, auto_private, position) VALUES (?, ?, ?, ?, ?, ?)",
        (name, body.color, body.emoji, int(body.favorite), int(body.auto_private), top + 1),
    )
    conn.commit()
    return _label(conn, cur.lastrowid)


@router.patch("/labels/{label_id}")
def update_label(label_id: int, body: LabelPatch, conn=Depends(get_db)):
    _label(conn, label_id)
    changes = body.model_dump(exclude_unset=True)
    if "name" in changes:
        changes["name"] = changes["name"].strip().lower()
        clash = conn.execute(
            "SELECT 1 FROM labels WHERE name = ? AND id != ?", (changes["name"], label_id)
        ).fetchone()
        if clash:
            raise HTTPException(status_code=409, detail=f"there's already a label called {changes['name']!r}")
    for field, value in changes.items():
        if isinstance(value, bool):
            value = int(value)
        conn.execute(f"UPDATE labels SET {field} = ? WHERE id = ?", (value, label_id))
    conn.commit()
    return _label(conn, label_id)


@router.delete("/labels/{label_id}", status_code=204)
def delete_label(label_id: int, conn=Depends(get_db)):
    """Removes the label from every task. The tasks themselves stay."""
    conn.execute("DELETE FROM labels WHERE id = ?", (label_id,))
    conn.commit()


# ---------------------------------------------------------------- lists


class ListIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    emoji: str | None = Field(default=None, max_length=8)


class ListPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    emoji: str | None = Field(default=None, max_length=8)
    archived: bool | None = None


@router.get("/lists")
def list_lists(conn=Depends(get_db)):
    rows = conn.execute(
        "SELECT l.*, (SELECT COUNT(*) FROM tasks t WHERE t.list_id = l.id AND t.status != 'done') AS open_count "
        "FROM lists l ORDER BY l.archived, l.position, l.name"
    ).fetchall()
    inbox = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE list_id IS NULL AND status != 'done'"
    ).fetchone()[0]
    return {
        "inbox_open_count": inbox,
        "lists": [{**dict(r), "archived": bool(r["archived"])} for r in rows],
    }


@router.post("/lists", status_code=201)
def create_list(body: ListIn, conn=Depends(get_db)):
    top = conn.execute("SELECT COALESCE(MAX(position), 0) FROM lists").fetchone()[0]
    cur = conn.execute(
        "INSERT INTO lists (name, emoji, position) VALUES (?, ?, ?)", (body.name.strip(), body.emoji, top + 1)
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM lists WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.patch("/lists/{list_id}")
def update_list(list_id: int, body: ListPatch, conn=Depends(get_db)):
    if conn.execute("SELECT 1 FROM lists WHERE id = ?", (list_id,)).fetchone() is None:
        raise _not_found("list")
    for field, value in body.model_dump(exclude_unset=True).items():
        if isinstance(value, bool):
            value = int(value)
        conn.execute(f"UPDATE lists SET {field} = ? WHERE id = ?", (value, list_id))
    conn.commit()
    return dict(conn.execute("SELECT * FROM lists WHERE id = ?", (list_id,)).fetchone())


# ---------------------------------------------------------------- saved filters


class FilterSpec(BaseModel):
    """What the Tasks page shows. Mirrors the toolbar: list, statuses, labels, search, view."""

    scope: Literal["all", "inbox"] | int = "all"
    statuses: list[Status] = []
    label_ids: list[int] = []
    q: str = Field(default="", max_length=100)
    view: Literal["list", "board"] = "list"


class SavedFilterIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    emoji: str | None = Field(default=None, max_length=8)
    filters: FilterSpec = FilterSpec()


class SavedFilterPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=40)
    emoji: str | None = Field(default=None, max_length=8)
    filters: FilterSpec | None = None
    position: float | None = None


def _filter_out(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    """Labels deleted since the filter was saved are dropped, so a saved
    filter never points at something that no longer exists."""
    spec = FilterSpec.model_validate_json(row["filters"])
    label_ids = {r["id"] for r in conn.execute("SELECT id FROM labels")}
    spec.label_ids = [i for i in spec.label_ids if i in label_ids]
    if isinstance(spec.scope, int) and conn.execute(
        "SELECT 1 FROM lists WHERE id = ?", (spec.scope,)
    ).fetchone() is None:
        spec.scope = "all"
    return {"id": row["id"], "name": row["name"], "emoji": row["emoji"],
            "position": row["position"], "filters": spec.model_dump()}


def _saved_filter(conn: sqlite3.Connection, filter_id: int) -> dict:
    row = conn.execute("SELECT * FROM saved_filters WHERE id = ?", (filter_id,)).fetchone()
    if row is None:
        raise _not_found("saved filter")
    return _filter_out(conn, row)


@router.get("/filters")
def list_filters(conn=Depends(get_db)):
    rows = conn.execute("SELECT * FROM saved_filters ORDER BY position, id").fetchall()
    return [_filter_out(conn, r) for r in rows]


@router.post("/filters", status_code=201)
def create_filter(body: SavedFilterIn, conn=Depends(get_db)):
    top = conn.execute("SELECT COALESCE(MAX(position), 0) FROM saved_filters").fetchone()[0]
    cur = conn.execute(
        "INSERT INTO saved_filters (name, emoji, filters, position) VALUES (?, ?, ?, ?)",
        (body.name.strip(), body.emoji, body.filters.model_dump_json(), top + 1),
    )
    conn.commit()
    return _saved_filter(conn, cur.lastrowid)


@router.patch("/filters/{filter_id}")
def update_filter(filter_id: int, body: SavedFilterPatch, conn=Depends(get_db)):
    _saved_filter(conn, filter_id)
    for field, value in body.model_dump(exclude_unset=True, exclude_none=True).items():
        if field == "filters":
            value = body.filters.model_dump_json()
        conn.execute(f"UPDATE saved_filters SET {field} = ? WHERE id = ?", (value, filter_id))
    conn.commit()
    return _saved_filter(conn, filter_id)


@router.delete("/filters/{filter_id}", status_code=204)
def delete_filter(filter_id: int, conn=Depends(get_db)):
    conn.execute("DELETE FROM saved_filters WHERE id = ?", (filter_id,))
    conn.commit()


# ---------------------------------------------------------------- tasks


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    notes: str = Field(default="", max_length=5000)
    status: Status = "todo"
    blocked_note: str | None = Field(default=None, max_length=300)
    list_id: int | None = None
    due_date: date | None = None
    due_time: str | None = None
    private: bool = False
    label_ids: list[int] = []
    contact_ids: list[int] = []
    reminders: list[str] = []

    @field_validator("due_time")
    @classmethod
    def _time(cls, v):
        if v is not None and not _TIME.match(v):
            raise ValueError("time looks like 09:30")
        return v

    @field_validator("reminders")
    @classmethod
    def _reminders(cls, v):
        return [_check_reminder(r) for r in v]

    @model_validator(mode="after")
    def _time_needs_date(self):
        if self.due_time and not self.due_date:
            raise ValueError("a due time needs a due date")
        return self


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=5000)
    status: Status | None = None
    blocked_note: str | None = Field(default=None, max_length=300)
    list_id: int | None = None
    due_date: date | None = None
    due_time: str | None = None
    private: bool | None = None
    label_ids: list[int] | None = None
    contact_ids: list[int] | None = None
    reminders: list[str] | None = None

    @field_validator("due_time")
    @classmethod
    def _time(cls, v):
        if v is not None and not _TIME.match(v):
            raise ValueError("time looks like 09:30")
        return v

    @field_validator("reminders")
    @classmethod
    def _reminders(cls, v):
        return None if v is None else [_check_reminder(r) for r in v]


class MoveIn(BaseModel):
    status: Status
    before_id: int | None = None


def _check_refs(
    conn: sqlite3.Connection, list_id: int | None, label_ids: list[int] | None,
    contact_ids: list[int] | None = None,
) -> None:
    if list_id is not None and conn.execute("SELECT 1 FROM lists WHERE id = ?", (list_id,)).fetchone() is None:
        raise HTTPException(status_code=422, detail=f"list {list_id} does not exist")
    for label_id in label_ids or []:
        if conn.execute("SELECT 1 FROM labels WHERE id = ?", (label_id,)).fetchone() is None:
            raise HTTPException(status_code=422, detail=f"label {label_id} does not exist")
    for contact_id in contact_ids or []:
        if conn.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,)).fetchone() is None:
            raise HTTPException(status_code=422, detail=f"contact {contact_id} does not exist")


def _write_labels(conn: sqlite3.Connection, task_id: int, label_ids: list[int]) -> None:
    conn.execute("DELETE FROM task_labels WHERE task_id = ?", (task_id,))
    for label_id in dict.fromkeys(label_ids):
        conn.execute("INSERT INTO task_labels (task_id, label_id) VALUES (?, ?)", (task_id, label_id))


def _write_contacts(conn: sqlite3.Connection, task_id: int, contact_ids: list[int]) -> None:
    conn.execute("DELETE FROM task_contacts WHERE task_id = ?", (task_id,))
    for contact_id in dict.fromkeys(contact_ids):
        conn.execute("INSERT INTO task_contacts (task_id, contact_id) VALUES (?, ?)", (task_id, contact_id))


def _write_reminders(conn: sqlite3.Connection, task_id: int, reminders: list[str]) -> None:
    """Replaces the task's reminders, keeping 'dismissed' on ones that didn't change."""
    existing = {
        r["remind_at"]: r["dismissed_at"]
        for r in conn.execute("SELECT * FROM task_reminders WHERE task_id = ?", (task_id,))
    }
    conn.execute("DELETE FROM task_reminders WHERE task_id = ?", (task_id,))
    for when in dict.fromkeys(reminders):
        conn.execute(
            "INSERT INTO task_reminders (task_id, remind_at, dismissed_at) VALUES (?, ?, ?)",
            (task_id, when, existing.get(when)),
        )


@router.get("/tasks")
def list_tasks(
    status: list[Status] | None = Query(default=None),
    label_id: list[int] | None = Query(default=None),
    list_id: int | None = None,
    inbox: bool = False,
    q: str | None = Query(default=None, max_length=100),
    include_old_done: bool = False,
    due_from: date | None = None,
    due_to: date | None = None,
    conn=Depends(get_db),
    today=Depends(get_today),
):
    return service.search(
        conn, today, statuses=status, label_ids=label_id, list_id=list_id, inbox=inbox,
        query=q, include_old_done=include_old_done, due_from=due_from, due_to=due_to,
    )


@router.get("/tasks/{task_id}")
def get_task(task_id: int, conn=Depends(get_db)):
    task = service.get_task(conn, task_id)
    if task is None:
        raise _not_found("task")
    return task


@router.post("/tasks", status_code=201)
def create_task(body: TaskIn, conn=Depends(get_db), now=Depends(get_now)):
    _check_refs(conn, body.list_id, body.label_ids, body.contact_ids)
    cur = conn.execute(
        "INSERT INTO tasks (list_id, title, notes, status, blocked_note, due_date, due_time, private, "
        "position, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            body.list_id, body.title.strip(), body.notes, body.status,
            body.blocked_note if body.status == "blocked" else None,
            body.due_date.isoformat() if body.due_date else None, body.due_time,
            int(body.private), service.next_position(conn, body.status),
            now.isoformat(timespec="seconds") if body.status == "done" else None,
        ),
    )
    _write_labels(conn, cur.lastrowid, body.label_ids)
    _write_contacts(conn, cur.lastrowid, body.contact_ids)
    _write_reminders(conn, cur.lastrowid, body.reminders)
    conn.commit()
    return service.get_task(conn, cur.lastrowid)


@router.patch("/tasks/{task_id}")
def update_task(task_id: int, body: TaskPatch, conn=Depends(get_db), now=Depends(get_now)):
    task = service.get_task(conn, task_id)
    if task is None:
        raise _not_found("task")
    changes = body.model_dump(exclude_unset=True)
    _check_refs(conn, changes.get("list_id"), changes.get("label_ids"), changes.get("contact_ids"))

    due_date = changes.get("due_date", task["due_date"])
    due_time = changes.get("due_time", task["due_time"])
    if due_time and not due_date:
        raise HTTPException(status_code=422, detail="a due time needs a due date")

    if "label_ids" in changes:
        _write_labels(conn, task_id, changes.pop("label_ids"))
    if "contact_ids" in changes:
        _write_contacts(conn, task_id, changes.pop("contact_ids") or [])
    if "reminders" in changes:
        _write_reminders(conn, task_id, changes.pop("reminders"))
    if "status" in changes:
        service.set_status(conn, task_id, changes.pop("status"), now)
    for field, value in changes.items():
        if isinstance(value, date):
            value = value.isoformat()
        elif isinstance(value, bool):
            value = int(value)
        conn.execute(f"UPDATE tasks SET {field} = ? WHERE id = ?", (value, task_id))
    conn.execute("UPDATE tasks SET updated_at = ? WHERE id = ?", (now.isoformat(timespec="seconds"), task_id))
    conn.commit()
    return service.get_task(conn, task_id)


@router.post("/tasks/{task_id}/move")
def move_task(task_id: int, body: MoveIn, conn=Depends(get_db), now=Depends(get_now)):
    if service.get_task(conn, task_id) is None:
        raise _not_found("task")
    service.move(conn, task_id, body.status, body.before_id, now)
    conn.commit()
    return service.get_task(conn, task_id)


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, conn=Depends(get_db)):
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()


@router.get("/today")
def get_today_view(conn=Depends(get_db), today=Depends(get_today)):
    return service.today_view(conn, today)


# ---------------------------------------------------------------- reminders


class SnoozeIn(BaseModel):
    minutes: int = Field(ge=1, le=7 * 24 * 60)


@router.get("/reminders/due")
def due_reminders(conn=Depends(get_db), now=Depends(get_now)):
    return service.due_reminders(conn, now)


@router.post("/reminders/{reminder_id}/dismiss")
def dismiss_reminder(reminder_id: int, conn=Depends(get_db), now=Depends(get_now)):
    cur = conn.execute(
        "UPDATE task_reminders SET dismissed_at = ? WHERE id = ?",
        (now.isoformat(timespec="seconds"), reminder_id),
    )
    if cur.rowcount == 0:
        raise _not_found("reminder")
    conn.commit()
    return {"ok": True}


@router.post("/reminders/{reminder_id}/snooze")
def snooze_reminder(reminder_id: int, body: SnoozeIn, conn=Depends(get_db), now=Depends(get_now)):
    later = (now + timedelta(minutes=body.minutes)).isoformat(timespec="minutes")
    cur = conn.execute(
        "UPDATE task_reminders SET remind_at = ?, dismissed_at = NULL WHERE id = ?", (later, reminder_id)
    )
    if cur.rowcount == 0:
        raise _not_found("reminder")
    conn.commit()
    return {"ok": True, "remind_at": later}
