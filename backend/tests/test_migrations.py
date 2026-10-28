"""Upgrading an existing database keeps the user's data and takes a backup first.

Required by docs/TESTING.md for every new schema version.
"""

from turtlemaxxxing import config, db


def test_upgrade_from_v1_keeps_data_and_backs_up(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    conn = db.connect(path)
    # Build a version-1 database by hand, exactly as 0001 left it.
    conn.executescript((db.MIGRATIONS_DIR / "0001_budget.sql").read_text(encoding="utf-8"))
    conn.execute("PRAGMA user_version = 1")
    conn.execute(
        "INSERT INTO accounts (name, kind, opening_balance_cents, opening_date) "
        "VALUES ('Checking', 'checking', 123456, '2026-10-01')"
    )
    conn.commit()

    version = db.migrate(conn)

    assert version == len(list(db.MIGRATIONS_DIR.glob("*.sql")))
    row = conn.execute("SELECT name, opening_balance_cents FROM accounts").fetchone()
    assert (row["name"], row["opening_balance_cents"]) == ("Checking", 123456)
    # The new tables exist and come with starter labels.
    assert conn.execute("SELECT COUNT(*) FROM labels").fetchone()[0] > 0
    # A backup of the version-1 database was saved before upgrading.
    backups = list(config.backups_dir().glob("turtle-*-v1.db"))
    assert len(backups) == 1
    old = db.connect(backups[0])
    assert old.execute("PRAGMA user_version").fetchone()[0] == 1
    assert old.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 1
    old.close()
    conn.close()


def test_fresh_install_needs_no_backup(tmp_path):
    conn = db.connect(tmp_path / "new.db")
    db.migrate(conn)
    assert list(config.backups_dir().glob("*.db")) == []
    conn.close()


def test_migrating_twice_is_harmless(tmp_path):
    conn = db.connect(tmp_path / "twice.db")
    first = db.migrate(conn)
    assert db.migrate(conn) == first
    assert list(config.backups_dir().glob("*.db")) == []
    conn.close()
