# Blank page, old version, or "Not Found"

**Symptoms:** http://turtle.localhost:8765 (or your custom address) shows `{"detail":"Not Found"}`, a blank white page, or doesn't show a change you just made.

## 1. Is the UI built?
The backend serves the UI from `frontend/dist`. If that folder is missing, you get "Not Found".
```powershell
Test-Path frontend\dist\index.html
```
❌ `False` → build it:
```powershell
npm install --prefix frontend
npm run build --prefix frontend
```
Then **restart the app** (Ctrl+C in its window, then start it again).

## 2. Old version showing?
After any UI change, rebuild (step 1), restart the app, then refresh the browser with **Ctrl+Shift+R** to skip the cache.

## 3. Blank page?
Open the browser's developer tools (F12) → **Console**.
- Red errors mentioning a file in `assets/` → rebuild (step 1).
- "Can't reach the TurtleMaxxxing backend" in the page → the backend isn't running; see [app-wont-start.md](app-wont-start.md).

## 4. Verify
```powershell
npm run build --prefix frontend
```
✅ It ends with `built in ...` and no errors, and the page loads with the turtle in the sidebar. 🐢
