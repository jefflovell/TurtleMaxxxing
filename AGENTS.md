# AGENTS.md: guide for AI agents working on TurtleMaxxxing

You're helping someone run, fix, update or change their own TurtleMaxxxing install. They may not be a programmer. Explain what you're doing in plain language, keep changes small, and run the tests before you call anything done.

## What this is

A free, open-source, **local-first** personal assistant and project manager. M1 (current) is **budgeting**: accounts, recurring money rules with paycheck splits, auto-posted ledger entries, a cash-flow chart, a bills calendar, and a review inbox. See `PLAN.md` for the roadmap.

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
| `backend/turtlemaxxxing/budget/` | Budget logic: schedules, ledger, reviews, API | [budget/AGENTS.md](backend/turtlemaxxxing/budget/AGENTS.md) |
| `frontend/` | React + TypeScript UI (Vite) | [frontend/AGENTS.md](frontend/AGENTS.md) |
| `docs/` | Security guide, testing SOP, setup prompt and notes, troubleshooting | — |
| `scripts/start-turtle.ps1` | What the "I like turtles" shortcut runs: starts the app if needed, then opens the browser | — |
| `docs/troubleshooting/` | Step-by-step fixes an agent can run | [index](docs/troubleshooting/README.md) |
| `.claude/skills/turtle-help/` | Claude Code skill: troubleshoot, change, update, undo | — |

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
| Develop the UI with live reload | Start the app, then `npm run dev --prefix frontend` and open http://127.0.0.1:5173 |

**Definition of done for any change:** the checklist in [docs/TESTING.md §6](docs/TESTING.md#6-definition-of-done-any-change-any-author).

## Where things live at runtime

- **Data:** `%LOCALAPPDATA%\TurtleMaxxxing\turtle.db` (SQLite). Override with `TURTLE_DATA_DIR`.
- **Backups:** `%LOCALAPPDATA%\TurtleMaxxxing\backups\`, written automatically before each database migration.
- **Address:** `http://turtle.localhost:8765` by default (also `127.0.0.1:8765`). Saved in `<data folder>\settings.json`, with `TURTLE_PORT` / `TURTLE_HOSTNAME` overrides. The server only binds `127.0.0.1` and only answers to its own host names (`backend/turtlemaxxxing/security.py`).
