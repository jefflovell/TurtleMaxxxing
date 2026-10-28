from datetime import date, datetime, time

import pytest
from fastapi.testclient import TestClient

from turtlemaxxxing import db
from turtlemaxxxing.app import create_app


class Clock:
    """A "today" (and time of day) that tests can move forward."""

    def __init__(self, today: date):
        self.today = today
        self.time = time(9, 0)

    def __call__(self) -> date:
        return self.today

    def now(self) -> datetime:
        return datetime.combine(self.today, self.time)


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    # Never touch the real app data folder from tests.
    monkeypatch.setenv("TURTLE_DATA_DIR", str(tmp_path / "data"))
    return tmp_path / "data"


@pytest.fixture
def clock():
    return Clock(date(2026, 11, 1))


@pytest.fixture
def client(tmp_path, clock):
    app = create_app(tmp_path / "test.db", clock=clock, now=clock.now)
    # The app only answers to its own names (see security.py), so talk to it as localhost.
    with TestClient(app, base_url="http://localhost") as c:
        yield c


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(tmp_path / "unit.db")
    db.migrate(connection)
    yield connection
    connection.close()
