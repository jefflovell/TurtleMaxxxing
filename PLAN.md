# TurtleMaxxxing — Project Plan 🐢

A **free, open-source, local-first personal assistant and project manager**. It's for keeping work and personal life separate in a world where everything blurs together, with AI help *only* where you allow it.

**Privacy and security first:**
- **Runs locally.** Your data lives on your machine, in a database you own.
- **Nothing in the cloud in our code.** No accounts, no telemetry, no servers of ours. The app only talks to services *you* connect.
- **You choose the connectors and the AI.** Use your own Claude, a fully local model, or another provider. AI only ever sees what you allow.
- **Easy setup.** Clear docs, plus a one-paste setup prompt for an AI coding assistant.

Our first user is a friend of the project, and their needs drive version 1.

Status: **planned**. All initial questions are answered (§9). Next up: M0.

---

## 1. First user (anonymized persona)

- New to AI tools, reasonably techy, on **Windows**, uses the **Claude desktop app**.
- Has work material that **must never touch AI**, and wants AI help with everything else.
- Already keeps work and personal apart (separate browsers and profiles), and wants the assistant to respect that boundary.
- Wants a **visual, GUI-first** assistant with **manual control**: AI suggests and drafts, and the user approves. No silent automation.

## 2. Requirements

| # | Requirement | Priority |
|---|---|---|
| R1 | Monthly budgeting: bills, income, due dates, and a **cash-flow-over-the-month** visual | **P1** |
| R2 | "Pay this bill on this date" view (a bills calendar with paid/unpaid tracking) | P1 |
| R2a | **Recurring rules with splits** (e.g. a paycheck divided into HSA, 401(k), 529s...) that auto-update balances, plus periodic accuracy check-ins and "still paying for this?" subscription reviews (§2a) | P1 |
| R3 | **Tasks and reminders** with kanban status (To Do / In Progress / Blocked / Done), user-defined labels with favorites, reminders, and list / board / Today / calendar views (§2b) | P2 |
| R4 | Calendar: see appointments alongside tasks and bills | P2 |
| R5 | AI assistant: summarize, draft, plan, answer, and *propose* changes the user approves | P2 |
| R6 | Research workspace: summarize public documents (e.g. building codes, standards, regulations) and check notes against them | P3 |
| R7 | Read-only financial awareness from alerts and statements, **without logging in to banks** | P3 |
| R8 | Phone access to the app | P4 |
| R9 | **Hard separation:** work files never enter the app, and anything marked Private never reaches AI | **Non-negotiable** |

## 2a. Budget model: a manual starter that becomes automatic

**What makes this better than a spreadsheet:** you describe your money's *rules* once, and the app keeps the ledger moving on its own. Then it checks in now and then so it doesn't drift from reality. Tracking every expense by hand is a pain, so we don't make you do it, and no bank logins are needed.

### Building blocks

- **Accounts and buckets:** anywhere money lives or goes, e.g. checking, HSA, 401(k), brokerage, a kid's 529, a savings goal. Each one has a running balance.
- **Recurring rules:** "this amount moves on this schedule."
  - **Income with splits:** a pay date and schedule (weekly, biweekly, semi-monthly, monthly), an amount, and how it's divided. For example, every other Friday:

    | Split | Amount |
    |---|---|
    | HSA | $127.39 |
    | 401(k) | $322.58 |
    | Brokerage | $25.00 |
    | Kid A 529 | $50.00 |
    | Kid B 529 | $50.00 |
    | Remainder → Checking | *(auto-calculated)* |

  - **Bills:** rent, utilities, loans, each with a due date.
  - **Subscriptions:** streaming, apps, memberships, each with a renewal date and cadence.
- **Auto-posting:** on each scheduled date, the app posts the *expected* entries automatically and updates every affected balance. Nothing needs entering by hand.

### Staying accurate without the busywork

- **Expected vs confirmed:** auto-posted entries start as *expected* (shown lighter). The user confirms them with one click, edits them ("this paycheck was $40 short"), or lets CSV import confirm them by matching.
- **Balance check-ins:** on a schedule the user picks (e.g. monthly per account), the app asks "your HSA should be about $4,312. What does it actually say?" Entering the real number creates a labeled **adjustment**, so drift never piles up.
- **"Are you still paying for this?":** monthly or quarterly, each subscription asks for a review, with buttons for keep, cancel (stop the rule) and change price. This is where forgotten subscriptions get caught.
- **Rule reviews:** when something changes, e.g. a raise or a new contribution amount, you edit the rule once, and future dates update while past entries stay as they were.
- **Review inbox:** all check-ins land in one place (the same inbox the AI proposals use), so reviewing is a two-minute weekly habit, not a chore. It never nags with pop-ups.

### Where AI helps later (optional, through the AI gate)
- "Set up my paycheck: $2,450 every other Friday, $127.39 to HSA..." → a proposed rule to approve.
- Spotting likely subscriptions in an imported CSV → proposed rules.
- A monthly plain-English summary: "You spent $63 more on subscriptions than last quarter."

## 2b. Tasks and reminders: more than a calendar

Tasks and reminders are a first-class part of the app, not just calendar entries. Every task carries a **status** and any number of **labels**, so you can tell at a glance what's on fire, what's stuck and what's done.

### Status (kanban)

| Default status | Meaning |
|---|---|
| **To Do** | Not started |
| **In Progress** | Being worked on |
| **Blocked** | Waiting on someone or something; can hold an optional "blocked by" note |
| **Done** | Finished, and hidden from default views after a while (configurable) |

The defaults ship as above. Renaming and adding statuses can come later if UAT asks for it.

### Labels: user-defined, with favorites

- **Users create their own labels**, each with a name, color and optional emoji. Example starters: `critical`, `urgent`, `important`, `work`, `wife`, `kids`, `home`, `money`. A task can have any number of labels.
- **Favorites:** star the labels you use most. Favorites show up as one-click chips when creating or editing a task, appear first in filters, and are what quick capture tries first. Everything else sits behind a "more labels" search.
- **Labels can carry behavior (optional):** e.g. a label set to **auto-Private**, so anything tagged with it is hidden from AI automatically. This ties labels to the security model.
- **Starter labels and colors are just defaults** to tune during QA/UAT.

### Reminders
- Any task can have a due date and time and one or more reminders (e.g. "1 day before" or "at 9am").
- Reminders show as in-app notifications (desktop notifications later, and on the phone in M5). They can **optionally** also push to the chosen personal calendar.

### Views (same tasks, different lenses)
- **List:** sort and filter by status, label, due date or favorite labels, e.g. "everything `urgent` that isn't Done".
- **Board:** kanban columns by status, with drag-and-drop between columns.
- **Today / Upcoming:** overdue, today, and the next 7 days. This is the default home screen.
- **Calendar:** tasks with due dates alongside events and bills.
- **Saved filters:** e.g. "Work, Blocked" or "Critical this week", pinned in the sidebar.

### Quick capture understands this
*"New reminder: call the plumber Thursday, urgent, home"* → a proposed task (due Thu, labels `urgent` + `home`, status To Do) to approve. Unknown labels are suggested, never created silently.

## 3. Security model (the most important section)

### Zones

| Zone | What lives there | AI access |
|---|---|---|
| 🐢 **Shell** | Personal tasks, budget, calendar, public reference docs, notes, **and work reminders as plain-text labels** ("Review Smith St proposal by noon Fri") | ✅ Allowed, gated and logged |
| 🔒 **Private** | Any item the user flags Private | ❌ Hidden from every AI path |
| 🚫 **Never in the app** | Work files, file paths, network paths, links into work systems | ❌ Not stored at all |

### Principles

1. **Separate by structure, not by filtering.** ✅ *Decided:* work files **never enter the app**. Work items are text labels only, with no attachments, file paths or network links.
2. **Labels are AI-visible by default.** Anything typed or dictated into a normal item may go to the AI, so labels should hold only what the user would be comfortable telling it. Anything more sensitive gets the 🔒 **Private** flag, and Private items are never returned by the AI gate or the MCP tools.
3. **Block file types at the door.** A user-configurable blocklist (e.g. CAD formats like `.dwg .dxf .rvt`) stops sensitive file types from being attached by accident.
4. **One AI gate.** Every call that sends data to *any* AI provider goes through one module that drops Private items and writes an **audit log** the user can read in the UI, including which provider got what.
5. **Approve before write.** The AI can propose a task, bill or event, and nothing is saved until the user clicks approve.
6. **Read-only integrations.** Email, calendars and statements are read-only (except writing user-approved events to one chosen calendar). No bank logins and no aggregators such as Plaid.
7. **No network by default.** A fresh install makes zero outbound connections until the user turns on a connector or an AI provider.

### Threats to design around (and test)

- **AI computer use / screen control** (e.g. Claude Desktop computer use) can see the *whole screen*, including work windows. → `SECURITY.md` recommends keeping it off, or using a separate OS user account for work.
- **AI browser extensions** (e.g. Claude in Chrome) see the browser they're installed in. → Install them only in a dedicated personal browser profile, and test that work browsers and profiles aren't visible.
- **AI apps with filesystem access** could read the app's database directly, Private items included. → Keep the app data folder **outside** any folder shared with an AI tool. Optional database encryption is in the parking lot.
- **Too much detail in a label**, e.g. a dictated reminder that names a sensitive client. → The user's judgment plus the Private flag. `SECURITY.md` gets a plain-language rule of thumb.
- **Pasting work files straight into an AI app** is outside our control. → Covered by `SECURITY.md` guidance; the app can't police other apps.
- **Employer policy:** users with regulated work should check what's allowed on a personal device. The app can enforce separation, but it can't make a disallowed setup allowed.

## 4. Architecture

```
 ┌──── Your personal computer (localhost only) ──────┐
 │                                                   │
 │  Browser UI (web app)  ◄──►  Local API server     │
 │   list / board /             (Python, FastAPI)    │
 │   calendar / budget              │                │
 │                                  ├── SQLite        │
 │                                  │   (Private items│
 │                                  │    never pass   │
 │                                  │    the AI gate) │
 │                          ┌───────┴──────┐         │
 │                          │   AI gate    │ ◄── audit log
 │                          └───┬──────┬───┘         │
 │   Claude Desktop / any ◄─ MCP │      │ AI provider │
 │   MCP-capable client   server │      │ adapters    │
 │                               │      ├─► Ollama (fully local)
 └───────────────────────────────┼──────┼────────────┘
                                 ▼      ▼
                    Only what you allow, to the provider you chose
   Phone ──Tailscale──► same web UI
```

**Key choices:**
- **Local web app** (Python FastAPI backend, SQLite, browser frontend). Cross-platform, with Windows as the first target. A web UI on `localhost` gives us phone access through Tailscale almost for free, with no app store.
- **SQLite is the source of truth.** Google Sheets or Drive can be **export** targets, never the database.
- **Frontend: React** (Vite + TypeScript) for the best UX: drag-and-drop boards, calendars and rich charts. The setup prompt hides the Node toolchain from users.

### AI: bring your own model

The app is **model-agnostic**. Two ways in, both behind the same AI gate:

1. **MCP server (first).** The app exposes its tools over MCP, so the user's own AI client drives it: Claude Desktop, Claude Code, or any other MCP-capable client. The user keeps their existing subscription, and we hold no API keys.
2. **In-app assistant (later).** A chat panel with pluggable provider adapters:

| Provider type | Examples | Where data goes |
|---|---|---|
| **Fully local** | Ollama (Llama, Qwen, Mistral, DeepSeek and Kimi open weights, ...) | **Nowhere.** Stays on the machine. |
| **Anthropic** | Claude | Anthropic |
| **OpenAI-compatible APIs** | ChatGPT/OpenAI, DeepSeek, Kimi (Moonshot), OpenRouter, ... | That provider |

- The settings screen shows **where data goes and which jurisdiction** each provider is in, so users choose with their eyes open.
- Provider choice can be per-feature, e.g. a local model for the budget and Claude for research.
- API keys live in the OS keychain, never in the repo, `.env` files or chat.

## 5. Integrations (user-chosen, read-only by default)

| Integration | Approach | Notes |
|---|---|---|
| Calendars | Provider-agnostic, see §5a | Writes approved events to one chosen calendar |
| Gmail (and other email later) | Read-only API scope, limited to labels like `Bills` | Bill alerts → suggested bills the user approves |
| Statements / alerts | Parse alert emails, plus manual **CSV/OFX** drop-in import | No bank logins |
| Google Drive / Sheets | Optional export target | Not the database |
| Phone | Tailscale to the home computer, opening the same web UI as a PWA | M5 |

## 5a. Calendars: support whatever the user has

**Goal:** never assume one calendar. One `CalendarProvider` interface, a few adapters, and the user picks which calendars are connected and which one approved events go to.

**Use case:** jot down personal and after-hours items, like a weekend appointment or "look up that spec Saturday", and they land on your personal calendar so your phone reminds you. Work calendars are never connected.

### Coverage

There's no reliable current market-share data for calendars, so this is ranked by platform reach: the calendars that ship with each OS, then the major alternatives.

| # | Calendar | Ships with | Adapter | Auth | Notes |
|---|---|---|---|---|---|
| 1 | Google Calendar | Android, Gmail | **Google Calendar API** | OAuth | Biggest platform. Also covers Samsung users who sync via Google. |
| 2 | Apple iCloud Calendar | iOS, macOS | **CalDAV** | App-specific password | |
| 3 | Outlook.com / Microsoft 365 | Windows (Outlook) | **Microsoft Graph** | OAuth | Personal Outlook.com accounts by default. Work and school accounts get a warning. |
| 4 | Samsung Calendar | Samsung Android | via Google, or local-only | none | Samsung Cloud has no public calendar API that we found. |
| 5 | Yahoo / AOL Calendar | — | **CalDAV** | App password | CalDAV support is vendor-reported; verify. |
| 6 | Fastmail | — | **CalDAV** | App password | Good CalDAV support. |
| 7 | Zoho Calendar | — | **CalDAV** | App password | Verify. |
| 8 | Nextcloud (self-hosted) | — | **CalDAV** | App password | A natural fit for FOSS and privacy-minded users. |
| 9 | Proton Calendar | — | **.ics** import/export only | none | No CalDAV because of end-to-end encryption. |
| 10 | Any .ics feed (holidays, sports, school) | — | **ICS (read-only)** | none | Universal fallback. |

**Build order:** ICS read-only (simplest, covers everyone for viewing) → Google → CalDAV (covers iCloud plus five more) → Microsoft Graph.

### Rules
- **Write only to the one calendar the user picks**, and only after they approve each event.
- **Credentials never touch AI or the repo.** OAuth tokens and app passwords are entered in the app's own settings screen and stored in the OS keychain (via Python `keyring`), never in chat, `.env` files or SQLite.
- **Work-account guard:** connecting a Microsoft work/school or Google Workspace account shows a warning and requires an explicit "this is personal" confirmation.
- Calendar event text goes through the same AI gate as everything else, so Private events stay hidden from AI.

## 6. Inspiration

| Project | What we borrow |
|---|---|
| **ClickUp** | Organization and UI: spaces, lists, and list/board/calendar views |
| **Cloaked** | A privacy-first mindset: the user controls what each service sees |
| **Tailscale** | Secure private access from your phone with no exposed ports |
| **Obsidian** | Local-first: your data is yours, on your disk |
| **Actual Budget** | Open-source, local-first budgeting done well |
| **Home Assistant** | Local-first with opt-in integrations, plus a strong open-source community |
| **Ollama** | Running models fully locally |

## 7. Milestones

**M0 — Guardrails and decisions** *(no app code)*
- ✅ Answer the open questions.
- ✅ Write [`docs/SECURITY.md`](docs/SECURITY.md) (zones, the sticky-note test for what's OK to tell an AI, data flows, habits, vulnerability reporting).
- ✅ Write the [separation test](docs/testing/SEPARATION_TEST.md): canary-based checks T1–T4 now (browser extension, other profiles, computer use, file access), with T5–T10 added as milestones land.
- ⬜ First user runs T1–T4 on their personal PC and records the results locally.
- ⬜ Turn on GitHub private vulnerability reporting for the repo (repo owner, in Settings → Security).

**M1 — App shell + budget (P1)** 🎯
- ✅ FastAPI, SQLite and the web UI running on `localhost`.
- ✅ Accounts and buckets with running balances.
- ✅ Recurring rules: income with splits, bills, subscriptions (§2a).
- ✅ Auto-posting of expected entries, with confirm.
- ✅ Monthly cash-flow chart: running balance across the month, bills marked on their dates.
- ✅ "Pay on this date" bills calendar with mark-paid.
- ✅ Review inbox: balance check-ins (scheduled, plus "check balance now") and "still paying for this?" subscription reviews.
- ✅ `AGENTS.md`, module guides, the `turtle-help` skill (troubleshoot, change, update, undo) and the first troubleshooting guides (§8a).
- ✅ Automated tests, including **T5 no network by default** (`backend/tests/test_privacy.py`).
- ➡️ **Moved to M2:** CSV import that matches transactions to expected entries. ✅ Done in M2b.
- ✅ First version of [`docs/SETUP_PROMPT.md`](docs/SETUP_PROMPT.md), plus the "I like turtles" Start-menu shortcut (`scripts/start-turtle.ps1`). Dry-run on the dev machine: fresh clone → install → tests → port scan → start script → shortcut.
- ⬜ Run the setup prompt end to end on a clean Windows user account (a real `winget` install and a real browser launch), ideally the first user's own PC.
- ✅ Public CI on every push: [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
- ⬜ First-user UAT: enter real bills and paychecks, use it for a couple of weeks, and collect feedback.

**M2 — Tasks, reminders and projects** (§2b)

*M2a, done:*
- ✅ Tasks with kanban status (To Do / In Progress / Blocked / Done), due dates and times, and reminders (in-app pop-ups with snooze).
- ✅ User-defined labels (name, color, emoji) with ⭐ favorites, plus auto-Private labels.
- ✅ Views: Today / Upcoming (home screen), list with status, label and search filters, and a kanban board with drag-and-drop.
- ✅ Lists for grouping tasks into projects (plus an Inbox).
- ✅ 🔒 Private flag, with one tested rule (`is_private`) for M3's AI gate to use.

*M2b, done:*
- ✅ Tasks on the calendar view, alongside bills (each can be shown or hidden). Click a day to add a task on it.
- ✅ Saved filters pinned in the sidebar (list, statuses, labels, search and list/board view).
- ✅ CSV import (moved from M1): matches bank or card rows to expected entries (exact amounts, or close amounts for bills that vary), adds the rest, skips anything already imported. Preview first; the file is never stored.

*M2c, next:*
- Contacts list (e.g. "Mr. Anderson → Smith Agency") so the AI can fill in who and where for appointments.

**M3 — AI via MCP**
- MCP server tools: read tasks, bills, calendar and contacts; *propose* new items.
- **Quick capture**, the headline use case. The user says or types: *"New reminder: review Smith St proposal by noon Friday, client meeting the following Monday at Smith Agency."* The AI proposes a task (due Fri 12:00) and a calendar event (Mon, with Mr. Anderson pulled from contacts), and the user approves both.
- AI gate, file-type blocklist and audit-log page.
- Approval inbox for AI proposals.
- Tests proving Private items and blocked file types can't reach any MCP tool.

**M4 — Connectors**
- Calendars, in the §5a build order.
- Gmail bill alerts → suggested bills, read-only.
- Sheets export.

**M5 — Phone**
- Tailscale and a PWA install, plus a mobile-friendly layout.

**M6 — In-app assistant + model choice**
- Chat panel with provider adapters: Ollama first (fully local), then Anthropic and OpenAI-compatible APIs.
- Per-feature provider choice and a "where your data goes" display.

**M7 — Research workspace**
- Upload *public* documents (codes, standards, regulations), have the AI summarize them, and build checklists that check notes against a standard.

**Parking lot** *(future, only if wanted)*
- Sending calendar invites to others.
- Rich contact cards.
- A text-only outline of a work file structure, for reference.
- Optional at-rest encryption of the database.
- More email providers.

## 8. Setup documentation (a deliverable, not an afterthought)

Every user should get this like a piece of custom software: clear docs plus a **one-paste setup prompt** for an AI coding assistant (Claude Code first).

**Deliverables:**
- `docs/SETUP_NOTES.md`: a **running log** we add to as we build. Every dependency, config value, account, port, folder and manual step goes here the moment we introduce it.
- `docs/INSTALL.md`: the polished, human-readable install and configuration guide, written from the notes.
- `docs/SETUP_PROMPT.md`: a prompt the user pastes into Claude Code. It:
  - checks prerequisites (Python, Git, Node if needed) and **asks before installing anything**,
  - clones the repo, installs dependencies and creates the app data folder **outside** any folder shared with AI tools,
  - registers the MCP server with the user's AI client,
  - walks the user through the steps that need a human (OAuth consent, app passwords, Tailscale sign-in) in the app's own settings screen, and **never asks for passwords or keys in chat**,
  - runs a self-check (app starts, MCP connects, and a test proves Private items are unreachable),
  - finishes with a short "how to use it" tour.
- `docs/SECURITY.md`: zones and rules in plain language.

**The setup prompt has guardrails too:** it tells the AI to stay inside the install folder, never open or search Documents, Downloads or any work folder, and stop and ask whenever something is unexpected.

**Rule while building:** any change that adds a dependency, setting, credential, port or manual step **also updates `docs/SETUP_NOTES.md` in the same commit.** (Written down for future AI sessions in `CLAUDE.md`.)

**When:** notes start now. `SETUP_PROMPT.md` gets a first version at the end of M1 and is re-tested on a clean Windows user account at every milestone.

## 8a. Self-serve maintenance: agent-readable everything

**Goal:** users can troubleshoot, update and tinker with their own install by chatting with an AI agent. Coding knowledge stays optional, and the project author is never on the hook for one-on-one support.

### Docs written for agents as much as humans
- **`AGENTS.md` at the root** (plus `CLAUDE.md`, which points to it): the project map, the rules (security model, no PII, no network by default), and how to run, test and change things. `AGENTS.md` is a cross-tool convention, so it works with any agent, not just Claude.
- **A short agent guide in each module folder** (`backend/budget/`, `backend/mcp/`, `frontend/...`): what the module does, its key files, how to change common things, and what not to touch.
- **Docs stay current by rule:** a change to a module updates its guide in the same commit, just like the setup notes.

### A bundled Claude skill (`.claude/skills/turtle-help/`)
Loads automatically when the user opens the repo in Claude Code, and knows how to:
- **Troubleshoot:** "the app won't start", "calendar stopped syncing", "MCP isn't connecting" → runs the matching diagnostic guide.
- **Change things safely:** "add a field to bills", "change the colors" → finds the right module guide, makes the change, runs the tests.
- **Update:** pull the latest version, migrate the database, re-run the setup self-check.
- **Undo:** "put it back how it was" → a git-based rollback, explained in plain language.

### Executable troubleshooting guides (`docs/troubleshooting/`)
- One file per problem, written as **steps an agent can run**: symptoms → checks (commands) → fixes → how to verify.
- Each one also reads fine for a human, and doubles as a prompt you can paste into any AI chat.

### Low stakes by design
- **Tests as a safety net:** a fast test suite, including the **Private-items-never-reach-AI tests**, runs after every agent change. The skill won't call a change done until the tests pass.
- **Easy rollback:** git under the hood, with "undo" as a first-class skill action.
- **Backups:** automatic local database backups before updates and migrations.
- **Chattable help (later):** the in-app assistant (M6) can answer "how do I...?" from these same docs.

## 9. Open questions

- ~~**Q1. Which machine?**~~ ✅ **Personal computers only.** The app is never meant to be installed on work hardware. The remaining risk is work material *arriving on* the personal machine, which the "never in the app" rules, the computer-use guidance and the M0 separation test cover.
- ~~**Q2. Do work files go in the app?**~~ ✅ **No.** Work items are plain-text labels only, and a 🔒 Private flag covers sensitive ones.
- ~~**Q3. Which calendars?**~~ ✅ **Whichever the user has** (§5a). Approved events go to one chosen personal calendar, and work calendars are never connected.
- ~~**Q8. Personal details in the repo?**~~ ✅ **None.** The first user is an anonymized persona, and there's no PII anywhere in the repo.
- ~~**Q4. First AI path?**~~ ✅ **MCP first (M3).** Users drive the app from their own Claude Desktop, Claude Code or another MCP client. The in-app chat with model choice comes in M6.
- ~~**Q5. Budget data?**~~ ✅ **Manual starter that becomes automatic, plus CSV import** (§2a). Recurring rules with splits auto-post expected entries, check-ins keep them accurate, and CSV import confirms actuals. No bank logins.
- ~~**Q6. Who builds and maintains it?**~~ ✅ **The project author builds it, and users maintain their own install with an AI agent's help** (§8a). React for UX. Contributors: we'll cross that bridge when we get there.
- ~~**Q7. License?**~~ ✅ **MIT.** See `LICENSE`.
