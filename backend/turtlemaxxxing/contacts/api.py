"""HTTP API for contacts: /api/contacts.

Privacy uses the same rule as tasks (tasks.service.is_private): a contact is
Private if it's flagged Private or has an auto-Private label.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from ..deps import get_db, get_now
from ..tasks import service as tasks

router = APIRouter(prefix="/api")


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="contact not found")


def _check_email(value: str | None) -> str | None:
    if value and ("@" not in value or value.strip() != value or " " in value):
        raise ValueError("that doesn't look like an email address")
    return value


class ContactIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    organization: str = Field(default="", max_length=100)
    role: str = Field(default="", max_length=100)
    email: str = Field(default="", max_length=200)
    phone: str = Field(default="", max_length=40)
    location: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=2000)
    private: bool = False
    label_ids: list[int] = []

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        return _check_email(v)


class ContactPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    organization: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    location: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    private: bool | None = None
    label_ids: list[int] | None = None

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        return _check_email(v)


def contacts_out(conn: sqlite3.Connection, rows: list[sqlite3.Row]) -> list[dict]:
    ids = [r["id"] for r in rows]
    labels = tasks.labels_for(conn, "contact", ids)
    counts = {
        r["contact_id"]: r["n"] for r in conn.execute(
            f"SELECT tc.contact_id, COUNT(*) AS n FROM task_contacts tc JOIN tasks t ON t.id = tc.task_id "
            f"WHERE t.status != 'done' AND tc.contact_id IN ({','.join('?' * len(ids))}) GROUP BY tc.contact_id",
            ids,
        )
    } if ids else {}
    out = []
    for r in rows:
        item = dict(r)
        item["private"] = bool(r["private"])
        item["labels"] = labels.get(r["id"], [])
        item["is_private"] = tasks.is_private(r, item["labels"])
        item["open_task_count"] = counts.get(r["id"], 0)
        out.append(item)
    return out


def _contact(conn: sqlite3.Connection, contact_id: int) -> dict:
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    if row is None:
        raise _not_found()
    return contacts_out(conn, [row])[0]


def _check_labels(conn: sqlite3.Connection, label_ids: list[int] | None) -> None:
    for label_id in label_ids or []:
        if conn.execute("SELECT 1 FROM labels WHERE id = ?", (label_id,)).fetchone() is None:
            raise HTTPException(status_code=422, detail=f"label {label_id} does not exist")


def _write_labels(conn: sqlite3.Connection, contact_id: int, label_ids: list[int]) -> None:
    conn.execute("DELETE FROM contact_labels WHERE contact_id = ?", (contact_id,))
    for label_id in dict.fromkeys(label_ids):
        conn.execute("INSERT INTO contact_labels (contact_id, label_id) VALUES (?, ?)", (contact_id, label_id))


@router.get("/contacts")
def list_contacts(
    q: str | None = Query(default=None, max_length=100),
    label_id: list[int] | None = Query(default=None),
    conn=Depends(get_db),
):
    """Sorted by organization, then name. q matches name, organization, role or location."""
    where, args = [], []
    if q:
        where.append("(name LIKE ? OR organization LIKE ? OR role LIKE ? OR location LIKE ?)")
        args += [f"%{q}%"] * 4
    if label_id:
        where.append(
            f"id IN (SELECT contact_id FROM contact_labels WHERE label_id IN ({','.join('?' * len(label_id))}))"
        )
        args += label_id
    sql = "SELECT * FROM contacts"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY organization = '', organization COLLATE NOCASE, name COLLATE NOCASE"
    return contacts_out(conn, conn.execute(sql, args).fetchall())


@router.get("/contacts/{contact_id}")
def get_contact(contact_id: int, conn=Depends(get_db)):
    """The contact plus the tasks they're on."""
    contact = _contact(conn, contact_id)
    rows = conn.execute(
        "SELECT t.* FROM tasks t JOIN task_contacts tc ON tc.task_id = t.id WHERE tc.contact_id = ? "
        "ORDER BY t.status = 'done', t.due_date IS NULL, t.due_date, t.id",
        (contact_id,),
    ).fetchall()
    contact["tasks"] = tasks.tasks_out(conn, rows)
    return contact


@router.post("/contacts", status_code=201)
def create_contact(body: ContactIn, conn=Depends(get_db)):
    _check_labels(conn, body.label_ids)
    cur = conn.execute(
        "INSERT INTO contacts (name, organization, role, email, phone, location, notes, private) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (body.name.strip(), body.organization.strip(), body.role.strip(), body.email.strip(),
         body.phone.strip(), body.location.strip(), body.notes, int(body.private)),
    )
    _write_labels(conn, cur.lastrowid, body.label_ids)
    conn.commit()
    return _contact(conn, cur.lastrowid)


@router.patch("/contacts/{contact_id}")
def update_contact(contact_id: int, body: ContactPatch, conn=Depends(get_db), now=Depends(get_now)):
    _contact(conn, contact_id)
    changes = body.model_dump(exclude_unset=True)
    _check_labels(conn, changes.get("label_ids"))
    if "label_ids" in changes:
        _write_labels(conn, contact_id, changes.pop("label_ids") or [])
    for field, value in changes.items():
        if value is None:
            continue  # name can't be blank; other fields are cleared with ""
        if isinstance(value, bool):
            value = int(value)
        elif isinstance(value, str) and field != "notes":
            value = value.strip()
        conn.execute(f"UPDATE contacts SET {field} = ? WHERE id = ?", (value, contact_id))
    conn.execute(
        "UPDATE contacts SET updated_at = ? WHERE id = ?", (now.isoformat(timespec="seconds"), contact_id)
    )
    conn.commit()
    return _contact(conn, contact_id)


@router.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: int, conn=Depends(get_db)):
    """Removes the contact from every task. The tasks themselves stay."""
    conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()
