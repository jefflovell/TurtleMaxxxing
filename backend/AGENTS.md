# Backend guide

Python 3.12+, FastAPI and SQLite (Python's built-in `sqlite3`, no ORM). Managed with `uv`.

## Files

| File | What it does |
|---|---|
| `turtlemaxxxing/__main__.py` | Command line: start (default), `--demo`, `--find-port`, `--hostname`. |
| `turtlemaxxxing/app.py` | `create_app()`: runs migrations, installs the security guard, mounts the API, serves `frontend/dist` if it has been built. |
| `turtlemaxxxing/config.py` | Data folder and address settings (`settings.json`: port and `*.localhost` friendly name). `HOST` must stay `127.0.0.1`. |
| `turtlemaxxxing/security.py` | Guards against malicious websites: answers only to its own host names, and refuses cross-site changes. **Never loosen; see `docs/TESTING.md`.** |
| `turtlemaxxxing/ports.py` | Free-port scan used by `--find-port`. |
| `turtlemaxxxing/demo.py` | Fictional demo data for `--demo` and manual testing. |
| `turtlemaxxxing/db.py` | Connections and migrations. Backs up the database before applying new migrations. |
| `turtlemaxxxing/deps.py` | Per-request DB connection, "today", and the daily tick (auto-post entries + open due reviews). |
| `turtlemaxxxing/migrations/` | Numbered SQL files. **Never edit one that has shipped;** add a new file instead. |
| `turtlemaxxxing/budget/` | The budget feature, including CSV import. See its own `AGENTS.md`. |
| `turtlemaxxxing/tasks/` | Tasks, labels, lists, reminders and saved filters. See its own `AGENTS.md`. |
| `turtlemaxxxing/contacts/` | Contacts and the people on each task. See its own `AGENTS.md`. |
| `tests/` | pytest suite. `conftest.py` gives a temp database and a movable `clock`. |

## Common changes

**Add a database column or table**
1. Create `turtlemaxxxing/migrations/000N_short_name.sql` with the next number.
2. Use `ALTER TABLE ... ADD COLUMN ...` (SQLite can't drop or rename easily, so prefer adding).
3. Update the code and API models that use it.
4. Add a test. Run `uv run pytest -q`.
5. Existing users are migrated automatically on next start, with a backup taken first.

**Add an API endpoint**
Add it to the feature's `api.py` router, using `Depends(get_db)` and `Depends(get_today)`. Then add a test in `tests/` that calls it through the `client` fixture.

**Add a dependency**
`uv add <package>` (or `uv add --dev <package>` for test-only). Then record it in `docs/SETUP_NOTES.md`. **Check it makes no network calls at runtime**; `tests/test_privacy.py` will catch most of these.

## Testing

Follow [docs/TESTING.md](../docs/TESTING.md) (binding).

```bash
uv run pytest -q
```

- Tests never touch the real data folder (`TURTLE_DATA_DIR` points to a temp folder).
- Move time with the `clock` fixture: `clock.today = date(2026, 12, 1)`.
- `test_privacy.py` fails if anything makes a non-localhost connection or DNS lookup.

## Don't
- Don't bind to `0.0.0.0` or any non-loopback address.
- Don't add telemetry, analytics or "phone home" update checks.
- Don't store money as floats; use integer cents.
- Don't name a class field after its own type (`date: date | None = None`). It works on new Pythons and crashes on 3.12. Use `import datetime as dt` and `date: dt.date | None`. To check locally: `uv run --python 3.12 --isolated --with-editable . --with pytest --with httpx pytest -q`.
