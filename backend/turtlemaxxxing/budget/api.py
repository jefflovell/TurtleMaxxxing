"""HTTP API for the budget: /api/accounts, /api/rules, /api/entries,
/api/cashflow, /api/calendar and /api/reviews.

All money is integer cents. The frontend converts to and from dollars.
"""

import datetime as dt
import sqlite3
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from ..deps import get_db, get_today
from . import ledger, reviews
from .schedule import FREQUENCIES

router = APIRouter(prefix="/api")

AccountKind = Literal[
    "checking", "savings", "credit", "hsa", "retirement", "brokerage", "education", "goal", "other"
]
RuleKind = Literal["income", "bill", "subscription"]
Frequency = Literal[FREQUENCIES]  # type: ignore[valid-type]


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{what} not found")


# ---------------------------------------------------------------- accounts


class AccountIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: AccountKind = "checking"
    opening_balance_cents: int = 0
    opening_date: date | None = None
    checkin_every_days: int | None = Field(default=None, ge=1, le=366)


class AccountPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    kind: AccountKind | None = None
    checkin_every_days: int | None = Field(default=None, ge=1, le=366)
    archived: bool | None = None


def _account_out(conn: sqlite3.Connection, row: sqlite3.Row, today: date) -> dict:
    out = dict(row)
    out["archived"] = bool(row["archived"])
    out["balance_cents"] = ledger.balance(conn, row["id"], today)
    return out


@router.get("/accounts")
def list_accounts(conn=Depends(get_db), today=Depends(get_today)):
    rows = conn.execute("SELECT * FROM accounts ORDER BY archived, id").fetchall()
    return [_account_out(conn, r, today) for r in rows]


@router.post("/accounts", status_code=201)
def create_account(body: AccountIn, conn=Depends(get_db), today=Depends(get_today)):
    cur = conn.execute(
        "INSERT INTO accounts (name, kind, opening_balance_cents, opening_date, checkin_every_days) "
        "VALUES (?, ?, ?, ?, ?)",
        (body.name, body.kind, body.opening_balance_cents,
         (body.opening_date or today).isoformat(), body.checkin_every_days),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _account_out(conn, row, today)


@router.patch("/accounts/{account_id}")
def update_account(account_id: int, body: AccountPatch, conn=Depends(get_db), today=Depends(get_today)):
    if conn.execute("SELECT 1 FROM accounts WHERE id = ?", (account_id,)).fetchone() is None:
        raise _not_found("account")
    for field, value in body.model_dump(exclude_unset=True).items():
        conn.execute(f"UPDATE accounts SET {field} = ? WHERE id = ?", (value, account_id))
    conn.commit()
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    return _account_out(conn, row, today)


@router.post("/accounts/{account_id}/checkin", status_code=201)
def start_checkin(account_id: int, conn=Depends(get_db), today=Depends(get_today)):
    """"Check balance now": opens a balance check-in in the review inbox."""
    try:
        return {"review_id": reviews.open_checkin(conn, account_id, today)}
    except LookupError:
        raise _not_found("account")


# ---------------------------------------------------------------- rules


class SplitIn(BaseModel):
    account_id: int
    amount_cents: int = Field(gt=0)
    label: str | None = Field(default=None, max_length=100)


class RuleIn(BaseModel):
    kind: RuleKind
    name: str = Field(min_length=1, max_length=100)
    amount_cents: int = Field(ge=0)
    account_id: int
    frequency: Frequency
    start_date: date
    end_date: date | None = None
    second_day: int | None = Field(default=None, ge=1, le=31)
    review_every_months: int | None = Field(default=None, ge=1, le=24)
    splits: list[SplitIn] = []

    @model_validator(mode="after")
    def _check(self):
        if self.splits and self.kind != "income":
            raise ValueError("only income can be split")
        if sum(s.amount_cents for s in self.splits) > self.amount_cents:
            raise ValueError("splits add up to more than the amount")
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end date is before start date")
        return self


class RulePatch(BaseModel):
    """Edits apply from today on. Entries already posted keep their old values."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    amount_cents: int | None = Field(default=None, ge=0)
    end_date: date | None = None
    review_every_months: int | None = Field(default=None, ge=1, le=24)
    splits: list[SplitIn] | None = None


def _rule_out(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    out = dict(row)
    out["splits"] = [dict(s) for s in ledger.splits_for(conn, row["id"])]
    return out


def _check_accounts(conn: sqlite3.Connection, ids: list[int]) -> None:
    for account_id in ids:
        if conn.execute("SELECT 1 FROM accounts WHERE id = ?", (account_id,)).fetchone() is None:
            raise HTTPException(status_code=422, detail=f"account {account_id} does not exist")


def _write_splits(conn: sqlite3.Connection, rule_id: int, splits: list[SplitIn]) -> None:
    conn.execute("DELETE FROM rule_splits WHERE rule_id = ?", (rule_id,))
    for s in splits:
        conn.execute(
            "INSERT INTO rule_splits (rule_id, account_id, amount_cents, label) VALUES (?, ?, ?, ?)",
            (rule_id, s.account_id, s.amount_cents, s.label),
        )


@router.get("/rules")
def list_rules(conn=Depends(get_db)):
    rows = conn.execute("SELECT * FROM rules ORDER BY kind, name").fetchall()
    return [_rule_out(conn, r) for r in rows]


@router.post("/rules", status_code=201)
def create_rule(body: RuleIn, conn=Depends(get_db), today=Depends(get_today)):
    _check_accounts(conn, [body.account_id] + [s.account_id for s in body.splits])
    cur = conn.execute(
        "INSERT INTO rules (kind, name, amount_cents, account_id, frequency, start_date, end_date, "
        "second_day, review_every_months) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (body.kind, body.name, body.amount_cents, body.account_id, body.frequency,
         body.start_date.isoformat(), body.end_date.isoformat() if body.end_date else None,
         body.second_day, body.review_every_months),
    )
    _write_splits(conn, cur.lastrowid, body.splits)
    conn.commit()
    # Catch up: a rule that started in the past gets its expected entries now.
    ledger.post_due(conn, today)
    reviews.generate(conn, today)
    return _rule_out(conn, conn.execute("SELECT * FROM rules WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.patch("/rules/{rule_id}")
def update_rule(rule_id: int, body: RulePatch, conn=Depends(get_db)):
    rule = conn.execute("SELECT * FROM rules WHERE id = ?", (rule_id,)).fetchone()
    if rule is None:
        raise _not_found("rule")
    changes = body.model_dump(exclude_unset=True)
    splits = changes.pop("splits", None)
    amount = changes.get("amount_cents", rule["amount_cents"])
    if splits is not None:
        if rule["kind"] != "income" and splits:
            raise HTTPException(status_code=422, detail="only income can be split")
        if sum(s["amount_cents"] for s in splits) > amount:
            raise HTTPException(status_code=422, detail="splits add up to more than the amount")
        _check_accounts(conn, [s["account_id"] for s in splits])
        _write_splits(conn, rule_id, [SplitIn(**s) for s in splits])
    elif "amount_cents" in changes:
        current = sum(s["amount_cents"] for s in ledger.splits_for(conn, rule_id))
        if current > amount:
            raise HTTPException(status_code=422, detail="splits add up to more than the amount")
    for field, value in changes.items():
        if isinstance(value, date):
            value = value.isoformat()
        conn.execute(f"UPDATE rules SET {field} = ? WHERE id = ?", (value, rule_id))
    conn.commit()
    return _rule_out(conn, conn.execute("SELECT * FROM rules WHERE id = ?", (rule_id,)).fetchone())


@router.post("/rules/{rule_id}/occurrences/{when}/confirm")
def confirm_occurrence(rule_id: int, when: date, conn=Depends(get_db)):
    try:
        ledger.confirm_occurrence(conn, rule_id, when)
    except LookupError:
        raise _not_found("rule")
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))
    return {"ok": True}


# ---------------------------------------------------------------- entries


# Fields named `date` use dt.date, so the field name can't shadow the type.
class EntryIn(BaseModel):
    account_id: int
    date: dt.date
    amount_cents: int
    description: str = Field(min_length=1, max_length=200)


class EntryPatch(BaseModel):
    status: Literal["expected", "confirmed"] | None = None
    amount_cents: int | None = None
    date: dt.date | None = None
    description: str | None = Field(default=None, min_length=1, max_length=200)


@router.get("/entries")
def list_entries(
    start: date, end: date, account_id: int | None = None, conn=Depends(get_db)
):
    events = ledger.stored_events(conn, start, end)
    if account_id is not None:
        events = [e for e in events if e["account_id"] == account_id]
    return events


@router.post("/entries", status_code=201)
def create_entry(body: EntryIn, conn=Depends(get_db)):
    """A one-off movement that isn't part of any rule."""
    _check_accounts(conn, [body.account_id])
    cur = conn.execute(
        "INSERT INTO entries (account_id, date, amount_cents, description, status) "
        "VALUES (?, ?, ?, ?, 'confirmed')",
        (body.account_id, body.date.isoformat(), body.amount_cents, body.description),
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM entries WHERE id = ?", (cur.lastrowid,)).fetchone())


@router.patch("/entries/{entry_id}")
def update_entry(entry_id: int, body: EntryPatch, conn=Depends(get_db)):
    if conn.execute("SELECT 1 FROM entries WHERE id = ?", (entry_id,)).fetchone() is None:
        raise _not_found("entry")
    for field, value in body.model_dump(exclude_unset=True).items():
        if isinstance(value, date):
            value = value.isoformat()
        conn.execute(f"UPDATE entries SET {field} = ? WHERE id = ?", (value, entry_id))
    conn.commit()
    return dict(conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone())


@router.delete("/entries/{entry_id}", status_code=204)
def delete_entry(entry_id: int, conn=Depends(get_db)):
    conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()


# ---------------------------------------------------------------- views


def _parse_month(month: str | None, today: date) -> tuple[int, int]:
    if not month:
        return today.year, today.month
    try:
        year, mon = (int(p) for p in month.split("-"))
        date(year, mon, 1)
    except ValueError:
        raise HTTPException(status_code=422, detail="month must look like 2026-11")
    return year, mon


@router.get("/cashflow")
def get_cashflow(
    month: str | None = None,
    account_id: list[int] | None = None,
    conn=Depends(get_db),
    today=Depends(get_today),
):
    """Defaults to this month across all checking accounts."""
    year, mon = _parse_month(month, today)
    ids = account_id or [
        r["id"] for r in conn.execute(
            "SELECT id FROM accounts WHERE kind = 'checking' AND archived = 0"
        )
    ]
    return ledger.cashflow(conn, ids, year, mon, today)


@router.get("/calendar")
def get_calendar(month: str | None = None, conn=Depends(get_db), today=Depends(get_today)):
    """Every rule-driven movement in the month, by day: what's due and whether it's paid."""
    year, mon = _parse_month(month, today)
    first, last = ledger.month_bounds(year, mon)
    events = [e for e in ledger.events_between(conn, first, last, today) if e["rule_id"]]
    return {"month": f"{year:04d}-{mon:02d}", "today": today.isoformat(), "events": events}


# ---------------------------------------------------------------- reviews


class CheckinIn(BaseModel):
    actual_balance_cents: int


class SubscriptionIn(BaseModel):
    action: Literal["keep", "cancel", "change_price"]
    new_amount_cents: int | None = Field(default=None, ge=0)


@router.get("/reviews")
def list_reviews(status: str = "open", conn=Depends(get_db), today=Depends(get_today)):
    rows = conn.execute(
        "SELECT * FROM reviews WHERE status = ? ORDER BY due_date, id", (status,)
    ).fetchall()
    out = []
    for r in rows:
        item = dict(r)
        if r["account_id"]:
            account = conn.execute("SELECT * FROM accounts WHERE id = ?", (r["account_id"],)).fetchone()
            item["account_name"] = account["name"]
            item["expected_balance_cents"] = ledger.balance(conn, r["account_id"], today)
        if r["rule_id"]:
            rule = conn.execute("SELECT * FROM rules WHERE id = ?", (r["rule_id"],)).fetchone()
            item["rule_name"] = rule["name"]
            item["amount_cents"] = rule["amount_cents"]
            item["frequency"] = rule["frequency"]
        out.append(item)
    return out


def _review_errors(fn):
    try:
        return fn()
    except LookupError:
        raise _not_found("review")
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))


@router.post("/reviews/{review_id}/checkin")
def resolve_checkin(review_id: int, body: CheckinIn, conn=Depends(get_db), today=Depends(get_today)):
    adjustment = _review_errors(
        lambda: reviews.resolve_checkin(conn, review_id, body.actual_balance_cents, today)
    )
    return {"adjustment_cents": adjustment}


@router.post("/reviews/{review_id}/subscription")
def resolve_subscription(
    review_id: int, body: SubscriptionIn, conn=Depends(get_db), today=Depends(get_today)
):
    _review_errors(
        lambda: reviews.resolve_subscription(conn, review_id, body.action, today, body.new_amount_cents)
    )
    return {"ok": True}


@router.post("/reviews/{review_id}/dismiss")
def dismiss_review(review_id: int, conn=Depends(get_db), today=Depends(get_today)):
    _review_errors(lambda: reviews.dismiss(conn, review_id, today))
    return {"ok": True}
