"""Tasks, labels, lists, Today view and reminders through the HTTP API."""

from datetime import date, time

import pytest


def labels(client):
    return {l["name"]: l for l in client.get("/api/labels").json()}


def make_task(client, title="Call the plumber", **fields):
    res = client.post("/api/tasks", json={"title": title, **fields})
    assert res.status_code == 201, res.text
    return res.json()


def titles(tasks):
    return [t["title"] for t in tasks]


# ---------------------------------------------------------------- labels


def test_starter_labels_with_favorites_first(client):
    all_labels = client.get("/api/labels").json()
    names = [l["name"] for l in all_labels]
    assert names[:4] == ["critical", "urgent", "important", "work"]
    assert all(l["favorite"] for l in all_labels[:4])
    assert labels(client)["private"]["auto_private"] is True


def test_user_defined_labels_and_favoriting(client):
    res = client.post("/api/labels", json={"name": "Wife", "color": "magenta", "emoji": "💍"})
    assert res.status_code == 201
    wife = res.json()
    assert wife["name"] == "wife" and wife["favorite"] is False
    client.patch(f"/api/labels/{wife['id']}", json={"favorite": True})
    assert labels(client)["wife"]["favorite"] is True
    # Names are unique regardless of case.
    assert client.post("/api/labels", json={"name": "WIFE"}).status_code == 409
    assert client.post("/api/labels", json={"name": "x", "color": "chartreuse"}).status_code == 422


def test_deleting_a_label_keeps_the_tasks(client):
    home = labels(client)["home"]["id"]
    task = make_task(client, label_ids=[home])
    client.delete(f"/api/labels/{home}")
    assert client.get(f"/api/tasks/{task['id']}").json()["labels"] == []


# ---------------------------------------------------------------- privacy


def test_private_flag_makes_a_task_private(client):
    assert make_task(client)["is_private"] is False
    assert make_task(client, private=True)["is_private"] is True


def test_auto_private_label_makes_tagged_tasks_private(client):
    private_label = labels(client)["private"]["id"]
    task = make_task(client, "Prep for client meeting", label_ids=[private_label])
    assert task["private"] is False
    assert task["is_private"] is True


def test_turning_on_auto_private_applies_to_existing_tasks(client):
    work = labels(client)["work"]["id"]
    task = make_task(client, "Prep slides", label_ids=[work])
    assert task["is_private"] is False
    client.patch(f"/api/labels/{work}", json={"auto_private": True})
    assert client.get(f"/api/tasks/{task['id']}").json()["is_private"] is True
    # Removing the label makes it non-private again.
    client.patch(f"/api/tasks/{task['id']}", json={"label_ids": []})
    assert client.get(f"/api/tasks/{task['id']}").json()["is_private"] is False


# ---------------------------------------------------------------- status


def test_status_lifecycle(client, clock):
    task = make_task(client, status="blocked", blocked_note="waiting on landlord")
    assert task["blocked_note"] == "waiting on landlord"

    task = client.patch(f"/api/tasks/{task['id']}", json={"status": "in_progress"}).json()
    assert task["blocked_note"] is None

    clock.time = time(14, 30)
    task = client.patch(f"/api/tasks/{task['id']}", json={"status": "done"}).json()
    assert task["completed_at"] == "2026-11-01T14:30:00"

    task = client.patch(f"/api/tasks/{task['id']}", json={"status": "todo"}).json()
    assert task["completed_at"] is None


def test_done_tasks_fade_out_after_a_week(client, clock):
    task = make_task(client)
    client.patch(f"/api/tasks/{task['id']}", json={"status": "done"})
    clock.today = date(2026, 11, 8)
    assert titles(client.get("/api/tasks").json()) == ["Call the plumber"]
    clock.today = date(2026, 11, 9)
    assert client.get("/api/tasks").json() == []
    assert len(client.get("/api/tasks", params={"include_old_done": True}).json()) == 1


# ---------------------------------------------------------------- filters


def test_filters(client):
    lab = labels(client)
    reno = client.post("/api/lists", json={"name": "Home reno", "emoji": "🔨"}).json()
    make_task(client, "Pick tile", list_id=reno["id"], label_ids=[lab["home"]["id"]])
    make_task(client, "Pay water bill", label_ids=[lab["money"]["id"], lab["urgent"]["id"]])
    make_task(client, "Renew passport", status="blocked")

    assert titles(client.get("/api/tasks", params={"status": "blocked"}).json()) == ["Renew passport"]
    assert titles(client.get("/api/tasks", params={"label_id": lab["urgent"]["id"]}).json()) == ["Pay water bill"]
    # Several labels match ANY of them.
    both = client.get("/api/tasks", params=[("label_id", lab["urgent"]["id"]), ("label_id", lab["home"]["id"])])
    assert sorted(titles(both.json())) == ["Pay water bill", "Pick tile"]
    assert titles(client.get("/api/tasks", params={"list_id": reno["id"]}).json()) == ["Pick tile"]
    assert sorted(titles(client.get("/api/tasks", params={"inbox": True}).json())) == ["Pay water bill", "Renew passport"]
    assert titles(client.get("/api/tasks", params={"q": "water"}).json()) == ["Pay water bill"]


def test_lists_count_open_tasks_and_archive(client):
    reno = client.post("/api/lists", json={"name": "Home reno"}).json()
    make_task(client, "Pick tile", list_id=reno["id"])
    make_task(client, "Inbox thing")
    data = client.get("/api/lists").json()
    assert data["inbox_open_count"] == 1
    assert data["lists"][0]["open_count"] == 1
    client.patch(f"/api/lists/{reno['id']}", json={"archived": True})
    assert client.get("/api/lists").json()["lists"][0]["archived"] is True


# ---------------------------------------------------------------- today


def test_today_view_buckets(client, clock):
    clock.today = date(2026, 11, 10)
    make_task(client, "Overdue", due_date="2026-11-08")
    make_task(client, "Today later", due_date="2026-11-10", due_time="15:00")
    make_task(client, "Today first", due_date="2026-11-10", due_time="09:00")
    make_task(client, "Friday", due_date="2026-11-13")
    make_task(client, "Too far", due_date="2026-11-30")
    make_task(client, "Someday")
    done = make_task(client, "Already done", due_date="2026-11-10")
    client.patch(f"/api/tasks/{done['id']}", json={"status": "done"})

    view = client.get("/api/today").json()
    assert titles(view["overdue"]) == ["Overdue"]
    assert titles(view["due_today"]) == ["Today first", "Today later"]
    assert titles(view["upcoming"]) == ["Friday"]
    assert view["no_date_count"] == 1
    assert view["done_today_count"] == 1


# ---------------------------------------------------------------- board


def test_board_moves_reorder_columns(client):
    a, b, c = (make_task(client, n) for n in "ABC")

    def column(status):
        return titles(client.get("/api/tasks", params={"status": status}).json())

    assert column("todo") == ["A", "B", "C"]
    client.post(f"/api/tasks/{c['id']}/move", json={"status": "todo", "before_id": a["id"]})
    assert column("todo") == ["C", "A", "B"]
    client.post(f"/api/tasks/{a['id']}/move", json={"status": "in_progress"})
    assert column("todo") == ["C", "B"]
    assert column("in_progress") == ["A"]


# ---------------------------------------------------------------- reminders


def test_reminders_fire_dismiss_and_snooze(client, clock):
    task = make_task(client, "Take out recycling", reminders=["2026-11-01T18:00"])
    assert client.get("/api/reminders/due").json() == []

    clock.time = time(18, 0)
    due = client.get("/api/reminders/due").json()
    assert [(d["task"]["title"], d["remind_at"]) for d in due] == [("Take out recycling", "2026-11-01T18:00")]

    res = client.post(f"/api/reminders/{due[0]['reminder_id']}/snooze", json={"minutes": 10})
    assert res.json()["remind_at"] == "2026-11-01T18:10"
    assert client.get("/api/reminders/due").json() == []

    clock.time = time(18, 10)
    due = client.get("/api/reminders/due").json()
    client.post(f"/api/reminders/{due[0]['reminder_id']}/dismiss")
    assert client.get("/api/reminders/due").json() == []
    assert client.get(f"/api/tasks/{task['id']}").json()["reminders"][0]["dismissed"] is True


def test_done_tasks_do_not_remind(client, clock):
    task = make_task(client, reminders=["2026-11-01T08:00"])
    client.patch(f"/api/tasks/{task['id']}", json={"status": "done"})
    assert client.get("/api/reminders/due").json() == []


def test_editing_reminders_keeps_dismissals_for_unchanged_times(client, clock):
    task = make_task(client, reminders=["2026-11-01T08:00"])
    rid = client.get("/api/reminders/due").json()[0]["reminder_id"]
    client.post(f"/api/reminders/{rid}/dismiss")
    client.patch(f"/api/tasks/{task['id']}", json={"reminders": ["2026-11-01T08:00", "2026-11-02T08:00"]})
    assert client.get("/api/reminders/due").json() == []


# ---------------------------------------------------------------- validation


@pytest.mark.parametrize("body", [
    {"title": ""},
    {"title": "x", "due_time": "09:00"},
    {"title": "x", "due_date": "2026-11-01", "due_time": "9am"},
    {"title": "x", "reminders": ["tomorrow"]},
    {"title": "x", "reminders": ["2026-02-30T09:00"]},
    {"title": "x", "status": "someday"},
    {"title": "x", "label_ids": [999]},
    {"title": "x", "list_id": 999},
])
def test_rejects_bad_input(client, body):
    assert client.post("/api/tasks", json=body).status_code == 422


def test_clearing_a_due_date_requires_clearing_the_time(client):
    task = make_task(client, due_date="2026-11-05", due_time="10:00")
    assert client.patch(f"/api/tasks/{task['id']}", json={"due_date": None}).status_code == 422
    res = client.patch(f"/api/tasks/{task['id']}", json={"due_date": None, "due_time": None})
    assert res.status_code == 200 and res.json()["due_date"] is None


# ---------------------------------------------------------------- calendar


def test_calendar_range_includes_finished_tasks_of_any_age(client, clock):
    make_task(client, "Pay the water bill", due_date="2026-11-03")
    make_task(client, "Book the dentist", due_date="2026-11-20")
    make_task(client, "December thing", due_date="2026-12-02")
    make_task(client, "No date")
    done = make_task(client, "Old finished one", due_date="2026-11-02")
    client.patch(f"/api/tasks/{done['id']}", json={"status": "done"})
    # Weeks later, the default list has dropped it, but the calendar still shows November's work.
    clock.today = date(2026, 12, 20)
    assert "Old finished one" not in titles(client.get("/api/tasks").json())
    month = client.get("/api/tasks", params={"due_from": "2026-11-01", "due_to": "2026-11-30"}).json()
    assert sorted(titles(month)) == ["Book the dentist", "Old finished one", "Pay the water bill"]


# ---------------------------------------------------------------- saved filters


def test_saved_filters_round_trip(client):
    work = labels(client)["work"]["id"]
    res = client.post("/api/filters", json={
        "name": "Critical work", "emoji": "🔥",
        "filters": {"statuses": ["todo", "blocked"], "label_ids": [work], "view": "board"},
    })
    assert res.status_code == 201
    saved = res.json()
    assert saved["filters"] == {"scope": "all", "statuses": ["todo", "blocked"], "label_ids": [work],
                                "q": "", "view": "board"}
    client.post("/api/filters", json={"name": "Search", "filters": {"q": "plumber"}})
    assert [f["name"] for f in client.get("/api/filters").json()] == ["Critical work", "Search"]

    client.patch(f"/api/filters/{saved['id']}", json={"name": "Work fires", "filters": {"scope": "inbox"}})
    updated = client.get("/api/filters").json()[0]
    assert updated["name"] == "Work fires" and updated["filters"]["scope"] == "inbox"

    assert client.delete(f"/api/filters/{saved['id']}").status_code == 204
    assert [f["name"] for f in client.get("/api/filters").json()] == ["Search"]


def test_saved_filters_forget_deleted_labels(client):
    garden = client.post("/api/labels", json={"name": "garden"}).json()
    work = labels(client)["work"]["id"]
    client.post("/api/filters", json={"name": "Weekend", "filters": {"label_ids": [garden["id"], work]}})
    client.delete(f"/api/labels/{garden['id']}")
    filters = client.get("/api/filters").json()[0]["filters"]
    assert filters["label_ids"] == [work]


def test_saved_filter_validation(client):
    assert client.post("/api/filters", json={"name": ""}).status_code == 422
    assert client.post("/api/filters", json={"name": "x", "filters": {"statuses": ["someday"]}}).status_code == 422
    assert client.patch("/api/filters/999", json={"name": "x"}).status_code == 404
