# Setup Notes (running log)

Raw notes for building `INSTALL.md` and `SETUP_PROMPT.md`. Add an entry **whenever** something new is needed to install, configure or run TurtleMaxxxing. Newest entries at the bottom.

**Fields per entry:** what it is · why it's needed · how to install/configure · how to verify · any security note.

---

## Target environment

- **Machine:** a personal computer, never a work computer. Windows is the first target.
- **AI:** Claude Desktop through MCP for the first user, and Claude Code for setup. Other MCP clients and providers come later.
- **Browsers:** any AI browser extension goes only in a dedicated personal browser profile. Work browsers and profiles get no AI extensions.

## Prerequisites (so far)

| Item | Why | Verify | Notes |
|---|---|---|---|
| Git | Clone and update the repo | `git --version` | |
| Python 3 | Runs the backend | `python --version` | Exact minimum version gets pinned in M1 |
| Node.js (LTS) | Builds the React frontend | `node --version` | Decided 2026-10-28 (React). Exact version gets pinned in M1 |

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
