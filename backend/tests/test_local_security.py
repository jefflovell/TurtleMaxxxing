"""Websites open in the same browser must not be able to read or change local data.

See turtlemaxxxing/security.py for the why. These tests simulate what a
browser sends when a malicious page tries DNS rebinding or a cross-site form post.
"""

import pytest
from fastapi.testclient import TestClient

from turtlemaxxxing import config
from turtlemaxxxing.app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(tmp_path / "sec.db", settings=config.Settings(port=8765, hostname="turtle.localhost"))


def call(app, method, path, host="turtle.localhost:8765", **headers):
    client = TestClient(app, base_url=f"http://{host}")
    return client.request(method, path, headers=headers, json={} if method == "POST" else None)


@pytest.mark.parametrize("host", ["turtle.localhost:8765", "localhost:8765", "127.0.0.1:8765"])
def test_answers_to_its_own_names(app, host):
    assert call(app, "GET", "/api/health", host=host).status_code == 200


@pytest.mark.parametrize("host", ["evil.example", "evil.example:8765", "turtle.localhost.evil.example", "192.168.1.20:8765"])
def test_refuses_other_host_names_dns_rebinding(app, host):
    assert call(app, "GET", "/api/accounts", host=host).status_code == 400


def test_custom_friendly_name_is_honoured(tmp_path):
    app = create_app(tmp_path / "c.db", settings=config.Settings(port=8790, hostname="i-like-turtles.localhost"))
    assert call(app, "GET", "/api/health", host="i-like-turtles.localhost:8790").status_code == 200
    assert call(app, "GET", "/api/health", host="turtle.localhost:8790").status_code == 400


def test_same_site_changes_are_allowed(app):
    res = call(app, "POST", "/api/accounts", origin="http://turtle.localhost:8765",
               **{"sec-fetch-site": "same-origin"})
    # Reaches the API (422 = validation, because the test body is empty); not blocked.
    assert res.status_code == 422


def test_tools_without_a_browser_are_allowed(app):
    # curl, scripts and local AI agents send no Origin header.
    assert call(app, "POST", "/api/accounts").status_code == 422


@pytest.mark.parametrize("origin", ["https://evil.example", "http://turtle.localhost.evil.example", "null"])
def test_cross_site_changes_are_refused(app, origin):
    assert call(app, "POST", "/api/reviews/1/dismiss", origin=origin).status_code == 403


def test_cross_site_fetch_metadata_is_refused(app):
    res = call(app, "POST", "/api/reviews/1/dismiss", **{"sec-fetch-site": "cross-site"})
    assert res.status_code == 403


def test_no_cors_headers_so_other_sites_cannot_read(app):
    res = call(app, "GET", "/api/accounts", origin="https://evil.example")
    assert "access-control-allow-origin" not in {k.lower() for k in res.headers}
