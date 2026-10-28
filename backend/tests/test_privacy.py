"""Privacy guarantees from PLAN.md §3 and docs/SECURITY.md.

- No network by default: starting the app and using it makes no outbound
  connections. Only loopback (localhost) is allowed.
- The server only listens on localhost.
- Data lives in the app data folder, never inside the repo.
"""

import socket
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from turtlemaxxxing import config
from turtlemaxxxing.app import create_app

LOOPBACK = {"127.0.0.1", "::1", "localhost"}


@pytest.fixture
def no_network(monkeypatch):
    """Fail the test if anything tries to reach a non-loopback address."""
    attempts = []
    real_connect = socket.socket.connect
    real_getaddrinfo = socket.getaddrinfo

    def guarded_connect(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if host not in LOOPBACK:
            attempts.append(("connect", host))
            raise OSError(f"blocked outbound connection to {host}")
        return real_connect(self, address)

    def guarded_getaddrinfo(host, *args, **kwargs):
        if host not in LOOPBACK and host is not None:
            attempts.append(("dns", host))
            raise OSError(f"blocked DNS lookup for {host}")
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
    return attempts


def test_using_the_app_makes_no_outbound_connections(tmp_path, no_network):
    app = create_app(tmp_path / "net.db", clock=lambda: date(2026, 11, 20))
    with TestClient(app, base_url="http://localhost") as client:
        account = client.post("/api/accounts", json={"name": "Checking", "opening_date": "2026-11-01"}).json()
        client.post("/api/rules", json={
            "kind": "income", "name": "Pay", "amount_cents": 1000, "account_id": account["id"],
            "frequency": "weekly", "start_date": "2026-11-01",
        })
        for path in ("/api/health", "/api/accounts", "/api/rules", "/api/cashflow",
                     "/api/calendar", "/api/reviews"):
            assert client.get(path).status_code == 200
    assert no_network == []


def test_server_listens_on_localhost_only():
    assert config.HOST == "127.0.0.1"


def test_default_data_folder_is_outside_the_repo(monkeypatch, tmp_path):
    monkeypatch.delenv("TURTLE_DATA_DIR", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "share"))
    repo = Path(__file__).resolve().parents[2]
    assert repo not in config.data_dir().resolve().parents
