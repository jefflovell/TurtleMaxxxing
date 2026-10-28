from datetime import date

from turtlemaxxxing import demo
from turtlemaxxxing.budget import ledger


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
