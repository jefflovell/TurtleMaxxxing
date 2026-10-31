-- Contacts ("Mr. Anderson -> Smith Agency"), their labels, and the people a task is about.

CREATE TABLE contacts (
    id           INTEGER PRIMARY KEY,
    name         TEXT    NOT NULL,
    organization TEXT    NOT NULL DEFAULT '',
    role         TEXT    NOT NULL DEFAULT '',   -- e.g. "Project manager", "Dentist"
    email        TEXT    NOT NULL DEFAULT '',
    phone        TEXT    NOT NULL DEFAULT '',
    location     TEXT    NOT NULL DEFAULT '',   -- where you meet them, e.g. "Smith Agency, 2nd floor"
    notes        TEXT    NOT NULL DEFAULT '',
    private      INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX contacts_name ON contacts (name COLLATE NOCASE);

-- Contacts share the task labels, so "work" and the auto-Private "private" label mean the same thing.
CREATE TABLE contact_labels (
    contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    label_id   INTEGER NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
    PRIMARY KEY (contact_id, label_id)
);

-- "Prep for client meeting" is with Mr. Anderson. Deleting either side removes the link.
CREATE TABLE task_contacts (
    task_id    INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, contact_id)
);
CREATE INDEX task_contacts_contact ON task_contacts (contact_id);
