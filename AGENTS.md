# AGENTS.md: guide for AI agents working on TurtleMaxxxing

You're helping someone run, fix, update or change their own TurtleMaxxxing install. They may not be a programmer. Explain what you're doing in plain language, keep changes small, and run the tests before you call anything done.

## What this is

A free, open-source, **local-first** personal assistant and project manager. Built so far:
- **Tasks (M2a):** kanban status, user-defined labels with favorites and auto-Private, lists, reminders, a Today home screen, list and board views.
- **M2b:** a calendar with tasks and bills together, saved filters pinned in the sidebar, and CSV import that matches bank rows to expected entries.
- **M2c:** contacts (who and where), linked to tasks, with the same Private rule.
- **Budgeting (M1):** accounts, recurring money rules with paycheck splits, auto-posted ledger entries, a cash-flow chart, a review inbox.

See `PLAN.md` for the roadmap.

## Rules you must follow

1. **Privacy first.** The app makes **no outbound network connections**: no telemetry, no analytics, no CDN fonts, no remote APIs. Only `127.0.0.1`. `backend/tests/test_privacy.py` enforces this. Never weaken it.
2. **Never read the user's data folder** (`%LOCALAPPDATA%\TurtleMaxxxing` on Windows) unless they ask you to for a specific problem, and never copy its contents into chat, files or commits.
3. **Work files never enter the app**, and items flagged Private must never reach any AI path. See `PLAN.md` §3 and `docs/SECURITY.md`.
4. **Public repo:** never commit personal data, real names, credentials or tokens.
5. **Docs stay current:** if you change a module, update its `AGENTS.md`. If you add a dependency, setting, port or manual step, update `docs/SETUP_NOTES.md`. Do both in the same commit.
6. **Back up before risky changes.** Database migrations back up automatically. For anything else, commit or stash first so "undo" is easy.
7. **Follow the testing SOP: [docs/TESTING.md](docs/TESTING.md).** It's binding. Never weaken a privacy or security test to make a change pass, use fictional data only, add a regression test for every bug, and report results honestly.

## Map

| Path | What it is | Guide |
|---|---|---|
| `backend/` | Python API server (FastAPI + SQLite), managed with `uv` | [backend/AGENTS.md](backend/AGENTS.md) |
| `backend/turtlemaxxxing/budget/` | Budget logic: schedules, ledger, reviews, CSV import, API | [budget/AGENTS.md](backend/turtlemaxxxing/budget/AGENTS.md) |
| `backend/turtlemaxxxing/tasks/` | Tasks, labels, lists, reminders, saved filters, Today view. **Owns the Private rule** (for tasks and contacts). | [tasks/AGENTS.md](backend/turtlemaxxxing/tasks/AGENTS.md) |
| `backend/turtlemaxxxing/contacts/` | Contacts and the people on each task | [contacts/AGENTS.md](backend/turtlemaxxxing/contacts/AGENTS.md) |
| `frontend/` | React + TypeScript UI (Vite) | [frontend/AGENTS.md](frontend/AGENTS.md) |
| `docs/` | Security guide, testing SOP, setup prompt and notes, troubleshooting | — |
| `docs/BACKLOG.md` | QA / UAT revision requests: bugs and change requests from testing, with priority, complexity and status. **Requesters by alias only.** | `.claude/skills/backlog/` |
| `scripts/start-turtle.ps1` | What the "I like turtles" shortcut runs: starts the app if needed, then opens the browser | — |
| `Install TurtleMaxxxing.cmd`, `scripts/setup.ps1` | The free double-click installer (M2.5). Same steps and guardrails as the setup prompt. `-Yes` runs it unattended (CI). | [docs/INSTALL.md](docs/INSTALL.md) |
| `scripts/update.ps1` | "Update TurtleMaxxxing": release installs download, verify, swap and re-test, **rolling back on failure**; Git installs `git pull`. | [docs/INSTALL.md](docs/INSTALL.md) |
| `scripts/check-install.ps1` | "Check my TurtleMaxxxing install": a privacy-safe report for getting help (**never** reads the database) | [docs/HELP_PROMPT.md](docs/HELP_PROMPT.md) |
| `scripts/build-bundle.ps1` | Builds the release ZIP (committed files + built screens + `VERSION`). Used by CI and `.github/workflows/release.yml`. | — |
| `scripts/turtle-common.ps1` | Helpers shared by the scripts above. **Keep these scripts ASCII-only** (Windows PowerShell 5.1 misreads other characters). | — |
| `scripts/make_art.py` | Redraws the README banner and the link-preview card in `assets/` (standard library only) | — |
| `docs/troubleshooting/` | Step-by-step fixes an agent can run | [index](docs/troubleshooting/README.md) |
| `.claude/skills/turtle-help/` | Claude Code skill: troubleshoot, change, update, undo | — |
| `.claude/skills/backlog/` | Claude Code skill: add, triage, work on and close backlog items | — |

## Everyday commands (run from the repo root)

| Task | Command |
|---|---|
| Install or refresh backend dependencies | `uv sync --directory backend` |
| Install or refresh frontend dependencies | `npm install --prefix frontend` |
| Build the UI (required after UI changes) | `npm run build --prefix frontend` |
| Start the app | `uv run --directory backend turtlemaxxxing`, then open http://turtle.localhost:8765 |
| Try it with fictional data (safe for testing) | `uv run --directory backend turtlemaxxxing --demo` |
| Pick a free port and/or friendly name | `uv run --directory backend turtlemaxxxing --find-port --hostname turtle.localhost` |
| Run backend tests | `uv run --directory backend pytest -q` |
| Lint the frontend | `npm run lint --prefix frontend` |
| Type-check and build the frontend | `npm run build --prefix frontend` |
| Check CI for the latest push | `gh run list --limit 3` (or the repo's Actions tab) |
| Build a release ZIP locally (uncommitted changes included) | `powershell -ExecutionPolicy Bypass -File scripts\build-bundle.ps1 -WorkingTree` |
| Try the installer without touching your real install | Set `$env:TURTLE_DATA_DIR` to a temp folder, then run `scripts\setup.ps1 -Yes -NoStart -InstallDir <temp> -StartMenu <temp>` from an unzipped bundle |
| Publish a release (maintainer) | Bump the version in `backend/pyproject.toml` and `backend/turtlemaxxxing/__init__.py`, run `uv lock --directory backend`, commit, then push a tag `vX.Y.Z` |
| Develop the UI with live reload | Start the app, then `npm run dev --prefix frontend` and open http://127.0.0.1:5173 |

**Definition of done for any change:** the checklist in [docs/TESTING.md §6](docs/TESTING.md#6-definition-of-done-any-change-any-author).

## Where things live at runtime

- **Data:** `%LOCALAPPDATA%\TurtleMaxxxing\turtle.db` (SQLite). Override with `TURTLE_DATA_DIR`.
- **Backups:** `%LOCALAPPDATA%\TurtleMaxxxing\backups\`, written automatically before each database migration.
- **Address:** `http://turtle.localhost:8765` by default (also `127.0.0.1:8765`). Saved in `<data folder>\settings.json`, with `TURTLE_PORT` / `TURTLE_HOSTNAME` overrides. The server only binds `127.0.0.1` and only answers to its own host names (`backend/turtlemaxxxing/security.py`).
