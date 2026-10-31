"""CSV import: bank rows confirm what the budget expected, and nothing is counted twice.

All names and amounts are fictional.
"""

from datetime import date

import pytest

from turtlemaxxxing.budget.csv_import import CsvError, detect_date_format, parse_amount

from test_budget_api import balances, make_account, paycheck

BANK_CSV = """Date,Description,Amount
11/02/2026,ACME PROPERTY MGMT,-1650.00
11/06/2026,EMPLOYER PAYROLL,2322.61
11/07/2026,CITY POWER,-131.40
11/12/2026,GROCERY MART,-84.12
11/12/2026,COFFEE,-5.00
11/12/2026,COFFEE,-5.00
11/20/2026,EMPLOYER PAYROLL,2322.61
11/22/2026,FIBER NET,-70.00
10/30/2026,OLD THING,-10.00
not a date,???,1.00
"""


def bill(client, account, name, cents, start):
    res = client.post("/api/rules", json={
        "kind": "bill", "name": name, "amount_cents": cents, "account_id": account,
        "frequency": "monthly", "start_date": start,
    })
    assert res.status_code == 201, res.text
    return res.json()["id"]


@pytest.fixture
def household(client, clock):
    """Checking ($1,000 on Oct 31), rent, electric, internet and a split paycheck; today is Nov 23."""
    checking = make_account(client, "Checking", opening=100000)
    hsa = make_account(client, "HSA", "hsa")
    paycheck(client, checking, [{"account_id": hsa, "amount_cents": 12739, "label": "HSA"}])
    bill(client, checking, "Rent", 165000, "2026-11-01")
    bill(client, checking, "Electric", 12000, "2026-11-05")
    bill(client, checking, "Internet", 7000, "2026-11-25")
    clock.today = date(2026, 11, 23)
    return checking


def preview(client, account, text=BANK_CSV, **mapping):
    res = client.post("/api/import/preview", json={"account_id": account, "csv_text": text, "mapping": mapping})
    assert res.status_code == 200, res.text
    return res.json()


def apply(client, account, text=BANK_CSV, skip_rows=(), **mapping):
    res = client.post("/api/import/apply", json={
        "account_id": account, "csv_text": text, "mapping": mapping, "skip_rows": list(skip_rows),
    })
    assert res.status_code == 200, res.text
    return res.json()


def actions(plan):
    return [(r["description"], r["action"]) for r in plan["rows"]]


def test_preview_matches_bank_rows_to_expected_entries(client, household):
    plan = preview(client, household)
    assert plan["mapping"]["date_format"] == "%m/%d/%Y"
    assert actions(plan) == [
        ("ACME PROPERTY MGMT", "match"),      # rent, posted a day after it was due
        ("EMPLOYER PAYROLL", "match"),        # the checking part of the split paycheck
        ("CITY POWER", "match_changed"),      # electric came in higher than expected
        ("GROCERY MART", "new"),
        ("COFFEE", "new"),
        ("COFFEE", "new"),                    # same day, same amount: still two coffees
        ("EMPLOYER PAYROLL", "match"),        # the next paycheck
        ("FIBER NET", "match"),               # internet, paid 3 days before it's due
        ("OLD THING", "before_start"),        # already in the starting balance
        ("???", "error"),
    ]
    electric = plan["rows"][2]
    assert electric["match"]["amount_cents"] == -12000 and electric["amount_cents"] == -13140


def test_preview_changes_nothing(client, household):
    before = balances(client)
    preview(client, household)
    assert balances(client) == before
    assert preview(client, household)["counts"]["match"] == 4


def test_apply_confirms_matches_adds_the_rest_and_balances_add_up(client, clock, household):
    result = apply(client, household)
    assert result == {"confirmed": 5, "added": 3, "skipped": 2}
    expected = (100000 - 165000 + 2 * 232261 - 13140 - 8412 - 500 - 500 - 7000)
    assert balances(client)["Checking"] == expected

    entries = {e["description"]: e for e in client.get(
        "/api/entries", params={"start": "2026-11-01", "end": "2026-11-30", "account_id": household}
    ).json()}
    assert entries["Rent"]["status"] == "confirmed" and entries["Rent"]["date"] == "2026-11-02"
    assert entries["Electric"]["amount_cents"] == -13140
    assert entries["GROCERY MART"]["status"] == "confirmed"

    # Internet was paid early: when its due date comes, it isn't posted again.
    clock.today = date(2026, 11, 26)
    assert balances(client)["Checking"] == expected


def test_importing_the_same_file_twice_changes_nothing(client, household):
    apply(client, household)
    after_first = balances(client)
    plan = preview(client, household)
    assert plan["counts"] == {"duplicate": 8, "before_start": 1, "error": 1}
    assert apply(client, household) == {"confirmed": 0, "added": 0, "skipped": 10}
    assert balances(client) == after_first


def test_overlapping_files_only_add_the_new_rows(client, household):
    lines = BANK_CSV.splitlines()
    header, coffee = lines[0], lines[5]
    # The first download ends after one coffee...
    apply(client, household, "\n".join(lines[:6]))
    # ...and the next one starts with that same coffee, then a second one.
    plan = preview(client, household, "\n".join([header, coffee, coffee]))
    assert actions(plan) == [("COFFEE", "duplicate"), ("COFFEE", "new")]


def test_rows_marked_paid_by_hand_are_linked_not_added_again(client, household):
    rent = next(r for r in client.get("/api/rules").json() if r["name"] == "Rent")
    client.post(f"/api/rules/{rent['id']}/occurrences/2026-11-01/confirm")
    before = balances(client)["Checking"]

    plan = preview(client, household, "Date,Description,Amount\n11/02/2026,ACME PROPERTY MGMT,-1650.00\n")
    assert plan["rows"][0]["action"] == "match"
    assert plan["rows"][0]["match"]["confirmed"] is True
    apply(client, household, "Date,Description,Amount\n11/02/2026,ACME PROPERTY MGMT,-1650.00\n")
    assert balances(client)["Checking"] == before


def test_unticked_rows_are_skipped(client, household):
    plan = preview(client, household)
    grocery = next(r["row"] for r in plan["rows"] if r["description"] == "GROCERY MART")
    result = apply(client, household, skip_rows=[grocery])
    assert result["added"] == 2
    descriptions = [e["description"] for e in client.get(
        "/api/entries", params={"start": "2026-11-01", "end": "2026-11-30"}
    ).json()]
    assert "GROCERY MART" not in descriptions


def test_the_file_itself_is_never_stored(client, household, tmp_path):
    apply(client, household)
    # Skipped rows leave no trace anywhere in the database.
    raw = (tmp_path / "test.db").read_bytes()
    assert b"OLD THING" not in raw and b"not a date" not in raw


def test_debit_credit_columns_preamble_and_card_signs(client, household):
    text = (
        "Account,Everyday Checking\n"
        "Exported,2026-11-23\n"
        "\n"
        "Posting Date,Payee,Debit,Credit\n"
        "2026-11-12,GROCERY MART,84.12,\n"
        "2026-11-13,REFUND,,12.00\n"
    )
    plan = preview(client, household, text)
    assert plan["mapping"]["date_col"] == "Posting Date"
    assert [r["amount_cents"] for r in plan["rows"]] == [-8412, 1200]

    # A card statement that shows purchases as positive numbers.
    card = "Transaction Date,Description,Amount\n2026-11-12,GROCERY MART,84.12\n"
    assert preview(client, household, card, flip_sign=True)["rows"][0]["amount_cents"] == -8412


def test_columns_can_be_picked_by_hand(client, household):
    text = "When,What,How much\n2026-11-12,GROCERY MART,-84.12\n"
    res = client.post("/api/import/preview", json={"account_id": household, "csv_text": text})
    assert res.status_code == 422 and "date column" in res.json()["detail"]
    plan = preview(client, household, text, date_col="When", description_col="What", amount_col="How much")
    assert plan["rows"][0]["amount_cents"] == -8412


def test_switching_from_one_amount_column_to_debit_and_credit(client, household):
    text = "Date,Description,Amount,Debit,Credit\n2026-11-12,GROCERY MART,ignored,84.12,\n"
    plan = preview(client, household, text, amount_col="")
    assert plan["mapping"]["amount_col"] is None and plan["mapping"]["debit_col"] == "Debit"
    assert plan["rows"][0]["amount_cents"] == -8412


def test_import_errors(client, household):
    res = client.post("/api/import/preview", json={"account_id": 999, "csv_text": BANK_CSV})
    assert res.status_code == 404
    res = client.post("/api/import/preview", json={"account_id": household, "csv_text": BANK_CSV,
                                                   "mapping": {"date_col": "Nope"}})
    assert res.status_code == 422


@pytest.mark.parametrize("text, cents", [
    ("-12.34", -1234), ("$1,234.56", 123456), ("(12.00)", -1200), ("12.00-", -1200),
    ("12.00 DR", -1200), ("5", 500), ("", None),
])
def test_parse_amount(text, cents):
    assert parse_amount(text) == cents


def test_parse_amount_rejects_junk():
    with pytest.raises(ValueError):
        parse_amount("twelve")


def test_date_format_detection():
    assert detect_date_format(["2026-11-02", "2026-11-30"]) == "%Y-%m-%d"
    assert detect_date_format(["11/02/2026", "11/30/2026"]) == "%m/%d/%Y"
    assert detect_date_format(["30/11/2026", "02/11/2026"]) == "%d/%m/%Y"
    # One junk row doesn't sink the file.
    assert detect_date_format(["11/02/2026", "Pending", "11/30/2026"]) == "%m/%d/%Y"
    with pytest.raises(CsvError):
        detect_date_format(["someday"])
