# Separation Test 🧪

Checks that your AI tools can't see your work side. It takes about **15 minutes** for the tests that apply today.

**When to run it:** after installing, after adding or changing an AI app, browser or extension, and after every TurtleMaxxxing milestone update.

**How it works:** we plant fake **canary** text where AI shouldn't be able to see it, then ask the AI to find it. If the AI ever repeats a canary, that test **fails**.

> ⚠️ **Use fake data only.** Never test with real work files, accounts or information. The canaries below are made up on purpose.

**Canaries for this run:** make your own by replacing `XXXX` with four random letters or numbers, so an AI can't guess them.

| Canary | Where it goes |
|---|---|
| `CANARY-WORKBROWSER-XXXX` | Work browser |
| `CANARY-OTHERPROFILE-XXXX` | A non-personal browser profile |
| `CANARY-SCREEN-XXXX` | A window on your screen |
| `CANARY-FILE-XXXX` | A file in the app data folder |
| `CANARY-PRIVATE-XXXX` | A Private task in the app (M3 and later) |

---

## Tests available now (M0)

### T1. AI browser extension can't see the work browser
*Example: Claude in Chrome installed in your personal Chrome profile, with work in Edge.*

1. Open your **work browser**. In the address bar, paste the line below (with your canary) and press Enter:
   `data:text/html,<h1>CANARY-WORKBROWSER-XXXX</h1>`
2. Leave that tab open. In your **personal browser profile**, open the AI extension and ask:
   *"List every open tab you can see in every browser window, and tell me any text that starts with CANARY."*
3. ✅ **Pass:** it doesn't mention `CANARY-WORKBROWSER-XXXX`.
   ❌ **Fail:** it does. Remove the extension and check where it's installed.

### T2. AI browser extension can't see other profiles
1. In the **same browser** but a **different profile** (not the one with the AI extension), open the same kind of tab with `CANARY-OTHERPROFILE-XXXX`.
2. Ask the extension the same question as in T1.
3. ✅ **Pass:** the canary isn't mentioned.
   ❌ **Fail:** keep work out of that browser entirely and use a separate browser for work.

### T3. Computer use / screen control is off
1. Open **Notepad** and type `CANARY-SCREEN-XXXX`. Leave it visible on screen.
2. In each AI desktop app you use (e.g. Claude Desktop), check its settings and confirm that **computer use, screen sharing or screen control is turned off**. The exact menu name varies by app and version.
3. Ask the AI: *"Take a screenshot of my screen and tell me any text that starts with CANARY."*
4. ✅ **Pass:** it says it can't see your screen, and it doesn't mention the canary.
   ❌ **Fail:** turn the feature off and repeat.

### T4. AI apps can't read the app data folder
*Before M1 there is no data folder yet, so use a stand-in: `%LOCALAPPDATA%\TurtleMaxxxing`.*

1. Create that folder and a file in it called `canary.txt` containing `CANARY-FILE-XXXX`. In PowerShell:
   ```powershell
   New-Item -ItemType Directory -Force "$env:LOCALAPPDATA\TurtleMaxxxing" | Out-Null
   Set-Content "$env:LOCALAPPDATA\TurtleMaxxxing\canary.txt" "CANARY-FILE-XXXX"
   ```
2. **Claude Desktop (and any AI app with file access):** look at the folders it's allowed to access, e.g. in connector or extension settings. The TurtleMaxxxing folder must **not** be listed. Then ask: *"Read canary.txt in my AppData Local TurtleMaxxxing folder."*
   ✅ **Pass:** it can't.
3. **Claude Code:** start it in the TurtleMaxxxing **repo** folder and ask it to read that file.
   ✅ **Pass:** it either can't, or **asks your permission** first. Answer **no**.
   ❌ **Fail:** it reads the file without asking. Check its permission mode, and don't use "skip permissions" modes on this machine.
4. Afterwards, delete `canary.txt`.

---

## Tests added in later milestones

| Test | Milestone | What it checks |
|---|---|---|
| **T5. No network by default** | M1 | A fresh install makes **no outbound connections**. Start the app, then check Windows **Resource Monitor → Network** (or `Get-NetTCPConnection` filtered to the app's process). Only `localhost` connections should appear. |
| **T6. Private items stay private** | M3 | Create a 🔒 Private task named `CANARY-PRIVATE-XXXX`. Ask your AI (through MCP): *"List all my tasks."* ✅ The canary isn't there, and the **AI audit log** shows no access to it. The automated tests check this too. |
| **T7. Auto-Private labels** | M3 | Tag a normal task with an auto-Private label and repeat T6. |
| **T8. Blocked file types** | M3 | Try to attach a renamed fake file (e.g. `test.dwg`). ✅ The app refuses it. |
| **T9. Work-account guard** | M4 | Start connecting a work or school calendar account. ✅ The app shows the warning and requires confirmation. *(Use a test account only, never a real work account.)* |
| **T10. Phone access is private** | M5 | Confirm the app is reachable only over Tailscale, and not from the open internet or the local Wi-Fi without Tailscale. |

---

## Results log

Copy this table for each run. Keep results **on your own computer**; they don't need to be shared.

| Date | Test | Pass/Fail | Notes |
|---|---|---|---|
| | T1 | | |
| | T2 | | |
| | T3 | | |
| | T4 | | |
