# Restore and undo

There are two different kinds of "put it back."

## A. Undo a code change (the app itself)
TurtleMaxxxing's code is tracked by git, so any change can be undone.

**See what changed:**
```powershell
git status
git log --oneline -5
```
**Throw away changes that aren't committed yet** (only affects code, never your budget data):
```powershell
git restore .
```
**Undo the last commit, keeping a record of the undo:**
```powershell
git revert HEAD
```
Then rebuild and restart:
```powershell
uv sync --directory backend
npm run build --prefix frontend
```
✅ Verify: `uv run --directory backend pytest -q` passes and the app starts.

## B. Restore your data (budget database)
Your data lives in `%LOCALAPPDATA%\TurtleMaxxxing\turtle.db`. A backup is saved in `backups\` **automatically before every database update.**

1. **Stop the app** (Ctrl+C in its window).
2. List the backups (newest last):
   ```powershell
   Get-ChildItem "$env:LOCALAPPDATA\TurtleMaxxxing\backups" | Sort-Object LastWriteTime
   ```
3. Keep a copy of the current database, just in case:
   ```powershell
   Copy-Item "$env:LOCALAPPDATA\TurtleMaxxxing\turtle.db" "$env:LOCALAPPDATA\TurtleMaxxxing\turtle-before-restore.db"
   ```
4. Copy the backup you want over the current database:
   ```powershell
   Copy-Item "$env:LOCALAPPDATA\TurtleMaxxxing\backups\<backup file name>" "$env:LOCALAPPDATA\TurtleMaxxxing\turtle.db"
   ```
5. If you restored a backup from *before* a code update, also undo that update (part A). Otherwise the app will just update the database again.
6. Start the app.

✅ Verify: your accounts and rules look like they did before the problem.

**Want your own backup any time?** Stop the app and copy `turtle.db` somewhere safe. That one file is everything.
