# TurtleMaxxxing

A free, open-source, local-first personal assistant and project manager with a privacy-first, model-agnostic AI layer. See `PLAN.md` for requirements, the security model and milestones.

## Rules

- **Public repo:** never commit personal data, PII, real names, credentials, tokens or real client details. Use anonymized personas and fictional examples.
- **Security model:** work files never enter the app. Work items are plain-text labels only, with no attachments, paths or links. Items flagged Private must never reach any AI code path, MCP tool, provider adapter or prompt. Read `PLAN.md` §3 before touching AI, MCP or file-handling code.
- **No network by default:** the app makes no outbound connections unless the user enabled that connector or AI provider. No telemetry.
- **Setup notes:** any change that adds a dependency, config value, credential, port, folder or manual step must also update `docs/SETUP_NOTES.md` in the same commit. The install docs and the one-paste setup prompt are built from those notes.
- **Agent-readable docs:** users maintain their own installs with an AI agent (`PLAN.md` §8a). A change to a module must update that module's agent guide in the same commit. Keep troubleshooting guides runnable step by step.
- **Stack:** Python (FastAPI, SQLite) backend, React (Vite + TypeScript) frontend.
- **Platforms:** Windows is the first target; keep code cross-platform and instructions Windows-friendly.
