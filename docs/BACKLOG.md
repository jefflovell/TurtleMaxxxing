# QA / UAT Backlog 🐢📝

Revision requests from testing: bugs, things that work but should work differently, and small features people ask for while using the app. The long-term roadmap lives in [PLAN.md](../PLAN.md); this file is for feedback on what's already built.

**To add an item,** tell Claude Code something like *"backlog: on my phone the calendar is hard to read (from first-user)"*. The `backlog` skill fills in the ID, date, milestone, categories, complexity and the rest, then shows you what it chose so you can correct it. You can also edit this file by hand; `backend/tests/test_backlog.py` checks the format in CI.

> 🔒 **This repo is public.** Requesters are listed by **alias only** (see [Requesters](#requesters)), never real names. Describe what the *app* did, never the tester's own data: no real amounts, payees, accounts, employers, addresses or screenshots of real data. Rewrite it with fictional examples ("a $120 electric bill").

---

## Open

| ID | Title | Category | Priority | Status | Complexity | Milestone | Requested | Requester |
|---|---|---|---|---|---|---|---|---|
| QA-001 | Calendar pills are cramped and cut off at phone width | ui, ux | P2 | triaged | S | M2b | 2026-10-31 | qa-agent |
| QA-002 | Reminder pop-ups get in the way until you act on them | ui, ux | P2 | triaged | S | M2a | 2026-10-31 | qa-agent |
| QA-003 | Naming a new list or saved filter uses the browser's plain pop-up box | ux, design, extension | P3 | triaged | S | M2b | 2026-10-31 | qa-agent |
| QA-004 | No keyboard or touch way to reorder cards on the board | accessibility, extension | P3 | triaged | M | M2a | 2026-10-28 | qa-agent |
| QA-005 | Review the starter label set with the first user | design | P3 | new | XS | M2a | 2026-10-28 | maintainer |
| QA-006 | Show each account's next automatic check-in date on the Accounts page | ui, ux, extension | P3 | new | M | M1 | 2026-10-31 | maintainer |
| QA-007 | Rename the Accounts table's "Check-in" column to "Auto check" | ui | P3 | new | XS | M1 | 2026-10-31 | maintainer |
| QA-008 | Let people drag table column edges to change their width | ux, ui, extension | P3 | new | M | M1 | 2026-10-31 | maintainer |
| QA-009 | Make "Check balance" and "Archive" on the Accounts table look like buttons | ui, ux | P3 | new | XS | M1 | 2026-10-31 | maintainer |
| QA-010 | Explore automatic account updates and investment views (balances, alerts, APY, cost basis, year-over-year) | design, feature, extension, integration, auth, privacy, data | P3 | new | L | M1 | 2026-10-31 | maintainer |
| QA-011 | Move explainer text into tooltips; keep inline explanations for the demo only | ux, ui, design | P2 | new | M | M1 | 2026-10-31 | maintainer |
| QA-012 | The one-paste setup prompt only works on Windows | setup, docs, extension | P3 | new | L | M1 | 2026-10-31 | maintainer |
| QA-013 | Grow the "Local only" lock into an in-app security dashboard, with posture notes per section | design, feature, ui, extension, privacy | P2 | new | L | M1 | 2026-10-31 | maintainer |
| QA-014 | Consider a Home dashboard as the start screen instead of Plan › Today | design, ux, feature, extension | P3 | new | M | M2a | 2026-10-31 | maintainer |
| QA-015 | After an update, the browser can keep showing the old version until a hard refresh | bug, setup | P2 | new | S | M1 | 2026-10-31 | qa-agent |

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

### QA-002 Reminder pop-ups get in the way until you act on them
- **Found in:** `72bdd93` (M2b walkthrough; the pop-ups shipped in M2a)
- **Environment:** any screen size. Worst at phone width (375px), where it covers the middle of the calendar.
- **Actual:** a due reminder's pop-up stays on top of the page, covering buttons and content, until you pick Done, 10 min, 1 hour or Dismiss. Seeing it is fine; being forced to act on it just to use the page isn't.
- **Expected:** reminders stay visible without blocking anything, and you never *have* to act on one:
  - It **tucks itself away when you scroll** (the requester's suggestion), or after a few seconds, into a small 🔔 badge with a count in a corner.
  - Click the badge to open the reminders again, with the same Done / snooze / Dismiss buttons.
  - It only pops back open for a **new** reminder, not on every 30-second check.
  - On phones, the badge sits clear of content and buttons.
- **Extends:** Reminders
- **Privacy impact:** none
- **Also requested by:** maintainer, 2026-10-31 ("annoying… in the way of functionality; I don't necessarily want to dismiss or snooze either. Maybe autohide on scroll.")
- **Notes:** frontend only (`ReminderToasts.tsx` and its styles). Screen readers should still hear new reminders. Originally logged as phone-only with Target M5; widened to every screen size, so it's no longer tied to M5.

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

### QA-006 Show each account's next automatic check-in date on the Accounts page
- **Found in:** `ae84cea`
- **Environment:** any
- **Actual:** the Accounts table's Check-in column shows how often ("Every 30 days") and the last check-in date, but not when the next one will appear in the Review inbox. You have to work it out yourself.
- **Expected:** a **Next check-in** column: the date (e.g. "Sat, Nov 28"), "Due now" when one is already waiting in the inbox, or "—" when check-ins are off.
- **Extends:** Accounts, balance check-ins (Review inbox)
- **Privacy impact:** none
- **Notes:** the next date is currently calculated only inside `reviews.generate()` (last check-in, or the opening date, plus the interval). Move that into one helper that both the review generator and the accounts API use, so the column can't disagree with when the check-in actually opens. Add a test that the shown date matches when the review opens. If QA-007 lands first, name this column **Next auto check** to match.

### QA-007 Rename the Accounts table's "Check-in" column to "Auto check"
- **Found in:** `ae84cea`
- **Environment:** any
- **Actual:** the column header reads "Check-in".
- **Expected:** it reads "Auto check", making clear the app schedules it.
- **Extends:** Accounts
- **Privacy impact:** none
- **Notes:** header only (`frontend/src/pages/AccountsPage.tsx`). The Review inbox and the "Check balance now" button keep their names unless asked. Related: QA-006 (its new column would be "Next auto check").

### QA-008 Let people drag table column edges to change their width
- **Found in:** `ae84cea`
- **Environment:** any (mouse or trackpad)
- **Actual:** column widths are fixed by the layout. Long names, like a bank description in the CSV import preview, wrap or squeeze other columns.
- **Expected:** drag the edge of a column header to resize it, with a visible handle and a resize cursor. Widths are remembered per table in this browser (a per-viewer convenience, like the list/board choice). Double-click a handle to reset it.
- **Extends:** all five tables: Accounts, Money rules, Cash flow (M1), Labels (M2a) and the Import CSV preview (M2b). The Milestone column shows the earliest.
- **Privacy impact:** none (only column widths are saved, in the browser).
- **Notes:** build one shared resizable-header piece and use it on all five tables. Keyboard users need a way too, e.g. focus the handle and use the arrow keys. Sized M because it touches every table page and is checked by hand only (no automated frontend tests, TESTING.md §8). At phone width, keep tables scrolling sideways instead.

### QA-009 Make "Check balance" and "Archive" on the Accounts table look like buttons
- **Found in:** `ae84cea`
- **Environment:** any
- **Actual:** each account row's **Check balance** and **Archive** (or **Restore**) are borderless "ghost" buttons, so they read as plain text and don't look clickable.
- **Expected:** they look like buttons: a border and background like the app's other small buttons, with clear spacing between the two.
- **Extends:** Accounts
- **Privacy impact:** none
- **Notes:** style only: drop `ghost` from both in `frontend/src/pages/AccountsPage.tsx`. Worth deciding while there: Archive hides an account, so it could look quieter than Check balance, or ask "Archive Checking?" first.

### QA-010 Explore automatic account updates and investment views (balances, alerts, APY, cost basis, year-over-year)
- **Found in:** `ae84cea`
- **Environment:** n/a (design question)
- **Actual:** account balances move only through money rules, manual entries, check-ins and CSV imports. Accounts have no history views, interest rates or investment details.
- **Expected:** a written design (in PLAN.md) for how accounts could update themselves and what to show, covering:
  - **Automatic updates:** balance changes and transactions arriving without a manual CSV.
  - **Connecting securely:** which connection methods are acceptable, and developing and testing them against providers' **sandbox** environments with fictional data before any real account.
  - **Alerts:** e.g. low balance, unusual charges, a bill that came in higher than expected.
  - **Views:** balance history per account; **APY** and interest earned on savings; **cost basis** and **year-over-year** change on investment accounts. Shown as tables or as groups of charts (e.g. "Kids' 529s", "Retirement").
- **Extends:** Accounts (M1), CSV import (M2b), connectors (M4)
- **Privacy impact:** review. This is a core privacy decision, not a feature tweak:
  - The plan promises **no bank logins** (PLAN.md R7, §3). Any connection is an opt-in connector the user turns on.
  - Credentials stay in Windows Credential Manager, never in the database or chat (SECURITY.md).
  - Network calls exist only while a connector is enabled, and `test_privacy.py` still proves there are none by default.
  - Account data must never reach AI paths it isn't allowed on.
  - Market prices for cost basis and year-over-year views also need a network source, which is a separate decision.
- **Options to compare in the design:**
  - Read-only feeds the user controls with a revocable token (e.g. SimpleFIN-style bridges).
  - Bank aggregators with sandboxes (e.g. Plaid): a third party sees the data.
  - OFX / Direct Connect where banks support it.
  - Parsing bank alert emails (already planned for M4).
  - A watched "drop folder" for downloaded statements: no network at all.
- **Proposed split** (each becomes its own item once the design is agreed):
  1. Balance history chart and table per account, built from the ledger the app already has. **No network**, could ship early (S–M).
  2. Interest rate (APY) on savings accounts, with projected interest added as an expected entry (M).
  3. Account groups ("Kids' 529s") with combined balances and charts (M).
  4. Holdings, lots and cost basis for investment accounts, entered by hand or imported by CSV (L).
  5. Year-over-year change and returns (M, after 4).
  6. Alerts on balances and transactions, in-app only (M).
  7. One opt-in connector, sandbox first (XL; split again when picked).
- **Target:** design before M4 (Connectors). Item 1 could come sooner.
- **Notes:** the requester's "AYPs" is read here as **APY** (annual percentage yield). Confirm when this is triaged.

### QA-011 Move explainer text into tooltips; keep inline explanations for the demo only
- **Found in:** `b09ffca`
- **Environment:** any
- **Actual:** every page opens with a paragraph explaining it ("Describe your paychecks, bills and subscriptions once…"), and several also end with tips or legends ("Tip: no mouse?…", the calendar's icon key, "Changing an amount affects future dates only…"). That's about 20 spots across 10 pages, always visible. Helpful the first time; clutter every day after.
- **Expected:** a consistent explainer design:
  - **Demo (`--demo`):** inline explanations stay, since that's where people learn the app.
  - **Normal use:** pages are clean. Explanations move behind a small ⓘ next to the title or control, shown on hover, focus or tap.
  - A **"Show tips"** setting to turn the inline text back on.
  - **Kept as they are:** empty-state guidance ("No rules yet. Start with your paycheck…"), and trust and safety notes that matter at the moment you act, e.g. "the file is never saved" on Import CSV and the task editor's Private explanation. These can be shorter, not hidden.
- **Extends:** every page's header and help text
- **Privacy impact:** none. The app needs to know whether it's running as the demo; expose that the same way the address is (`/api/health`), and store nothing new.
- **Notes:** tooltips must work with a keyboard and on touch screens, not just mouse hover, and be read by screen readers. Build one shared help piece and use it everywhere so it stays consistent. Sized M: a small backend flag plus every page, checked by hand.

### QA-012 The one-paste setup prompt only works on Windows
- **Found in:** `b09ffca`
- **Environment:** macOS or Linux
- **Actual:** `docs/SETUP_PROMPT.md` assumes Windows throughout: `winget` installs, PowerShell commands, `%LOCALAPPDATA%`, the `scripts/start-turtle.ps1` start script and the Start-menu "I like turtles" shortcut. The app itself already runs on Linux (CI tests it there), but the guided install doesn't.
- **Expected:** the prompt detects the OS and follows matching steps:
  - **macOS:** Homebrew installs, a shell start script, and a Dock / Spotlight launcher.
  - **Linux:** the package manager, a shell start script, and a `.desktop` launcher.
  - Same guardrails everywhere: stay in the install folder, no admin rights, no passwords in chat.
- **Extends:** setup prompt, start script and shortcut (M1)
- **Privacy impact:** none
- **Status note:** logged for later, no action now (requester). Still true after M2.5: the new double-click installer, updater and checker are Windows PowerShell scripts too. Windows is the first target by design (PLAN.md §1), so this waits until someone on macOS or Linux wants it.
- **Notes:** sized L because each OS needs its own start script and launcher, and the prompt has to be run end to end on a real machine of each kind before it's trusted. Same rule as the open M1 item for a clean Windows account.

### QA-013 Grow the "Local only" lock into an in-app security dashboard, with posture notes per section
- **Found in:** `b09ffca`
- **Environment:** any
- **Actual:** the only security signal in the app is the sidebar footer, "🔒 Local only. Your data stays on this computer." The promise is right, but you can't see *why* it's true, and every section looks equally sensitive.
- **Expected:**
  1. **A 🔒 Security page** (the lock links to it) that shows live checks the app can really verify about itself:
     - The server listens only on this computer (`127.0.0.1`).
     - The guard against other websites is on, and lists the addresses it answers to.
     - Network connections: none, or exactly which connectors you turned on (M4).
     - Where your data is stored, with a warning if that folder is inside OneDrive, Dropbox or another synced folder.
     - The last automatic backup and how many backups are kept.
     - AI access: not connected yet; from M3 on, what was shared and when (audit log), and that Private items were withheld.
     - How many items are Private.
     - The app version and when the self-checks last ran, with a **Run checks** button.
  2. **The separation test (T1–T4) as an in-app checklist,** with your results saved on this computer. Today it's a document you follow by hand.
  3. **Posture notes per section.** A small badge or ⓘ on each section explains its policy in a sentence, e.g.:
     - **Money (accounts, rules, imports): sensitive.** "Balances and transactions stay on this computer. Imported files are never saved."
     - **Tasks: normal.** "Shareable with your AI once you connect one, except Private items, which never are."
  4. **Theme treatment:** the lock reflects the overall status with an icon *and* a word ("All checks passed", "1 warning"), never color alone.
- **Extends:** the sidebar's Local-only lock (M1); SECURITY.md and the separation test (M0)
- **Privacy impact:** review. A security page that's wrong is worse than none:
  - It may only show green for something it **actually checked** just now. Anything unchecked says "not checked", never a default pass.
  - The checks themselves must make no network calls (`test_privacy.py` covers the new endpoint).
- **Design question for M3:** should Money be **off-limits to AI by default** (an opt-in per section), rather than following the same rule as tasks? The per-section notes make this visible, and the answer should be decided before AI connects.
- **Proposed split:**
  1. Per-section posture notes, sharing QA-011's ⓘ design (S–M).
  2. The Security page with runtime checks and a Run checks button (L).
  3. The separation test checklist in the app (M).
  4. Per-section AI permissions, as part of M3.
- **Notes:** related to QA-011 (one shared tooltip design) and QA-010 (any account connection would show up here). The automated test suite (`pytest`) stays a developer tool; the page runs its own lightweight checks instead of the test suite.

### QA-014 Consider a Home dashboard as the start screen instead of Plan › Today
- **Found in:** `b09ffca`
- **Environment:** any
- **Actual:** the app always opens on **☀️ Today**, which shows tasks only. Money (bills due, balances, the review inbox) means visiting other pages.
- **Expected (to explore):** a **🏠 Home** screen that summarizes everything at a glance, with each card linking to its page:
  - Today's and overdue tasks, with quick add (what Today shows now, condensed).
  - Bills due in the next 7 days and anything unpaid.
  - This month's cash-flow low point and the checking balance.
  - Review inbox count and due reminders.
  - Security status from QA-013 ("All checks passed").
  - A **Start on** setting (Home / Today / Calendar / any page), remembered on this computer.
- **Extends:** Today home screen (M2a), with cards from Money (M1) and the calendar (M2b)
- **Privacy impact:** none for data flow, since it's all local. But money on the very first screen can be read over your shoulder, so consider a **hide amounts** toggle (show •••• until clicked), on by default for the Home screen.
- **Notes:** "possible", per the requester. Decide during UAT whether Today stays the default. Any charts follow the project's chart rules (color-blind-safe palette, labels not color alone, table view available). Can build on existing endpoints at first (`/api/today`, `/api/calendar`, `/api/cashflow`, `/api/reviews`); add a single summary endpoint only if it's slow. Related: QA-013 (security card), QA-010 (account graph groups could become cards), QA-011 (keep cards free of explainer clutter).

### QA-015 After an update, the browser can keep showing the old version until a hard refresh
- **Found in:** M2c walkthrough (before the M2c commit)
- **Environment:** the browser pane, after rebuilding the UI and restarting the app
- **Severity:** minor (works after Ctrl+Shift+R)
- **Steps:** open the app; rebuild the UI (`npm run build --prefix frontend`) and restart the app; open the address again.
- **Actual:** the browser reused its cached copy of the page, which loaded the previous version's code. The new Contacts page was missing until the page was force-reloaded.
- **Expected:** after an update, the next normal visit shows the new version.
- **Extends:** serving the UI (`backend/turtlemaxxxing/app.py`), the update steps in the `turtle-help` skill
- **Privacy impact:** none
- **Notes:** the fix is to send `Cache-Control: no-cache` for `index.html` (and the page's other non-hashed files). The `assets/` files have content hashes in their names, so they can stay cached. Add a test that `/` comes back with `no-cache`. Until then, `docs/troubleshooting/blank-or-old-page.md` step 2 (Ctrl+Shift+R) covers it.

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
| Contacts, people on tasks | M2c |
| Free setup: installer, updater, "check my install", release bundles | M2.5 |
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
