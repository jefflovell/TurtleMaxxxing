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


def test_upgrade_from_v2_keeps_tasks_and_entries(tmp_path):
    path = tmp_path / "v2.db"
    conn = db.connect(path)
    for name in ("0001_budget.sql", "0002_tasks.sql"):
        conn.executescript((db.MIGRATIONS_DIR / name).read_text(encoding="utf-8"))
    conn.execute("PRAGMA user_version = 2")
    conn.execute(
        "INSERT INTO accounts (name, kind, opening_balance_cents, opening_date) "
        "VALUES ('Checking', 'checking', 0, '2026-10-01')"
    )
    conn.execute(
        "INSERT INTO entries (account_id, date, amount_cents, description, status) "
        "VALUES (1, '2026-10-05', -1500, 'Lunch', 'confirmed')"
    )
    conn.execute("INSERT INTO tasks (title) VALUES ('Call the plumber')")
    conn.commit()

    db.migrate(conn)

    assert conn.execute("SELECT title FROM tasks").fetchone()["title"] == "Call the plumber"
    entry = conn.execute("SELECT description, import_key FROM entries").fetchone()
    assert (entry["description"], entry["import_key"]) == ("Lunch", None)
    assert conn.execute("SELECT COUNT(*) FROM saved_filters").fetchone()[0] == 0
    assert len(list(config.backups_dir().glob("turtle-*-v2.db"))) == 1
    conn.close()


def test_upgrade_from_v3_adds_contacts_and_keeps_tasks(tmp_path):
    conn = db.connect(tmp_path / "v3.db")
    for file in sorted(db.MIGRATIONS_DIR.glob("*.sql"))[:3]:
        conn.executescript(file.read_text(encoding="utf-8"))
    conn.execute("PRAGMA user_version = 3")
    conn.execute("INSERT INTO tasks (title) VALUES ('Client meeting')")
    work = conn.execute("SELECT id FROM labels WHERE name = 'work'").fetchone()["id"]
    conn.execute("INSERT INTO task_labels VALUES (1, ?)", (work,))
    conn.commit()

    db.migrate(conn)

    assert conn.execute("SELECT title FROM tasks").fetchone()["title"] == "Client meeting"
    assert conn.execute("SELECT COUNT(*) FROM task_labels").fetchone()[0] == 1
    conn.execute("INSERT INTO contacts (name) VALUES ('Mr. Anderson')")
    conn.execute("INSERT INTO task_contacts VALUES (1, 1)")
    conn.execute("INSERT INTO contact_labels VALUES (1, ?)", (work,))
    assert len(list(config.backups_dir().glob("turtle-*-v3.db"))) == 1
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
