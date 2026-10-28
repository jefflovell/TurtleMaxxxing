"""SQLite connection and migrations.

Schema changes are numbered SQL files in migrations/ (0001_..., 0002_...).
The database remembers the last one applied in PRAGMA user_version. Before
applying new migrations to an existing database, a backup copy is saved in
the data folder's backups/ directory.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from . import config

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def connect(path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrations() -> list[tuple[int, Path]]:
    found = []
    for file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        found.append((int(file.name.split("_", 1)[0]), file))
    return found


def _backup(conn: sqlite3.Connection, version: int) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = config.backups_dir() / f"turtle-{stamp}-v{version}.db"
    with sqlite3.connect(target) as backup:
        conn.backup(backup)
    return target


def migrate(conn: sqlite3.Connection) -> int:
    """Apply any pending migrations. Returns the schema version afterwards."""
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    pending = [(v, f) for v, f in _migrations() if v > current]
    if pending and current > 0:
        _backup(conn, current)
    for version, file in pending:
        conn.executescript(file.read_text(encoding="utf-8"))
        conn.execute(f"PRAGMA user_version = {version}")
        conn.commit()
        current = version
    return current
