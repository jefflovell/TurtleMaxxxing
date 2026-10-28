"""Shared FastAPI dependencies: a database connection, "today" and "now".

Each request gets its own connection. The first request of each day also
runs the daily tick: auto-post due rule entries and open due reviews.
"""

from collections.abc import Iterator
from datetime import date, datetime

from fastapi import Request

from . import db
from .budget import ledger, reviews


def get_today(request: Request) -> date:
    return request.app.state.clock()


def get_now(request: Request) -> datetime:
    """Local date and time, used for reminders and completion times."""
    return request.app.state.now()


def get_db(request: Request) -> Iterator:
    conn = db.connect(request.app.state.db_path)
    try:
        today = request.app.state.clock()
        if request.app.state.last_tick != today:
            ledger.post_due(conn, today)
            reviews.generate(conn, today)
            request.app.state.last_tick = today
        yield conn
    finally:
        conn.close()
