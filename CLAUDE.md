# TurtleMaxxxing

**Read `AGENTS.md` first.** It has the project map, the rules and the everyday commands, for any AI agent. This file adds Claude-specific notes.

A free, open-source, local-first personal assistant and project manager with a privacy-first, model-agnostic AI layer. See `PLAN.md` for requirements, the security model and milestones.

## Rules

- **Public repo:** never commit personal data, PII, real names, credentials, tokens or real client details. Use anonymized personas and fictional examples.
- **Security model:** work files never enter the app. Work items are plain-text labels only, with no attachments, paths or links. Items flagged Private must never reach any AI code path, MCP tool, provider adapter or prompt. Read `PLAN.md` §3 before touching AI, MCP or file-handling code.
- **No network by default:** the app makes no outbound connections unless the user enabled that connector or AI provider. No telemetry. `backend/tests/test_privacy.py` enforces this.
- **Setup notes:** any change that adds a dependency, config value, credential, port, folder or manual step must also update `docs/SETUP_NOTES.md` in the same commit. The install docs and the one-paste setup prompt are built from those notes.
- **Agent-readable docs:** users maintain their own installs with an AI agent (`PLAN.md` §8a). A change to a module must update that module's `AGENTS.md` in the same commit. Keep troubleshooting guides runnable step by step.
- **Stack:** Python (FastAPI, SQLite) backend, React (Vite + TypeScript) frontend.
- **Platforms:** Windows is the first target; keep code cross-platform and instructions Windows-friendly.

- **Testing SOP:** [docs/TESTING.md](docs/TESTING.md) is binding for every session. Never weaken, skip or delete a privacy or security test to get a change through. Fictional data only; never touch the real data folder (use `--demo` for manual testing). Every bug gets a regression test. Report failures and untested areas plainly.

## Claude Code
- The `turtle-help` skill (`.claude/skills/turtle-help/`) covers troubleshoot / change / update / undo for users.
- Done means the [docs/TESTING.md §6](docs/TESTING.md#6-definition-of-done-any-change-any-author) checklist is met.
