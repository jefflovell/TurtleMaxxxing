-- Saved task filters (pinned in the sidebar) and CSV import tracking.

-- A named view of the task list, e.g. "🔥 Critical work".
-- filters is JSON: {"scope": "all"|"inbox"|<list id>, "statuses": [...],
-- "label_ids": [...], "q": "...", "view": "list"|"board"}.
CREATE TABLE saved_filters (
    id         INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    emoji      TEXT,
    filters    TEXT    NOT NULL DEFAULT '{}',
    position   REAL    NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Ledger entries confirmed or created by a CSV import remember which bank
-- row they came from, so importing the same file twice changes nothing.
ALTER TABLE entries ADD COLUMN import_key TEXT;
CREATE UNIQUE INDEX entries_import_key ON entries (account_id, import_key)
    WHERE import_key IS NOT NULL;
