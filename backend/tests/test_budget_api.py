"""End-to-end budget behavior through the HTTP API."""

from datetime import date


def make_account(client, name, kind="checking", opening=0, **extra):
    body = {"name": name, "kind": kind, "opening_balance_cents": opening,
            "opening_date": "2026-10-31", **extra}
    res = client.post("/api/accounts", json=body)
    assert res.status_code == 201, res.text
    return res.json()["id"]


def balances(client):
    return {a["name"]: a["balance_cents"] for a in client.get("/api/accounts").json()}


def paycheck(client, checking, splits, amount=245000, start="2026-11-06"):
    res = client.post("/api/rules", json={
        "kind": "income", "name": "Paycheck", "amount_cents": amount,
        "account_id": checking, "frequency": "biweekly", "start_date": start,
        "splits": splits,
    })
    assert res.status_code == 201, res.text
    return res.json()


def test_health(client):
    assert client.get("/api/health").json()["ok"] is True


def test_paycheck_splits_auto_post_and_update_balances(client, clock):
    checking = make_account(client, "Checking", opening=100000)
    hsa = make_account(client, "HSA", "hsa")
    k401 = make_account(client, "401(k)", "retirement")
    kid_a = make_account(client, "Kid A 529", "education")
    paycheck(client, checking, [
        {"account_id": hsa, "amount_cents": 12739, "label": "HSA"},
        {"account_id": k401, "amount_cents": 32258, "label": "401(k)"},
        {"account_id": kid_a, "amount_cents": 5000, "label": "Kid A 529"},
    ])

    # Before payday nothing has moved.
    assert balances(client)["HSA"] == 0

    clock.today = date(2026, 11, 6)
    b = balances(client)
    assert b["HSA"] == 12739
    assert b["401(k)"] == 32258
    assert b["Kid A 529"] == 5000
    assert b["Checking"] == 100000 + 245000 - 12739 - 32258 - 5000

    # Two weeks later it happens again, with no manual entry.
    clock.today = date(2026, 11, 20)
    assert balances(client)["HSA"] == 2 * 12739


def test_auto_posting_is_idempotent(client, clock):
    checking = make_account(client, "Checking")
    paycheck(client, checking, [])
    clock.today = date(2026, 11, 6)
    client.get("/api/accounts")
    clock.today = date(2026, 11, 7)
    client.get("/api/accounts")
    entries = client.get("/api/entries", params={"start": "2026-11-01", "end": "2026-11-30"}).json()
    assert len(entries) == 1
    assert entries[0]["status"] == "expected"


def test_rule_dates_before_the_opening_balance_are_not_double_counted(client, clock):
    # The balance entered as of Oct 31 already includes the July-Oct charges and Oct 31 rent.
    checking = make_account(client, "Checking", opening=284000)  # opening_date 2026-10-31
    client.post("/api/rules", json={
        "kind": "subscription", "name": "Streaming", "amount_cents": 1599, "account_id": checking,
        "frequency": "monthly", "start_date": "2026-07-05",
    })
    client.post("/api/rules", json={
        "kind": "bill", "name": "Rent", "amount_cents": 165000, "account_id": checking,
        "frequency": "monthly", "start_date": "2026-10-31",
    })
    assert balances(client)["Checking"] == 284000
    assert client.get("/api/entries", params={"start": "2026-01-01", "end": "2026-11-01"}).json() == []

    clock.today = date(2026, 11, 5)
    assert balances(client)["Checking"] == 284000 - 1599


def test_splits_cannot_exceed_amount(client):
    checking = make_account(client, "Checking")
    hsa = make_account(client, "HSA", "hsa")
    res = client.post("/api/rules", json={
        "kind": "income", "name": "Pay", "amount_cents": 1000, "account_id": checking,
        "frequency": "monthly", "start_date": "2026-11-01",
        "splits": [{"account_id": hsa, "amount_cents": 1001}],
    })
    assert res.status_code == 422


def test_rule_edits_change_the_future_not_the_past(client, clock):
    checking = make_account(client, "Checking")
    rule = client.post("/api/rules", json={
        "kind": "bill", "name": "Internet", "amount_cents": 6000, "account_id": checking,
        "frequency": "monthly", "start_date": "2026-11-05",
    }).json()
    clock.today = date(2026, 11, 10)
    client.get("/api/accounts")
    client.patch(f"/api/rules/{rule['id']}", json={"amount_cents": 7000})
    clock.today = date(2026, 12, 10)
    entries = client.get("/api/entries", params={"start": "2026-11-01", "end": "2026-12-31"}).json()
    assert [e["amount_cents"] for e in entries] == [-6000, -7000]


def test_cashflow_runs_balance_through_the_month_with_projections(client, clock):
    checking = make_account(client, "Checking", opening=50000)
    paycheck(client, checking, [], amount=200000, start="2026-11-13")
    client.post("/api/rules", json={
        "kind": "bill", "name": "Rent", "amount_cents": 150000, "account_id": checking,
        "frequency": "monthly", "start_date": "2026-11-03",
    })
    clock.today = date(2026, 11, 5)
    flow = client.get("/api/cashflow", params={"month": "2026-11"}).json()
    days = {d["date"]: d for d in flow["days"]}

    assert flow["start_balance_cents"] == 50000
    assert days["2026-11-03"]["balance_cents"] == 50000 - 150000
    assert days["2026-11-13"]["balance_cents"] == 50000 - 150000 + 200000
    assert days["2026-11-13"]["projected"] is True
    assert flow["low_point"] == {"date": "2026-11-03", "balance_cents": -100000}
    statuses = {e["description"]: e["status"] for e in flow["events"]}
    assert statuses == {"Rent": "expected", "Paycheck": "projected"}


def test_cashflow_shows_starting_balance_in_the_opening_month(client):
    client.post("/api/accounts", json={
        "name": "Checking", "opening_balance_cents": 284000, "opening_date": "2026-11-10",
    })
    flow = client.get("/api/cashflow", params={"month": "2026-11"}).json()
    days = {d["date"]: d["balance_cents"] for d in flow["days"]}
    assert flow["start_balance_cents"] == 0
    assert days["2026-11-09"] == 0
    assert days["2026-11-10"] == 284000
    assert [(e["description"], e["status"]) for e in flow["events"]] == [("Starting balance", "opening")]


def test_cashflow_for_a_future_month_starts_from_projected_balance(client):
    checking = make_account(client, "Checking", opening=10000)
    client.post("/api/rules", json={
        "kind": "subscription", "name": "Streaming", "amount_cents": 1500, "account_id": checking,
        "frequency": "monthly", "start_date": "2026-11-20",
    })
    flow = client.get("/api/cashflow", params={"month": "2027-01"}).json()
    assert flow["start_balance_cents"] == 10000 - 1500 * 2


def test_calendar_shows_bills_and_mark_paid(client, clock):
    checking = make_account(client, "Checking")
    rule = client.post("/api/rules", json={
        "kind": "bill", "name": "Water", "amount_cents": 4500, "account_id": checking,
        "frequency": "monthly", "start_date": "2026-11-15",
    }).json()
    cal = client.get("/api/calendar", params={"month": "2026-11"}).json()
    assert [(e["date"], e["status"]) for e in cal["events"]] == [("2026-11-15", "projected")]

    # Paying early confirms the future date, and it isn't projected twice.
    res = client.post(f"/api/rules/{rule['id']}/occurrences/2026-11-15/confirm")
    assert res.status_code == 200
    cal = client.get("/api/calendar", params={"month": "2026-11"}).json()
    assert [(e["date"], e["status"]) for e in cal["events"]] == [("2026-11-15", "confirmed")]

    # When the date arrives, auto-posting doesn't add a duplicate.
    clock.today = date(2026, 11, 20)
    assert balances(client)["Checking"] == -4500


def test_confirm_rejects_dates_that_are_not_on_the_schedule(client):
    checking = make_account(client, "Checking")
    rule = client.post("/api/rules", json={
        "kind": "bill", "name": "Water", "amount_cents": 4500, "account_id": checking,
        "frequency": "monthly", "start_date": "2026-11-15",
    }).json()
    assert client.post(f"/api/rules/{rule['id']}/occurrences/2026-11-16/confirm").status_code == 422


def test_balance_checkin_creates_adjustment(client, clock):
    make_account(client, "HSA", "hsa", opening=400000, checkin_every_days=30)
    assert client.get("/api/reviews").json() == []

    clock.today = date(2026, 12, 1)
    open_reviews = client.get("/api/reviews").json()
    assert len(open_reviews) == 1
    review = open_reviews[0]
    assert review["kind"] == "balance_checkin"
    assert review["expected_balance_cents"] == 400000

    res = client.post(f"/api/reviews/{review['id']}/checkin", json={"actual_balance_cents": 431200})
    assert res.json() == {"adjustment_cents": 31200}
    assert balances(client)["HSA"] == 431200
    assert client.get("/api/reviews").json() == []


def test_subscription_review_keep_cancel_and_change_price(client, clock):
    checking = make_account(client, "Checking")
    for name in ("Music", "Gym", "Cloud storage"):
        client.post("/api/rules", json={
            "kind": "subscription", "name": name, "amount_cents": 1000, "account_id": checking,
            "frequency": "monthly", "start_date": "2026-08-01", "review_every_months": 3,
        })
    open_reviews = {r["rule_name"]: r for r in client.get("/api/reviews").json()}
    assert set(open_reviews) == {"Music", "Gym", "Cloud storage"}

    client.post(f"/api/reviews/{open_reviews['Music']['id']}/subscription", json={"action": "keep"})
    client.post(f"/api/reviews/{open_reviews['Gym']['id']}/subscription", json={"action": "cancel"})
    client.post(
        f"/api/reviews/{open_reviews['Cloud storage']['id']}/subscription",
        json={"action": "change_price", "new_amount_cents": 1200},
    )
    assert client.get("/api/reviews").json() == []

    clock.today = date(2026, 12, 2)
    december = client.get("/api/entries", params={"start": "2026-12-01", "end": "2026-12-31"}).json()
    assert sorted((e["description"], e["amount_cents"]) for e in december) == [
        ("Cloud storage", -1200), ("Music", -1000),
    ]


def test_check_balance_now(client):
    hsa = make_account(client, "HSA", "hsa", opening=1000)
    first = client.post(f"/api/accounts/{hsa}/checkin").json()["review_id"]
    again = client.post(f"/api/accounts/{hsa}/checkin").json()["review_id"]
    assert first == again
    assert [r["account_name"] for r in client.get("/api/reviews").json()] == ["HSA"]
    assert client.post("/api/accounts/999/checkin").status_code == 404


def test_dismissed_review_comes_back_next_interval(client, clock):
    make_account(client, "Savings", "savings", checkin_every_days=30)
    clock.today = date(2026, 12, 1)
    review = client.get("/api/reviews").json()[0]
    client.post(f"/api/reviews/{review['id']}/dismiss")
    assert client.get("/api/reviews").json() == []
    clock.today = date(2026, 12, 31)
    assert len(client.get("/api/reviews").json()) == 1
