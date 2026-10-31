"""CSV import: match bank or card transactions to what the budget expected.

The user downloads a CSV from their bank's website themselves and drops it
in. TurtleMaxxxing never logs in anywhere. The file is read in memory and
never stored; only the resulting ledger entries are.

Two steps, both computed by plan():
1. Preview: every row gets an action.
     match         same amount as an expected entry within a few days -> confirm it
                   (if it was already marked paid by hand, it's linked, not added again)
     match_changed close amount (e.g. electric came in higher) -> confirm it at the real amount
     new           nothing expected it (groceries, a one-off) -> add as a confirmed entry
     duplicate     already imported from an earlier file -> skip
     before_start  on or before the account's "balance as of" date, so already counted -> skip
     error         couldn't read the date or amount -> skip
2. Apply: the same plan is recomputed from the same file (the browser never
   tells us which entry to change) and applied, minus any rows the user unticked.

Re-importing the same file, or an overlapping one, is safe: each bank row
gets an import_key, and a row whose key is already in the ledger is a duplicate.
"""

import csv
import hashlib
import io
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from . import ledger

MAX_ROWS = 5000
# Banks often post a payment a few days before or after its due date.
DATE_WINDOW_DAYS = 4
# "Close" means within 25% of the expected amount, e.g. a utility bill.
CLOSE_AMOUNT = Decimal("0.25")

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%Y/%m/%d", "%d-%b-%Y", "%b %d, %Y")

# Header names banks commonly use, most specific first. Matched case-insensitively.
_HEADERS = {
    "date": ("transaction date", "trans. date", "trans date", "date", "posted date", "posting date", "post date"),
    "description": ("description", "payee", "merchant", "name", "details", "transaction", "memo"),
    "amount": ("amount", "transaction amount", "amount (usd)"),
    "debit": ("debit", "withdrawal", "withdrawals", "money out", "paid out"),
    "credit": ("credit", "deposit", "deposits", "money in", "paid in"),
}


@dataclass
class Mapping:
    """Which column holds what. None means "guess from the headers";
    an empty string means "this file has no such column"."""

    date_col: str | None = None
    description_col: str | None = None
    amount_col: str | None = None
    debit_col: str | None = None
    credit_col: str | None = None
    date_format: str = "auto"
    # Card statements often show purchases as positive numbers. Flip them.
    flip_sign: bool = False


@dataclass
class Row:
    row: int
    raw: dict
    date: date | None = None
    description: str = ""
    amount_cents: int | None = None
    import_key: str | None = None
    action: str = "new"
    message: str | None = None
    match: dict | None = None


@dataclass
class Plan:
    headers: list[str]
    mapping: Mapping
    rows: list[Row] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.rows:
            out[r.action] = out.get(r.action, 0) + 1
        return out


class CsvError(ValueError):
    """The file can't be imported at all (no header, no date or amount column)."""


# ---------------------------------------------------------------- reading


def read_table(text: str) -> tuple[list[str], list[dict]]:
    text = text.lstrip("﻿")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    lines = [r for r in csv.reader(io.StringIO(text), dialect) if any(c.strip() for c in r)]
    if not lines:
        raise CsvError("the file is empty")
    # Some banks put a few lines of account info above the real header row.
    header_index = next(
        (i for i, r in enumerate(lines[:15]) if _find(r, "date") is not None and len(r) >= 2), 0
    )
    headers = [h.strip() for h in lines[header_index]]
    rows = [dict(zip(headers, (c.strip() for c in r))) for r in lines[header_index + 1:]]
    if len(rows) > MAX_ROWS:
        raise CsvError(f"the file has more than {MAX_ROWS} rows; split it into smaller files")
    return headers, rows


def _find(headers: list[str], kind: str) -> str | None:
    lowered = {h.strip().lower(): h.strip() for h in headers}
    for name in _HEADERS[kind]:
        if name in lowered:
            return lowered[name]
    return None


def resolve_mapping(headers: list[str], given: Mapping) -> Mapping:
    m = Mapping(**vars(given))
    for kind in ("date", "description", "amount", "debit", "credit"):
        attr = f"{kind}_col"
        if getattr(m, attr) == "":
            setattr(m, attr, None)
        elif getattr(m, attr) is None:
            setattr(m, attr, _find(headers, kind))
        elif getattr(m, attr) not in headers:
            raise CsvError(f"there's no column called {getattr(m, attr)!r}")
    if m.date_col is None:
        raise CsvError("couldn't find a date column; pick it by hand")
    if m.amount_col is None and m.debit_col is None and m.credit_col is None:
        raise CsvError("couldn't find an amount column; pick it by hand")
    if m.amount_col is not None:
        m.debit_col = m.credit_col = None
    return m


def parse_amount(text: str) -> int | None:
    """'$1,234.56', '-12.00', '(12.00)', '12.00-' and '12.00 DR' -> cents. Blank -> None."""
    s = text.strip().upper()
    if not s:
        return None
    negative = s.startswith("(") and s.endswith(")") or s.endswith("-") or s.endswith(" DR")
    s = re.sub(r"[^\d.\-]", "", s.removesuffix(" DR").removesuffix(" CR")).rstrip("-")
    if s.startswith("-"):
        negative, s = True, s[1:]
    try:
        cents = int((Decimal(s) * 100).quantize(Decimal(1)))
    except InvalidOperation:
        raise ValueError(f"can't read the amount {text!r}")
    return -cents if negative else cents


def detect_date_format(values: list[str]) -> str:
    """The format that reads the most values, so one junk row (a "Pending"
    line, a footer) doesn't sink the whole file; that row shows as an error.
    On a tie, US month/day wins over day/month. The preview shows which
    format was picked, and the user can change it."""
    values = [v for v in values if v]

    def reads(fmt: str, v: str) -> bool:
        try:
            datetime.strptime(v, fmt)
            return True
        except ValueError:
            return False

    scores = [(sum(reads(fmt, v) for v in values), -i, fmt) for i, fmt in enumerate(DATE_FORMATS)]
    best = max(scores)
    if best[0] == 0:
        raise CsvError("couldn't read the dates; pick the date format by hand")
    return best[2]


def import_key(when: date, cents: int, description: str, nth: int) -> str:
    """Identifies one bank row. nth counts identical rows in the same file
    (two $5 coffees on the same day are two transactions)."""
    text = f"{when.isoformat()}|{cents}|{' '.join(description.lower().split())}|{nth}"
    return hashlib.sha256(text.encode()).hexdigest()[:20]


# ---------------------------------------------------------------- matching


def _candidates(conn: sqlite3.Connection, account_id: int, start: date, end: date, today: date) -> list[dict]:
    """Movements the budget knows about on this account that no bank row has
    claimed yet: expected entries, entries marked paid by hand (so they aren't
    counted twice), and future rule dates (a bill paid a few days early)."""
    rows = conn.execute(
        "SELECT * FROM entries WHERE account_id = ? AND status IN ('expected', 'confirmed') "
        "AND import_key IS NULL AND date BETWEEN ? AND ?",
        (account_id, start.isoformat(), end.isoformat()),
    ).fetchall()
    found = [
        {"entry_id": r["id"], "rule_id": r["rule_id"], "occurrence_date": r["occurrence_date"],
         "date": r["date"], "amount_cents": r["amount_cents"], "description": r["description"],
         "confirmed": r["status"] == "confirmed"}
        for r in rows
    ]
    for e in ledger.project(conn, start, end, today):
        if e["account_id"] == account_id:
            found.append({"entry_id": None, "rule_id": e["rule_id"], "occurrence_date": e["date"],
                          "date": e["date"], "amount_cents": e["amount_cents"], "description": e["description"],
                          "confirmed": False})
    return found


def _days_apart(row: Row, cand: dict) -> int:
    return abs((row.date - date.fromisoformat(cand["date"])).days)


def _is_close(actual: int, expected: int) -> bool:
    if expected == 0 or (actual < 0) != (expected < 0):
        return False
    return abs(Decimal(actual - expected)) <= abs(Decimal(expected)) * CLOSE_AMOUNT


def _match(rows: list[Row], candidates: list[dict]) -> None:
    taken: set[int] = set()
    pending = [r for r in rows if r.action == "new"]

    def best(row: Row, ok) -> int | None:
        options = [
            (i, c) for i, c in enumerate(candidates)
            if i not in taken and _days_apart(row, c) <= DATE_WINDOW_DAYS and ok(row, c)
        ]
        if not options:
            return None
        return min(options, key=lambda o: (abs(row.amount_cents - o[1]["amount_cents"]), _days_apart(row, o[1])))[0]

    # Exact amounts first, so a close match never steals another row's exact one.
    for kind, ok in (
        ("match", lambda r, c: r.amount_cents == c["amount_cents"]),
        ("match_changed", lambda r, c: c["rule_id"] is not None and _is_close(r.amount_cents, c["amount_cents"])),
    ):
        for row in pending:
            if row.action != "new":
                continue
            i = best(row, ok)
            if i is not None:
                taken.add(i)
                row.action, row.match = kind, candidates[i]
                if row.match["confirmed"]:
                    row.message = "already marked paid; links it to this bank row"


# ---------------------------------------------------------------- plan and apply


def plan(conn: sqlite3.Connection, account_id: int, text: str, given: Mapping, today: date) -> Plan:
    account = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if account is None:
        raise LookupError(f"account {account_id} not found")
    headers, raw_rows = read_table(text)
    mapping = resolve_mapping(headers, given)
    if mapping.date_format == "auto":
        mapping.date_format = detect_date_format([r.get(mapping.date_col, "") for r in raw_rows])
    result = Plan(headers=headers, mapping=mapping)

    seen: dict[tuple, int] = {}
    existing = {
        r["import_key"] for r in conn.execute(
            "SELECT import_key FROM entries WHERE account_id = ? AND import_key IS NOT NULL", (account_id,)
        )
    }
    for n, raw in enumerate(raw_rows, start=1):
        row = Row(row=n, raw=raw, description=raw.get(mapping.description_col or "", "") or "(no description)")
        result.rows.append(row)
        try:
            row.date = datetime.strptime(raw.get(mapping.date_col, ""), mapping.date_format).date()
        except ValueError:
            row.action, row.message = "error", f"can't read the date {raw.get(mapping.date_col, '')!r}"
            continue
        try:
            if mapping.amount_col:
                cents = parse_amount(raw.get(mapping.amount_col, ""))
            else:
                debit = parse_amount(raw.get(mapping.debit_col or "", "")) or 0
                credit = parse_amount(raw.get(mapping.credit_col or "", "")) or 0
                cents = credit - abs(debit) if (debit or credit) else None
        except ValueError as err:
            row.action, row.message = "error", str(err)
            continue
        if cents is None:
            row.action, row.message = "error", "no amount"
            continue
        row.amount_cents = -cents if mapping.flip_sign else cents
        ident = (row.date, row.amount_cents, " ".join(row.description.lower().split()))
        seen[ident] = seen.get(ident, 0) + 1
        row.import_key = import_key(row.date, row.amount_cents, row.description, seen[ident])
        if row.import_key in existing:
            row.action, row.message = "duplicate", "already imported"
        elif row.date.isoformat() <= account["opening_date"]:
            row.action, row.message = "before_start", "already in the starting balance"

    dated = [r.date for r in result.rows if r.action == "new"]
    if dated:
        window = timedelta(days=DATE_WINDOW_DAYS)
        _match(result.rows, _candidates(conn, account_id, min(dated) - window, max(dated) + window, today))
    return result


def apply(conn: sqlite3.Connection, account_id: int, the_plan: Plan, skip_rows: set[int]) -> dict[str, int]:
    done = {"confirmed": 0, "added": 0, "skipped": 0}
    for row in the_plan.rows:
        if row.row in skip_rows or row.action not in ("match", "match_changed", "new"):
            done["skipped"] += 1
            continue
        m = row.match
        if m and m["entry_id"]:
            conn.execute(
                "UPDATE entries SET status = 'confirmed', date = ?, amount_cents = ?, import_key = ? WHERE id = ?",
                (row.date.isoformat(), row.amount_cents, row.import_key, m["entry_id"]),
            )
            done["confirmed"] += 1
        elif m:
            # A future rule date paid early: store it now as confirmed.
            conn.execute(
                "INSERT INTO entries (account_id, date, amount_cents, description, status, rule_id, "
                "occurrence_date, import_key) VALUES (?, ?, ?, ?, 'confirmed', ?, ?, ?)",
                (account_id, row.date.isoformat(), row.amount_cents, m["description"],
                 m["rule_id"], m["occurrence_date"], row.import_key),
            )
            done["confirmed"] += 1
        else:
            conn.execute(
                "INSERT INTO entries (account_id, date, amount_cents, description, status, import_key) "
                "VALUES (?, ?, ?, ?, 'confirmed', ?)",
                (account_id, row.date.isoformat(), row.amount_cents, row.description[:200], row.import_key),
            )
            done["added"] += 1
    conn.commit()
    return done


def plan_out(p: Plan) -> dict:
    return {
        "headers": p.headers,
        "mapping": vars(p.mapping),
        "counts": p.counts(),
        "rows": [
            {"row": r.row, "date": r.date.isoformat() if r.date else None, "description": r.description,
             "amount_cents": r.amount_cents, "action": r.action, "message": r.message,
             "match": r.match and {k: r.match[k] for k in ("description", "date", "amount_cents", "confirmed")}}
            for r in p.rows
        ],
    }
