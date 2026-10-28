# The app won't start

**Symptoms:** running `uv run --directory backend turtlemaxxxing` shows an error, closes right away, or http://turtle.localhost:8765 says it can't connect.

> Your address may differ if you changed it at setup. The app prints its address when it starts, and it's saved in `%LOCALAPPDATA%\TurtleMaxxxing\settings.json`.

Run these from the TurtleMaxxxing folder, in PowerShell.

## 1. Are the tools installed?
```powershell
uv --version
python --version
node --version
```
- **"not recognized"** for `uv` → install it from https://docs.astral.sh/uv/ and open a new terminal.
- `python` missing is OK, because `uv` can provide Python itself.
- `node` is only needed to *build* the UI (see [blank-or-old-page.md](blank-or-old-page.md)).

## 2. Are the dependencies installed?
```powershell
uv sync --directory backend
```
✅ It finishes without errors. ❌ Network errors here are normal if you're offline; reconnect and retry.

## 3. Is something else using the port?
If the app says **"Port 8765 is already in use"**:
- TurtleMaxxxing may already be running in another window. Try the address it printed, and close the extra copy.
- If another program owns the port, let TurtleMaxxxing pick a new one and remember it:
  ```powershell
  uv run --directory backend turtlemaxxxing --find-port
  ```
  It prints your new address. Update your bookmark if you have one.

To see what's using a port:
```powershell
Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
```

## 4. Read the actual error
```powershell
uv run --directory backend turtlemaxxxing
```
| Error mentions | Meaning | Fix |
|---|---|---|
| `ModuleNotFoundError` | Dependencies are missing | Step 2 |
| `address already in use` / `10048` | Port taken | Step 3 |
| `database is locked` | Another copy is running | Close the other copy |
| `migrat...` or `sqlite3.OperationalError` | A database update failed | [restore-and-undo.md](restore-and-undo.md). A backup was taken automatically. |
| `PermissionError` on the data folder | Windows blocked the folder | Check `%LOCALAPPDATA%\TurtleMaxxxing` exists and you own it |
| `hostname must be 'localhost' or end in '.localhost'` | `settings.json` has an invalid name | Run `uv run --directory backend turtlemaxxxing --hostname turtle.localhost` |
| The page says **"Unknown host"** | You opened it by a name it doesn't answer to | Use the address the app printed at startup |

## 5. Verify
```powershell
uv run --directory backend pytest -q
```
✅ All tests pass, the app starts, and `<your address>/api/health` (e.g. http://turtle.localhost:8765/api/health) shows `"ok": true`.
