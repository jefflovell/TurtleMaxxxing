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

## Files

| File | What it does |
|---|---|
| `schedule.py` | Which dates a rule falls on. Monthly schedules count from the start date, so the 31st never drifts. Pure functions, easy to test. |
| `ledger.py` | `post_due()` writes expected entries up to today (idempotent). `project()` computes future dates on the fly (never stored). `balance()`, `cashflow()`, `confirm_occurrence()`. |
| `reviews.py` | `generate()` opens due reviews (idempotent). `open_checkin()` ("check balance now"), `resolve_checkin()`, `resolve_subscription()`, `dismiss()`. |
| `api.py` | HTTP endpoints under `/api`. Money is integer cents in and out. |

## How a day works
1. The first API request each day runs `post_due(today)` and `generate(today)` (see `deps.py`).
2. Every rule date up to today becomes an `expected` entry once, thanks to a unique index on `(rule_id, occurrence_date, account_id)`.
3. Future dates are projected live, so **editing a rule changes the future and never rewrites the past.**

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
`tests/test_schedule.py` (dates) and `tests/test_budget_api.py` (end-to-end through the API, moving the `clock`).
