from datetime import date, datetime

from turtlemaxxxing import demo
from turtlemaxxxing.budget import ledger
from turtlemaxxxing.tasks import service


def test_demo_data_seeds_a_believable_month(conn):
    today = date(2026, 11, 20)
    demo.seed(conn, today)
    names = [r["name"] for r in conn.execute("SELECT name FROM accounts ORDER BY id")]
    assert names == ["Checking", "HSA", "401(k)", "Brokerage", "Kid A 529", "Kid B 529"]
    # Paydays Nov 2 and Nov 16 each send $127.39 to the HSA.
    hsa = conn.execute("SELECT id FROM accounts WHERE name = 'HSA'").fetchone()["id"]
    assert ledger.balance(conn, hsa, today) == 410000 + 2 * 12739
    # The demo has something waiting in the review inbox.
    assert conn.execute("SELECT COUNT(*) FROM reviews WHERE status = 'open'").fetchone()[0] >= 1


def test_demo_tasks_fill_every_part_of_the_today_view(conn):
    today = date(2026, 11, 20)
    now = datetime(2026, 11, 20, 9, 0)
    demo.seed(conn, today, now)
    view = service.today_view(conn, today)
    assert view["overdue"] and view["due_today"] and view["upcoming"]
    assert view["no_date_count"] >= 1 and view["done_today_count"] == 1
    # One task is Private through the auto-Private "private" label.
    private = [t["title"] for t in service.search(conn, today) if t["is_private"]]
    assert private == ["Prep for client meeting"]
    # A reminder is already due.
    assert [r["task"]["title"] for r in service.due_reminders(conn, now)] == ["Call the plumber about the leak"]


def test_demo_contacts_are_linked_and_one_is_private(conn):
    today = date(2026, 11, 20)
    demo.seed(conn, today, datetime(2026, 11, 20, 9, 0))
    tasks = {t["title"]: t for t in service.search(conn, today)}
    assert [p["name"] for p in tasks["Prep for client meeting"]["contacts"]] == ["Mr. Anderson"]
    people = conn.execute("SELECT * FROM contacts").fetchall()
    private = [
        p["name"] for p in people
        if service.is_private(p, service.labels_for(conn, "contact", [p["id"]]).get(p["id"], []))
    ]
    assert private == ["Jordan Lee"]


def test_demo_saved_filters_are_valid(conn):
    from turtlemaxxxing.tasks.api import FilterSpec

    demo.seed(conn, date(2026, 11, 20), datetime(2026, 11, 20, 9, 0))
    rows = conn.execute("SELECT * FROM saved_filters ORDER BY position").fetchall()
    assert [r["name"] for r in rows] == ["Fires", "Home reno board"]
    for r in rows:
        FilterSpec.model_validate_json(r["filters"])
