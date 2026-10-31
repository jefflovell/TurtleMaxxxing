# One-paste setup 🐢

> **No paid Claude plan? You don't need this page.** The free [double-click installer](INSTALL.md) does the same thing. This prompt is an optional extra for people with Claude Code (included in Claude's paid plans).

Install TurtleMaxxxing by pasting one prompt into **Claude Code**. Claude explains each step, asks before installing anything, and checks its own work at the end. It takes about 15–20 minutes, mostly waiting on downloads.

## Before you start
- Use your **personal** Windows computer, never a work computer.
- Have **Claude Code** available: the *Code* tab in the Claude desktop app, or `claude` in a terminal. Start it in your **home folder** (e.g. `C:\Users\<you>`), not in Documents, Downloads or anywhere with work files.
- Leave Claude Code in its normal permission mode, so it asks before running commands. Don't use any "skip permissions" mode for this.
- You'll be asked a few questions: where to install, which browser is your *personal* one, and what to call the app's address.

## What it will do
1. Check for **Git**, **uv** and **Node.js**, and offer to install whatever's missing (using Windows' built-in `winget`; you approve each one).
2. Download TurtleMaxxxing from GitHub into a folder you choose.
3. Install its parts and build the screens.
4. **Run the full test suite**, including the privacy tests, and show you the result.
5. Pick a free local port and your friendly address (default `http://turtle.localhost:8765`).
6. Add an **"I like turtles"** shortcut to your Start menu.
7. Start the app, open it in your personal browser, and give you a quick tour.
8. Offer to walk you through the 15-minute [separation test](testing/SEPARATION_TEST.md).

It **won't** ask for any passwords or keys, look through your files, change system settings, or need administrator rights. (The only exception: if a `winget` install asks Windows for permission, that's Windows asking you, and you decide.)

## The prompt

Copy everything inside the box and paste it into Claude Code:

````text
Please install TurtleMaxxxing for me: a free, open-source, local-first personal assistant
and budgeting app. Repo: https://github.com/jefflovell/TurtleMaxxxing

I'm not a programmer, so explain each step in plain language before you do it, and keep
going one step at a time. Use PowerShell commands (I'm on Windows).

GROUND RULES (follow these the whole time)
- Ask me before installing anything, and before creating anything outside the install folder.
- Stay inside the install folder. Do NOT open, list or search my Documents, Downloads,
  Desktop, OneDrive, or any work-related folder, and do not read my browser data.
- Never ask me for passwords, API keys or tokens, and never ask me to paste one into chat.
- Never use computer use, screenshots of my screen, or browser control.
- Don't change system settings, don't run anything as administrator, and don't edit the
  hosts file.
- Never open or read the app's data folder (%LOCALAPPDATA%\TurtleMaxxxing) except
  settings.json if a step below needs it.
- If anything is unexpected (an error, a prompt you didn't expect, a file that's already
  there), STOP, tell me what you see, and ask what to do.
- Report results honestly. If a test fails, show me the failure; don't hide or skip it.

STEPS
1. Plan: briefly tell me what you're about to do (the steps below) and roughly how long
   it takes. Then ask me:
   a) Where to install. Suggest %USERPROFILE%\Apps\TurtleMaxxxing.
   b) Which browser I use for PERSONAL things (Chrome, Edge, Firefox, or "my default").
      Remind me not to pick the browser I use for work.

2. Prerequisites: check `git --version`, `uv --version` and `node --version`.
   For each one that's missing, tell me what it's for and ask before installing it with:
     git  -> winget install --id Git.Git -e --source winget
     uv   -> winget install --id astral-sh.uv -e --source winget
     node -> winget install --id OpenJS.NodeJS.LTS -e --source winget
   After installing, refresh PATH for this session with:
     $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
   and check the version again. If winget itself is missing, stop and tell me.

3. Download: if the install folder doesn't exist, `git clone` the repo into it. If it
   already exists and is a TurtleMaxxxing checkout, run `git status`. If it's clean,
   `git pull`; if not, stop and ask me. If it exists but is something else, stop and ask.

4. Install and build (from the install folder):
     uv sync --locked --directory backend
     npm ci --prefix frontend
     npm run build --prefix frontend
   Each must finish without errors.

5. Self-check: run `uv run --directory backend pytest -v`. Tell me how many tests passed,
   and call out the privacy and security tests by name (test_privacy.py and
   test_local_security.py) in one plain sentence each, e.g. "the app makes no internet
   connections". Everything must pass before you continue.

6. Address: run `uv run --directory backend turtlemaxxxing --find-port` to pick a free
   local port. Then ask me what I'd like to type to reach the app. Offer
   "turtle.localhost" (the default) and "i-like-turtles.localhost". Explain that it must
   end in ".localhost", which keeps it on my computer. If I pick a different name, run
   `uv run --directory backend turtlemaxxxing --hostname <name>`.
   Tell me my final address.

7. Shortcut: ask if I'd like a Start-menu shortcut called "I like turtles" (typing that in
   Windows search will then start the app). If yes, create it with:
     $repo = '<install folder>'
     $lnk = Join-Path ([Environment]::GetFolderPath('Programs')) 'I like turtles.lnk'
     $s = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
     $s.TargetPath = (Get-Command powershell.exe).Source
     $s.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$repo\scripts\start-turtle.ps1`" -Browser <chrome|edge|firefox|default>"
     $s.WorkingDirectory = $repo
     $s.IconLocation = "$repo\assets\turtle.ico"
     $s.Description = 'Start TurtleMaxxxing'
     $s.Save()
   using my personal browser from step 1. Explain that -ExecutionPolicy Bypass only
   applies to this one script when the shortcut runs, and changes no settings.

8. Start it: run `powershell -NoProfile -ExecutionPolicy Bypass -File "<install folder>\scripts\start-turtle.ps1" -Browser <my choice>`.
   It starts the app in a minimized window and opens my address in my personal browser.
   Tell me:
   - closing the minimized "TurtleMaxxxing" window stops the app,
   - my data is saved on this computer only, in %LOCALAPPDATA%\TurtleMaxxxing,
   - to press Ctrl+D in that browser tab and name the bookmark "I like turtles 🐢".

9. Quick tour (just explain, don't click anything): suggest I start in Accounts (add
   checking, plus any HSA, 401(k), 529 or savings goals), then Money rules (my paycheck
   with its splits, then bills and subscriptions), then Cash flow and the Calendar.
   Mention the Review inbox for balance check-ins and "still paying for this?" reviews.
   Tip: `uv run --directory backend turtlemaxxxing --demo` shows fictional sample data in
   a throwaway folder if I want to explore first (close the real app before trying it).

10. Safety: point me to docs\SECURITY.md (the 5-minute read) and its "sticky-note test".
    Ask if I'd like to do the separation test now (docs\testing\SEPARATION_TEST.md,
    tests T1–T4, about 15 minutes). If yes, guide me step by step. I do the clicking and
    tell you what I see. You never look at my screen or browser.

11. Wrap up with a short summary: install folder, my address, the shortcut, how many tests
    passed, and anything that didn't go to plan. Then tell me: if anything ever goes wrong,
    open the install folder in Claude Code and say "help". The bundled turtle-help skill
    and docs\troubleshooting can fix most problems, update the app, or undo a change.
````

## After setup
- **Start:** type **I like turtles** in Windows search, or use your bookmark.
- **Stop:** close the minimized "TurtleMaxxxing" window.
- **Update:** Start menu → TurtleMaxxxing → **Update TurtleMaxxxing** (it runs `git pull` for an install made this way), or say "update TurtleMaxxxing" in Claude Code.
- **Fix or change something:** open the install folder in Claude Code and say what you want ("the app won't start", "add a field to bills"). See [troubleshooting](troubleshooting/README.md).
- **Uninstall:** delete the install folder, the "I like turtles" Start-menu shortcut, and, if you also want your data gone, `%LOCALAPPDATA%\TurtleMaxxxing`.

## Prefer to do it by hand?
See **Try it** in the [README](../README.md). The commands are the same as steps 4–8 above.
