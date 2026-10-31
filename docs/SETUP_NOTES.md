# Setup Notes (running log)

Raw notes for building `INSTALL.md` and `SETUP_PROMPT.md`. Add an entry **whenever** something new is needed to install, configure or run TurtleMaxxxing. Newest entries at the bottom.

**Fields per entry:** what it is · why it's needed · how to install/configure · how to verify · any security note.

---

## Install paths (from M2.5)

| Path | Needs | Doc |
|---|---|---|
| **Double-click installer** (main path) | A personal Windows 10/11 PC. The installer offers to install **uv** via winget; Python comes through uv. No Node.js, no Git, no accounts. | [INSTALL.md](INSTALL.md) |
| One-paste Claude Code prompt (optional) | A paid Claude plan (Claude Code), plus Git, uv and Node.js (installed by Claude via winget) | [SETUP_PROMPT.md](SETUP_PROMPT.md) |
| By hand | Git, uv, Node.js | [README](../README.md#install-by-hand-for-the-technical) |

## Target environment

- **Machine:** a personal computer, never a work computer. Windows is the first target.
- **AI:** Claude Desktop through MCP for the first user, and Claude Code for setup. Other MCP clients and providers come later.
- **Browsers:** any AI browser extension goes only in a dedicated personal browser profile. Work browsers and profiles get no AI extensions.

## Prerequisites (so far)

| Item | Why | Verify | Notes |
|---|---|---|---|
| Git | Clone and update the repo | `git --version` | |
| uv | Installs Python (if needed) and the backend's dependencies, and runs the app | `uv --version` | Developed with 0.13.6. One installer, no separate Python install needed. |
| Python ≥ 3.12 | Runs the backend | `uv run python --version` | Provided by uv if missing. Developed on 3.15. |
| Node.js (LTS) | Builds the React frontend | `node --version` | Developed on v24. Only needed to build the UI, not to run the app. |

## Install and run (M1)

From the repo root:

| Step | Command | Verify |
|---|---|---|
| Backend dependencies | `uv sync --directory backend` | No errors; creates `backend/.venv` |
| Frontend dependencies | `npm install --prefix frontend` | No errors |
| Build the UI | `npm run build --prefix frontend` | Ends with `built in ...`; creates `frontend/dist` |
| Start | `uv run --directory backend turtlemaxxxing` | Prints the turtle; http://127.0.0.1:8765 loads |
| Self-check | `uv run --directory backend pytest -q` | All tests pass, including `test_privacy.py` (no network) |

## Runtime facts

| Thing | Value | Override |
|---|---|---|
| Address | `http://turtle.localhost:8765`, bound to `127.0.0.1` only | `settings.json` in the data folder (`--find-port`, `--hostname`), or `TURTLE_PORT` / `TURTLE_HOSTNAME`. The bind address is fixed. |
| Data folder | `%LOCALAPPDATA%\TurtleMaxxxing` (Windows), `~/.local/share/turtlemaxxxing` (others) | `TURTLE_DATA_DIR` |
| Database | `<data folder>\turtle.db` (SQLite, one file = all your data) | — |
| Backups | `<data folder>\backups\`, written automatically before each migration | — |
| Lockfiles | `backend/uv.lock`, `frontend/package-lock.json`, committed so installs are reproducible | — |

## Friendly address ("I like turtles")

The setup prompt should:
1. Run `uv run --directory backend turtlemaxxxing --find-port`, which scans 8765–8799 (skipping common dev ports) and saves the first free one.
2. Offer a custom name, e.g. `--hostname i-like-turtles.localhost`. It must end in `.localhost`: browsers send those to this computer with **no hosts-file edit and no admin rights**, and the app refuses anything else.
3. Create a browser **bookmark named "I like turtles 🐢"** pointing to the saved address. Typing "I like turtles" in the address bar then suggests it. *(Chrome and Edge match bookmark titles; it shows as a suggestion, and isn't guaranteed to be the top pick over a web search.)*
4. Create a **Start-menu shortcut named "I like turtles"** that starts the app and opens the address. Typing "I like turtles" in Windows search then launches it reliably.

Not done, on purpose:
- **Editing the hosts file** for a bare name like `turtles/`: needs admin rights and changes a system file. Not worth the risk for a nicer URL.
- **Port 80** (to drop `:8765`): often taken (IIS and other tools), and grabbing it silently would surprise people.
- **Hijacking address-bar search** for the exact phrase: needs a browser extension or a search-engine change. Out of scope.

## Day-to-day start and stop
- **Start:** the Start-menu shortcut **"I like turtles"** runs `scripts/start-turtle.ps1 -Browser <personal browser>`. It reads the address from `settings.json`, starts the app in a minimized window if it isn't already running (checked via `127.0.0.1:<port>/api/health`), then opens the address in the chosen browser. Icon: `assets/turtle.ico`.
- **Stop:** close the minimized "TurtleMaxxxing" window.
- `-ExecutionPolicy Bypass` in the shortcut applies only to that one script run. No machine setting changes.
- The browser is chosen explicitly so the app never opens in the work browser by accident, even if that's the system default.

## Not yet decided
- Start at login: off for now. Could be added as an opt-in later.
- Whether to ship a prebuilt `frontend/dist` so users don't need Node at all.
- A `docs/INSTALL.md` human-only guide. For now the README's "Try it by hand" plus `SETUP_PROMPT.md` cover it.

## Repo

- GitHub: https://github.com/jefflovell/TurtleMaxxxing (public, so no GitHub login is needed to clone)

## Security setup steps (verified by [the separation test](testing/SEPARATION_TEST.md); user guide in [SECURITY.md](SECURITY.md))

- [ ] Computer use / screen control is **off** in AI apps on this machine.
- [ ] AI browser extensions are installed only in a dedicated personal browser profile.
- [ ] Work browsers and profiles have no AI extensions.
- [ ] The app data folder is outside any folder shared with AI tools.

## Log

- **2026-10-28:** Repo created. No runtime dependencies yet beyond Python (for `hello.py`).
- **2026-10-28:** M0 security docs added. The setup prompt should end by pointing the user to `docs/SECURITY.md` and running separation tests T1–T4. The planned app data folder is `%LOCALAPPDATA%\TurtleMaxxxing` (to confirm in M1). It must stay outside any AI tool's shared folders.
- **2026-10-28 (M1):**
  - Backend added: FastAPI, uvicorn, SQLite, managed with uv. Data folder confirmed as `%LOCALAPPDATA%\TurtleMaxxxing`.
  - Frontend added: React 19, Vite, TypeScript and Recharts. The backend serves `frontend/dist`, so the UI must be built once after install and after each update.
  - Note: FastAPI pulls in `opentelemetry-api`. That's the API only, with no exporter, so it sends nothing; `test_privacy.py` confirms there are no outbound connections.
  - The `turtle-help` skill and `docs/troubleshooting/` are added. The setup prompt should mention both at the end ("if anything goes wrong, open this folder in Claude Code and say *help*").
  - Friendly address `turtle.localhost`, `settings.json`, `--find-port` / `--hostname` / `--demo` added. A host and origin guard protects against malicious websites (DNS rebinding, CSRF).
  - The testing SOP is published at `docs/TESTING.md`. The setup prompt's self-check should run the full test suite and name the privacy tests in its summary.
  - **M2a (tasks):** no new dependencies or setup steps. Migration 0002 adds the task tables and starter labels, and existing installs upgrade automatically with a backup first. Reminders only pop up while the app is open in a browser tab; desktop notifications come later.
  - **M2b (calendar tasks, saved filters, CSV import):** no new dependencies or setup steps. Migration 0003 adds `saved_filters` and `entries.import_key`, and existing installs upgrade automatically with a backup first. CSV files are read in memory and never saved; the user downloads them from their bank's website themselves (no bank logins). The "Bills calendar" page is now just "Calendar" (under Plan).
  - **M2c (contacts):** no new dependencies or setup steps. Migration 0004 adds `contacts`, `contact_labels` and `task_contacts`, and existing installs upgrade automatically with a backup first.
  - **M2.5 (free setup):** Claude Code needs a paid plan, so the main install path no longer uses it.
    - `Install TurtleMaxxxing.cmd` runs `scripts/setup.ps1`: checks for uv (offers `winget install --id astral-sh.uv`), copies the app to `%USERPROFILE%\Apps\TurtleMaxxxing` (warns about Documents, Desktop, Downloads and OneDrive), `uv sync --locked`, runs the privacy tests then the full suite, `--find-port`, an optional `--hostname`, the browser choice, and three Start-menu shortcuts (`I like turtles`, plus `TurtleMaxxxing\Update TurtleMaxxxing` and `TurtleMaxxxing\Check my TurtleMaxxxing install`).
    - Release ZIPs (`.github/workflows/release.yml`, built by `scripts/build-bundle.ps1`) include `frontend/dist` and a `VERSION` file, so Node.js isn't needed.
    - `scripts/update.ps1`: GitHub's latest-release API → download → SHA-256 check → stop the app → rename to `<install>.previous` → copy → `uv sync` → tests → **roll back on failure** → restart. Git installs: `git pull --ff-only`, rebuild, re-test. The updater is the only part that connects to the internet, and only when run.
    - `scripts/check-install.ps1`: a privacy-safe report (no database reads; the user name is replaced with `<you>`), copied to the clipboard; pairs with `docs/HELP_PROMPT.md` for a free Claude chat.
    - Verified on the dev machine with a temp data folder and Start menu: install (46 s, skipped a busy 8765), start, check, update over the running app, and rollback of a deliberately broken 9.9.9. CI repeats this on every push. **Not yet run:** a real winget install of uv, the SmartScreen prompt, a real Start menu, a download from a published release, a clean Windows account.
  - `docs/SETUP_PROMPT.md` v1 written. Prerequisites via winget (verified IDs: `Git.Git`, `astral-sh.uv`, `OpenJS.NodeJS.LTS`). Dry-run on the dev machine from a fresh clone: install, build, 63 tests, `--find-port` (correctly skipped a busy 8765), start script (start + already-running paths), shortcut creation. **Not yet run:** a real winget install, the browser-launch path, a clean Windows account.
