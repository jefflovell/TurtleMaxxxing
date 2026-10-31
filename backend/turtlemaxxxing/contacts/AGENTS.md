# Contacts module guide

People your tasks are about ("Mr. Anderson → Smith Agency") and where to find them. M3's quick capture uses these to fill in *who* and *where*.

## Concepts

| Concept | Table | Notes |
|---|---|---|
| **Contact** | `contacts` | `name` (required), `organization`, `role`, `email`, `phone`, `location` ("where you meet them"), `notes`, `private`. Empty fields are `''`, not `NULL`. |
| **Contact label** | `contact_labels` | Contacts share the task labels, so `work` and the auto-Private `private` label mean the same thing everywhere. |
| **People on a task** | `task_contacts` | Many to many. Deleting a contact or a task removes the link; the other side stays. |

## 🔒 Privacy (same rule as tasks)

A contact is Private if `contacts.private` is set **or** it has a label with `auto_private`. This uses **`tasks.service.is_private()`**, the one rule for both. Never write a second version of it.

- Every contact carries `is_private`, and so does each person listed on a task (`task.contacts[].is_private`).
- **A Private person on a shareable task must still be withheld** from AI (M3). The task's own `is_private` doesn't cover the people on it.
- Tests: `test_contacts_follow_the_same_private_rule_as_tasks` and `test_tasks_list_their_people_with_each_persons_privacy` in `tests/test_contacts_api.py`.

## Files

| File | What it does |
|---|---|
| `api.py` | `/api/contacts` (list with `q` and `label_id` filters, get with the contact's tasks, create, update, delete). |
| `../tasks/service.py` | `contacts_by_task()` builds the short people list on each task; `labels_for()` reads labels for tasks or contacts. |
| `../tasks/api.py` | `contact_ids` on task create and update. |

## Behaviors worth knowing
- The list is sorted by organization, then name. People with no organization come last.
- `q` matches name, organization, role or location. **Task search** (`/api/tasks?q=`) also matches the names and organizations of a task's people.
- Email is lightly checked (has an `@`, no spaces). Phone is free text.
- Like everything else in the app, contacts are labels and notes only: no attachments, file paths or links into work systems (PLAN.md §3).

## Common changes

**Add a field** (e.g. "birthday"): new migration with `ALTER TABLE contacts ADD COLUMN ... NOT NULL DEFAULT ''`, then `ContactIn` / `ContactPatch` and the insert in `api.py`, `Contact` in `frontend/src/lib/types.ts`, and the editor in `frontend/src/pages/ContactsPage.tsx`. Add a test.

**Show another field in the short people list on tasks:** add it in `contacts_by_task()` and `ContactSummary` in `types.ts`.

## Tests
`tests/test_contacts_api.py`, `tests/test_migrations.py` (upgrade from v3), and `tests/test_privacy.py` (contacts in the no-network check).
