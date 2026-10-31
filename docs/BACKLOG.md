# QA / UAT Backlog 🐢📝

Revision requests from testing: bugs, things that work but should work differently, and small features people ask for while using the app. The long-term roadmap lives in [PLAN.md](../PLAN.md); this file is for feedback on what's already built.

**To add an item,** tell Claude Code something like *"backlog: on my phone the calendar is hard to read (from first-user)"*. The `backlog` skill fills in the ID, date, milestone, categories, complexity and the rest, then shows you what it chose so you can correct it. You can also edit this file by hand; `backend/tests/test_backlog.py` checks the format in CI.

> 🔒 **This repo is public.** Requesters are listed by **alias only** (see [Requesters](#requesters)), never real names. Describe what the *app* did, never the tester's own data: no real amounts, payees, accounts, employers, addresses or screenshots of real data. Rewrite it with fictional examples ("a $120 electric bill").

---

## Open

| ID | Title | Category | Priority | Status | Complexity | Milestone | Requested | Requester |
|---|---|---|---|---|---|---|---|---|
| QA-001 | Calendar pills are cramped and cut off at phone width | ui, ux | P2 | triaged | S | M2b | 2026-10-31 | qa-agent |
| QA-002 | Reminder pop-ups cover the page at phone width | ui, ux | P2 | triaged | S | M2a | 2026-10-31 | qa-agent |
| QA-003 | Naming a new list or saved filter uses the browser's plain pop-up box | ux, design, extension | P3 | triaged | S | M2b | 2026-10-31 | qa-agent |
| QA-004 | No keyboard or touch way to reorder cards on the board | accessibility, extension | P3 | triaged | M | M2a | 2026-10-28 | qa-agent |
| QA-005 | Review the starter label set with the first user | design | P3 | new | XS | M2a | 2026-10-28 | maintainer |

## Closed

| ID | Title | Status | Requested | Closed | Fixed in |
|---|---|---|---|---|---|

---

## Details

### QA-001 Calendar pills are cramped and cut off at phone width
- **Found in:** `72bdd93` (M2b)
- **Environment:** demo data, 375px wide, dark mode
- **Actual:** each day cell shows pills truncated to a couple of characters, so bills and tasks can't be told apart without tapping.
- **Expected:** readable at a glance, e.g. a dot or count per day on phones, with the day's items listed below the grid when you tap it.
- **Extends:** Calendar
- **Privacy impact:** none
- **Target:** M5 (mobile-friendly layout) unless UAT says sooner

### QA-002 Reminder pop-ups cover the page at phone width
- **Found in:** `72bdd93` (M2b walkthrough; the pop-ups shipped in M2a)
- **Environment:** demo data, 375px wide
- **Actual:** the reminder pop-up sits over the middle of the calendar until it's acted on.
- **Expected:** on narrow screens it docks at the bottom edge, or collapses to a small 🔔 badge that expands on tap.
- **Extends:** Reminders
- **Privacy impact:** none
- **Target:** M5

### QA-003 Naming a new list or saved filter uses the browser's plain pop-up box
- **Found in:** `72bdd93`
- **Environment:** any browser
- **Actual:** "+ New list" and "⭐ Save filter" ask for a name in the browser's built-in prompt box, which can't take an emoji picker, looks out of place and is easy to dismiss by accident.
- **Expected:** a small in-app dialog with name and emoji fields, like the label editor.
- **Extends:** Lists, Saved filters
- **Privacy impact:** none

### QA-004 No keyboard or touch way to reorder cards on the board
- **Found in:** `1395f7e` (M2a)
- **Environment:** keyboard only, or a touch screen
- **Actual:** cards can be moved between columns from the task editor's Status field, but their order within a column can only be changed by mouse drag-and-drop.
- **Expected:** "Move up / Move down" in the task editor or the card's menu, and touch dragging on phones.
- **Extends:** Board view
- **Privacy impact:** none
- **Notes:** drag-and-drop is also only tested by hand (TESTING.md §8).

### QA-005 Review the starter label set with the first user
- **Found in:** planning (M2a requirements)
- **Actual:** new installs start with critical, urgent, important, work, home, family, money and private.
- **Expected:** a set that fits how the first user actually sorts things, decided during UAT. Changes ship as a new migration for new installs only; existing installs keep their own labels.
- **Extends:** Labels
- **Privacy impact:** none. Keep `private` as an auto-Private starter.
- **Notes:** from planning: "we can muck about with specific labels in QA / UAT."

---

## How items are filled in

The skill (or a person editing by hand) follows these rules, so items stay comparable.

### Fields at a glance

| Field | Where | Meaning |
|---|---|---|
| **ID** | table | `QA-` plus the next free three-digit number. Never reused, even after an item closes. |
| **Title** | table | What's wrong or wanted, in plain words, from the user's point of view. |
| **Category** | table | One or more from the list below, comma-separated. |
| **Priority** | table | P0 to P3 (below). |
| **Status** | table | Where it is in the workflow (below). |
| **Complexity** | table | XS to XL estimate (below). |
| **Milestone** | table | The milestone that **originally built the feature** this item is about (map below), or `new` for a request with no existing feature. |
| **Requested** | table | The date it was **first** asked for, as `YYYY-MM-DD`. If someone asks again later, add them under *Also requested by*; the date doesn't change. |
| **Requester** | table | Alias of whoever asked first. |
| **Found in** | details | The commit or milestone where it was seen (`git log -1 --format=%h`). |
| **Environment** | details | Where it happens: phone width, dark mode, browser, demo or real data (never the data itself). |
| **Actual / Expected** | details | What happens now and what should happen. Bugs also get **Steps** to reproduce. |
| **Severity** | details, bugs only | `blocker` (can't use the app or lose data), `major` (a feature is wrong), `minor` (works with a workaround), `cosmetic`. |
| **Extends** | details | The existing feature (or `QA-` item) this builds on, for `extension` items. |
| **Privacy impact** | details | `none`, or `review` if it touches the Private rule, AI paths, the network, `security.py` or what data is stored. `review` items get a security pass before they ship. |
| **Target** | details | The milestone it's planned for, once planned. |
| **Also requested by** | details | Other aliases who asked for the same thing, with dates. A rough vote count. |
| **Fixed in / Regression test / Verified** | details | Filled when closing: the commit, the test that proves it (bugs always get one, per [TESTING.md](TESTING.md) rule 5), and who confirmed it in the app and when. |

### Categories
`bug` (worked wrong) · `ux` (how it feels to use: flow, wording, clicks) · `ui` (how it looks: layout, spacing, colors) · `design` (a product decision to make, e.g. defaults) · `extension` (builds on an existing feature; name it under **Extends**) · `feature` (something new) · `accessibility` · `performance` · `data` (calculations, imports, balances) · `storage` (database, backups, migrations) · `auth` (sign-ins, connector credentials) · `privacy` (what AI or the network can see) · `setup` (install, start-up, updates) · `docs` · `ai` · `integration` (calendars, email, other services).

### Priority
| | Means | Example |
|---|---|---|
| **P0** | Fix now. Data loss, wrong money math, a privacy leak, or the app won't start. | A Private task shows up in an AI tool. |
| **P1** | Next up. Hurts everyday use. | Imported rows land on the wrong account. |
| **P2** | Should do soon. A real annoyance with a workaround. | Hard to read on a phone. |
| **P3** | Nice to have. | A prettier dialog. |

Anything with **Privacy impact: review** that could leak data is P0 regardless of how small it looks.

### Status
`new` → `triaged` (fields checked, priority set) → `planned` (has a Target) → `in-progress` → `ready-to-verify` (shipped; waiting on the requester) → `verified` (the requester confirmed it in the app). Or `wont-do` / `duplicate` (with a reason or the other ID in Notes). The last three move the row to **Closed**.

### Complexity (estimate)
| | Rough size |
|---|---|
| **XS** | Under an hour. Wording, a color, one small file. |
| **S** | A few files on one side (frontend *or* backend), no database change. |
| **M** | Frontend and backend, or a migration, plus new tests. |
| **L** | A new page or module, a migration with UI, or anything with **Privacy impact: review**. |
| **XL** | Spans milestones, adds a dependency or changes the architecture. Split it into smaller items. |

Bump one size up for anything touching money calculations or the security guard.

### Milestone map (what built which feature)
| Area | Milestone |
|---|---|
| Security guide, separation test | M0 |
| App shell, accounts, money rules and splits, auto-posting, cash flow, review inbox, setup prompt, start shortcut, friendly address, CI | M1 |
| Tasks, labels and favorites, lists and Inbox, reminders, Today screen, list and board views, Private flag | M2a |
| Calendar (tasks and bills), saved filters, CSV import | M2b |
| Contacts | M2c |
| AI via MCP, quick capture, AI gate, audit log, approval inbox | M3 |
| Calendar and email connectors, Sheets export | M4 |
| Phone access, mobile layout | M5 |
| In-app chat, model choice | M6 |
| Research workspace | M7 |

When a milestone ships, add its areas here.

## Requesters

Aliases only. The mapping from alias to real person is **never** written in this repo.

| Alias | Who |
|---|---|
| `maintainer` | The project's maintainer |
| `first-user` | The project's first user (the persona in PLAN.md §1) |
| `qa-agent` | An AI agent doing a QA walkthrough (TESTING.md §5) |

New tester? Add a neutral alias here first (`tester-2`, a GitHub handle they chose, or `community` for public issues), then use it.
