# Budget module guide

The "manual starter that becomes automatic" from `PLAN.md` §2a.

## Concepts

| Concept | Table | Notes |
|---|---|---|
| **Account** | `accounts` | Anywhere money lives (checking, HSA, 529...). Its opening balance is the balance at the **end** of `opening_date`, so only movements *after* that date count. |
| **Rule** | `rules` | Money that moves on a schedule: `income`, `bill` or `subscription`. |
| **Split** | `rule_splits` | Income only: fixed amounts to other accounts. The remainder goes to the rule's own account. |
| **Entry** | `entries` | The ledger. `expected` (auto-posted), `confirmed` (user said it happened), `adjustment` (from a balance check-in). Positive = money in. |
| **Review** | `reviews` | Inbox items: `balance_checkin` and `subscription_review`. |
| **Import key** | `entries.import_key` | Set on entries confirmed or added by a CSV import: a fingerprint of the bank row, so importing the same rows again does nothing. |

## Files

| File | What it does |
|---|---|
| `schedule.py` | Which dates a rule falls on. Monthly schedules count from the start date, so the 31st never drifts. Pure functions, easy to test. |
| `ledger.py` | `post_due()` writes expected entries up to today (idempotent). `project()` computes future dates on the fly (never stored). `balance()`, `cashflow()`, `confirm_occurrence()`. |
| `reviews.py` | `generate()` opens due reviews (idempotent). `open_checkin()` ("check balance now"), `resolve_checkin()`, `resolve_subscription()`, `dismiss()`. |
| `csv_import.py` | CSV import: reads the file (in memory only), guesses columns and the date format, matches rows to expected entries, applies the plan. |
| `api.py` | HTTP endpoints under `/api`. Money is integer cents in and out. |

## How a day works
1. The first API request each day runs `post_due(today)` and `generate(today)` (see `deps.py`).
2. Every rule date up to today becomes an `expected` entry once, thanks to a unique index on `(rule_id, occurrence_date, account_id)`.
3. Future dates are projected live, so **editing a rule changes the future and never rewrites the past.**

## CSV import
`POST /api/import/preview` shows what a file would do and changes nothing. `POST /api/import/apply` recomputes the same plan from the same file and applies it, minus `skip_rows`. The browser never says which entry to change.

| Row becomes | When | Apply does |
|---|---|---|
| `match` | Same amount as a known entry on this account within `DATE_WINDOW_DAYS` (4) | Confirms it, at the bank's date. If it was already marked paid by hand, it's linked instead of added again. |
| `match_changed` | A rule's entry within 25% (`CLOSE_AMOUNT`), e.g. a utility bill | Confirms it at the real amount |
| `new` | Nothing expected it | Adds a confirmed one-off entry |
| `duplicate` | Its `import_key` is already in the ledger | Nothing |
| `before_start` | On or before the account's opening date (already in the opening balance) | Nothing |
| `error` | Unreadable date or amount | Nothing |

Exact matches are claimed before close ones. Candidates include future rule dates, so a bill paid a few days early is matched and isn't posted again on its due date. Two identical rows in one file (two $5 coffees) get different keys.

**A bank's CSV doesn't import right:** add its header names to `_HEADERS` or its date format to `DATE_FORMATS` in `csv_import.py` (and the frontend's `DATE_FORMATS` in `ImportPage.tsx`), then add a test to `tests/test_csv_import.py` with a few fictional rows in that bank's layout.

## Common changes

**New frequency (e.g. "every 4 weeks")**
1. Add it to `FREQUENCIES` (and `_DAY_STEPS` or `_MONTH_STEPS`) in `schedule.py`.
2. Add it to the `CHECK` constraint in a **new** migration. SQLite can't alter a CHECK, so this one needs a table rebuild migration. Ask for review if unsure.
3. Add a label in `frontend/src/lib/format.ts` → `FREQUENCY_LABELS`.
4. Add a test in `tests/test_schedule.py`.

**New account type**
Same pattern: the `kind` CHECK constraint (new migration), `AccountKind` in `api.py`, `frontend/src/lib/types.ts` and `ACCOUNT_KIND_LABELS`.

**Change review defaults**
Check-in intervals are per account (`checkin_every_days`). Subscription review cadence is per rule (`review_every_months`). The UI defaults are in `frontend/src/pages/AccountsPage.tsx` (`DEFAULT_CHECKIN`) and `RuleForm.tsx`.

## Tests
`tests/test_schedule.py` (dates), `tests/test_budget_api.py` (end-to-end through the API, moving the `clock`) and `tests/test_csv_import.py`.
