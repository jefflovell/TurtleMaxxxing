-- Tasks and reminders (PLAN.md §2b): lists, user-defined labels with
-- favorites, tasks with kanban status, reminders.

-- Lists group tasks into projects ("Home reno", "Taxes"). Tasks with no
-- list live in the Inbox.
CREATE TABLE lists (
    id         INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    emoji      TEXT,
    position   INTEGER NOT NULL DEFAULT 0,
    archived   INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- User-defined labels. Favorites show as one-click chips. An auto_private
-- label makes every task tagged with it Private (hidden from all AI paths).
CREATE TABLE labels (
    id           INTEGER PRIMARY KEY,
    name         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    color        TEXT    NOT NULL DEFAULT 'slate',
    emoji        TEXT,
    favorite     INTEGER NOT NULL DEFAULT 0,
    auto_private INTEGER NOT NULL DEFAULT 0,
    position     INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE tasks (
    id           INTEGER PRIMARY KEY,
    list_id      INTEGER REFERENCES lists(id) ON DELETE SET NULL,
    title        TEXT    NOT NULL,
    notes        TEXT    NOT NULL DEFAULT '',
    status       TEXT    NOT NULL DEFAULT 'todo'
                 CHECK (status IN ('todo', 'in_progress', 'blocked', 'done')),
    blocked_note TEXT,
    due_date     TEXT,                    -- YYYY-MM-DD, optional
    due_time     TEXT,                    -- HH:MM, optional (needs due_date)
    private      INTEGER NOT NULL DEFAULT 0,
    position     REAL    NOT NULL DEFAULT 0,  -- order within a board column
    completed_at TEXT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX tasks_status ON tasks (status, position);
CREATE INDEX tasks_due ON tasks (due_date);

CREATE TABLE task_labels (
    task_id  INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    label_id INTEGER NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, label_id)
);

-- Reminders fire in the app at remind_at (local time, YYYY-MM-DDTHH:MM).
CREATE TABLE task_reminders (
    id           INTEGER PRIMARY KEY,
    task_id      INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    remind_at    TEXT    NOT NULL,
    dismissed_at TEXT
);
CREATE INDEX task_reminders_due ON task_reminders (remind_at) WHERE dismissed_at IS NULL;

-- Starter labels. Users can rename, recolor, delete or add their own.
INSERT INTO labels (name, color, emoji, favorite, auto_private, position) VALUES
    ('critical',  'red',     '🔥', 1, 0, 1),
    ('urgent',    'orange',  '⏰', 1, 0, 2),
    ('important', 'yellow',  '⭐', 1, 0, 3),
    ('work',      'blue',    '💼', 1, 0, 4),
    ('home',      'green',   '🏠', 0, 0, 5),
    ('family',    'magenta', '💞', 0, 0, 6),
    ('money',     'aqua',    '💸', 0, 0, 7),
    ('private',   'violet',  '🔒', 0, 1, 8);
