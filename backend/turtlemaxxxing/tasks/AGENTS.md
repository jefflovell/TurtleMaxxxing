# Tasks module guide

Tasks and reminders from `PLAN.md` §2b: kanban status, user-defined labels with favorites, lists, reminders and the Today view.

## Concepts

| Concept | Table | Notes |
|---|---|---|
| **Task** | `tasks` | `status` is `todo` / `in_progress` / `blocked` / `done`. Optional `due_date` (+ `due_time`), `blocked_note`, `private`. `position` orders cards within a board column. |
| **Label** | `labels` | User-defined, with name (stored lowercase, unique), color, emoji, `favorite`, `auto_private`. Starter labels ship in migration 0002. |
| **List** | `lists` | Groups tasks into projects. Tasks with no list are in the **Inbox**. |
| **Saved filter** | `saved_filters` | A named Tasks-page view pinned in the sidebar. `filters` is JSON: `scope` (`all`, `inbox` or a list id), `statuses`, `label_ids`, `q`, `view`. Labels deleted later are dropped when it's read. |
| **Reminder** | `task_reminders` | `remind_at` in local time (`YYYY-MM-DDTHH:MM`). The UI polls `/api/reminders/due` and shows a pop-up. |

## 🔒 The privacy rule (most important)

A task is **Private** if `tasks.private` is set **or** it has any label with `auto_private`. The single source of truth is `service.is_private()`, exposed on every task as `is_private`.

- **Every AI path (MCP tools in M3, in-app chat in M6) must drop tasks where `is_private` is true.** Never re-implement the rule elsewhere; call `is_private()`.
- Changing a label's `auto_private` immediately changes every task carrying it.
- Tests: `test_private_flag_makes_a_task_private`, `test_auto_private_label_makes_tagged_tasks_private`, `test_turning_on_auto_private_applies_to_existing_tasks`. Never weaken these (see `docs/TESTING.md`).

## Files

| File | What it does |
|---|---|
| `service.py` | `is_private()`, `search()` (filters), `today_view()`, `set_status()` (stamps `completed_at`, clears `blocked_note`), `move()` (board drag-and-drop), `due_reminders()`. |
| `api.py` | Endpoints: `/api/tasks`, `/api/tasks/{id}/move`, `/api/today`, `/api/labels`, `/api/lists`, `/api/filters`, `/api/reminders/...`. |

## Behaviors worth knowing
- **Done tasks fade out** of default views after `DONE_VISIBLE_DAYS` (7). Pass `include_old_done=true` to see them all.
- **Label filters match ANY** of the chosen labels.
- **The calendar** asks for `due_from` / `due_to`. A date range includes done tasks of any age, so past months still show what got finished.
- **Editing reminders** keeps "dismissed" on reminders whose time didn't change.
- A **due time needs a due date**. Clearing the date requires clearing the time too.

## Common changes

**Change the starter labels** for new installs: add a new migration that inserts or updates labels (never edit `0002_tasks.sql`, which has already shipped). Existing users keep their own labels.

**Add a task field** (e.g. "effort"): new migration with `ALTER TABLE tasks ADD COLUMN ...`, then add it to `TaskIn` / `TaskPatch` in `api.py`, `Task` in `frontend/src/lib/types.ts`, and `TaskEditor.tsx`. Add a test.

**Change how long done tasks stay visible:** `DONE_VISIBLE_DAYS` in `service.py`.

## Tests
`tests/test_tasks_api.py` (end to end, moving the `clock` and its time of day; includes saved filters and the calendar range), `tests/test_migrations.py` (upgrades from v1 and v2), and `tests/test_privacy.py` (covers task endpoints in the no-network check).
