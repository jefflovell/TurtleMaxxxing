"""docs/BACKLOG.md stays well-formed: unique IDs, known values, a details
section per item, and requesters listed by alias only (the repo is public).

Allowed categories, milestones and aliases are read from BACKLOG.md itself,
so changing the rules there is enough.
"""

import re
from datetime import date
from pathlib import Path

import pytest

BACKLOG = Path(__file__).resolve().parents[2] / "docs" / "BACKLOG.md"

PRIORITIES = {"P0", "P1", "P2", "P3"}
OPEN_STATUSES = {"new", "triaged", "planned", "in-progress", "ready-to-verify"}
CLOSED_STATUSES = {"verified", "wont-do", "duplicate"}
COMPLEXITY = {"XS", "S", "M", "L", "XL"}
ID = re.compile(r"^QA-\d{3}$")


def _section(text: str, heading: str) -> str:
    match = re.search(rf"^{re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    assert match, f"BACKLOG.md is missing the {heading!r} section"
    return match.group(1)


def _rows(block: str) -> list[list[str]]:
    rows = []
    for line in block.splitlines():
        if line.startswith("|") and not line.startswith("|---"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows[1:]  # skip the header row


@pytest.fixture(scope="module")
def backlog():
    text = BACKLOG.read_text(encoding="utf-8")
    rules = _section(text, "## How items are filled in")
    categories = set(re.findall(r"`([a-z]+)`", _section(rules, "### Categories")))
    milestones = {r[1] for r in _rows(_section(rules, "### Milestone map (what built which feature)"))}
    return {
        "text": text,
        "open": _rows(_section(text, "## Open")),
        "closed": _rows(_section(text, "## Closed")),
        "details": re.findall(r"^### (QA-\d{3}) ", text, re.M),
        "aliases": {r[0].strip("`") for r in _rows(_section(text, "## Requesters"))},
        "categories": categories,
        "milestones": milestones | {"new"},
    }


def test_rules_were_found(backlog):
    assert {"bug", "ux", "ui", "extension", "storage", "auth"} <= backlog["categories"]
    assert {"M1", "M2a", "M2b"} <= backlog["milestones"]
    assert {"maintainer", "first-user", "qa-agent"} <= backlog["aliases"]


def test_ids_are_unique_and_have_details(backlog):
    ids = [r[0] for r in backlog["open"] + backlog["closed"]]
    assert all(ID.match(i) for i in ids), ids
    assert len(ids) == len(set(ids)), "an ID is used twice"
    assert sorted(ids) == sorted(backlog["details"]), "every item needs exactly one ### Details section"


def test_open_items_use_known_values(backlog):
    for row in backlog["open"]:
        assert len(row) == 9, row
        item, _title, categories, priority, status, complexity, milestone, requested, requester = row
        assert set(c.strip() for c in categories.split(",")) <= backlog["categories"], item
        assert priority in PRIORITIES, item
        assert status in OPEN_STATUSES, f"{item}: {status} (closed items go in the Closed table)"
        assert complexity in COMPLEXITY, item
        assert milestone in backlog["milestones"], item
        date.fromisoformat(requested)
        assert requester in backlog["aliases"], f"{item}: requester must be an alias from the Requesters table"


def test_closed_items_use_known_values(backlog):
    for row in backlog["closed"]:
        assert len(row) == 6, row
        item, _title, status, requested, closed, _fixed = row
        assert status in CLOSED_STATUSES, item
        assert date.fromisoformat(closed) >= date.fromisoformat(requested), item
