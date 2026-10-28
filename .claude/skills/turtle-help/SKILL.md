---
name: turtle-help
description: Help a TurtleMaxxxing user run, troubleshoot, update, change or undo their install. Use when they say the app won't start, shows a blank page, numbers look wrong, want to update to the latest version, want to change something about the app (fields, colors, labels, defaults), or want to put things back how they were.
---

# TurtleMaxxxing help 🐢

The user may not be a programmer. Use plain language, explain each step before you run it, keep changes small, and never call something done until it's verified.

**Always:**
- Read `AGENTS.md` first for the rules and the project map.
- Never read or share the user's budget data (`%LOCALAPPDATA%\TurtleMaxxxing`) unless a troubleshooting step needs it. Say why and ask first.
- Never ask for passwords, tokens or keys in chat.
- Never add network calls, telemetry or non-localhost listeners.
- Follow `docs/TESTING.md`: never weaken privacy or security tests, use `--demo` (fictional data) for manual checks, and report test results honestly.

Pick the matching action below.

## 1. Troubleshoot
1. Ask what they see, or read the error they pasted.
2. Open the matching guide in `docs/troubleshooting/README.md` and work through its steps in order, running the commands and explaining the results.
3. Finish with the guide's **Verify** step. If no guide fits, gather facts (`git status`, test output, the app's error), explain what you found, and propose one fix.

## 2. Change something safely
1. Restate the change in one sentence and confirm it with the user.
2. Make sure the work tree is clean (`git status`). If it isn't, ask whether to commit or stash first, so undo stays easy.
3. Find the right module guide: `backend/AGENTS.md`, `backend/turtlemaxxxing/budget/AGENTS.md` or `frontend/AGENTS.md`. Follow its "Common changes" recipe.
4. Make the smallest change that works. Update that module's `AGENTS.md`, and `docs/SETUP_NOTES.md` if setup changed.
5. Verify, all of these:
   - `uv run --directory backend pytest -q` passes,
   - `npm run build --prefix frontend` passes (if the UI changed),
   - restart the app and have the user look at the change.
6. Offer to commit with a clear message. **Do not push** unless they ask.

## 3. Update to the latest version
1. `git status` must be clean. If they have local changes, ask before doing anything.
2. `git pull`
3. `uv sync --directory backend` and `npm install --prefix frontend`, then `npm run build --prefix frontend`.
4. Ask the user to close the minimized "TurtleMaxxxing" window, then start it again from the "I like turtles" shortcut (or `scripts\start-turtle.ps1`). Database updates run automatically, with a backup taken first.
5. Verify: `uv run --directory backend pytest -q` passes and the app loads. Summarize what's new from `git log --oneline` since the old version.

## 4. Undo
Follow `docs/troubleshooting/restore-and-undo.md`:
- **Code change** → part A (`git restore` for uncommitted changes, `git revert` for commits). Prefer `revert` over `reset` so history is kept.
- **Data problem** → part B (restore `turtle.db` from `backups\`). Always copy the current database first.
Explain in one sentence what was undone, then verify.
