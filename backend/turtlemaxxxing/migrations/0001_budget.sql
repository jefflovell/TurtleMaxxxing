-- Budget: accounts, recurring rules with splits, ledger entries, review inbox.
-- Money is stored as integer cents. Dates are ISO strings (YYYY-MM-DD).

CREATE TABLE accounts (
    id                    INTEGER PRIMARY KEY,
    name                  TEXT    NOT NULL,
    kind                  TEXT    NOT NULL DEFAULT 'checking'
                          CHECK (kind IN ('checking', 'savings', 'credit', 'hsa', 'retirement',
                                          'brokerage', 'education', 'goal', 'other')),
    opening_balance_cents INTEGER NOT NULL DEFAULT 0,
    opening_date          TEXT    NOT NULL,
    checkin_every_days    INTEGER,          -- NULL = no balance check-ins
    last_checkin_date     TEXT,
    archived              INTEGER NOT NULL DEFAULT 0,
    created_at            TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- "This amount moves on this schedule." Income can be split across accounts;
-- bills and subscriptions take money out of account_id.
CREATE TABLE rules (
    id                  INTEGER PRIMARY KEY,
    kind                TEXT    NOT NULL CHECK (kind IN ('income', 'bill', 'subscription')),
    name                TEXT    NOT NULL,
    amount_cents        INTEGER NOT NULL CHECK (amount_cents >= 0),
    account_id          INTEGER NOT NULL REFERENCES accounts(id),
    frequency           TEXT    NOT NULL
                        CHECK (frequency IN ('once', 'weekly', 'biweekly', 'semimonthly',
                                             'monthly', 'quarterly', 'yearly')),
    start_date          TEXT    NOT NULL,
    end_date            TEXT,             -- NULL = runs forever
    second_day          INTEGER,          -- semimonthly only: the second day of the month
    review_every_months INTEGER,          -- "are you still paying for this?" cadence
    last_reviewed_date  TEXT,
    posted_through      TEXT,             -- auto-posting has created entries up to this date
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Income splits, e.g. paycheck -> HSA $127.39, 401(k) $322.58. The remainder
-- goes to the rule's account_id.
CREATE TABLE rule_splits (
    id           INTEGER PRIMARY KEY,
    rule_id      INTEGER NOT NULL REFERENCES rules(id) ON DELETE CASCADE,
    account_id   INTEGER NOT NULL REFERENCES accounts(id),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    label        TEXT
);

-- The ledger. Positive = money in, negative = money out.
--   expected   auto-posted from a rule, not yet confirmed
--   confirmed  the user (or a CSV import) confirmed it happened
--   adjustment a correction from a balance check-in
CREATE TABLE entries (
    id              INTEGER PRIMARY KEY,
    account_id      INTEGER NOT NULL REFERENCES accounts(id),
    date            TEXT    NOT NULL,
    amount_cents    INTEGER NOT NULL,
    description     TEXT    NOT NULL,
    status          TEXT    NOT NULL CHECK (status IN ('expected', 'confirmed', 'adjustment')),
    rule_id         INTEGER REFERENCES rules(id) ON DELETE SET NULL,
    occurrence_date TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- One entry per rule, occurrence and account, so auto-posting is safe to re-run.
CREATE UNIQUE INDEX entries_rule_occurrence
    ON entries (rule_id, occurrence_date, account_id) WHERE rule_id IS NOT NULL;
CREATE INDEX entries_account_date ON entries (account_id, date);

-- Review inbox: balance check-ins and subscription reviews.
CREATE TABLE reviews (
    id          INTEGER PRIMARY KEY,
    kind        TEXT NOT NULL CHECK (kind IN ('balance_checkin', 'subscription_review')),
    account_id  INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    rule_id     INTEGER REFERENCES rules(id) ON DELETE CASCADE,
    due_date    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'done', 'dismissed')),
    resolution  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT
);
