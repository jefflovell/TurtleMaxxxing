# Install TurtleMaxxxing 🐢

**Free, no programming, and no paid accounts.** You don't need a GitHub account or a Claude account to install or use TurtleMaxxxing. It takes about 10 minutes, mostly waiting on downloads.

Use your **personal** Windows 10 or 11 computer, never a work computer.

## 1. Download

1. Go to the **[latest release](https://github.com/jefflovell/TurtleMaxxxing/releases/latest)**.
2. Under **Assets**, click **TurtleMaxxxing-*version*.zip** to download it. (Ignore the `.sha256` file; that's a fingerprint the updater uses.)

## 2. Unzip

1. Open your **Downloads** folder.
2. Right-click the ZIP → **Extract All…** → **Extract**.

That's just a temporary copy. The installer puts the app in its own folder, outside Downloads, so you can delete these files afterwards.

## 3. Run the installer

1. In the unzipped **TurtleMaxxxing** folder, double-click **Install TurtleMaxxxing** (it may show as `Install TurtleMaxxxing.cmd`).
2. If Windows shows **"Windows protected your PC"**, click **More info** → **Run anyway**.
   - *Why:* Windows warns about any download that isn't signed with a paid certificate, which most free open-source apps aren't. You can read exactly what the installer does in `scripts\setup.ps1` before running it.
3. A window opens and walks you through it. It asks:
   - **Where to install.** The suggested folder, `C:\Users\<you>\Apps\TurtleMaxxxing`, is fine.
   - **Whether to install uv**, if you don't have it. uv is a free, open-source tool that sets up Python for the app. Say **Y**. Windows may ask for permission; that's Windows asking you, and it's your choice.
   - **What to call the app's address.** Press Enter for `turtle.localhost`, or type something like `i-like-turtles.localhost`.
   - **Which browser you use for personal things.** Not the one you use for work.
4. It installs everything, **runs the built-in privacy tests**, and shows the results. Every test must pass. If any fail, it stops and tells you; please [report it](#get-help).
5. When it says **All done!**, TurtleMaxxxing opens in your browser.

### What the installer does and doesn't do
- ✅ **Creates** the app folder, three Start-menu shortcuts, and your data folder (`%LOCALAPPDATA%\TurtleMaxxxing`).
- ✅ **Downloads** uv (only if you say yes) and the app's Python parts, from their official sources.
- ❌ **Never** needs administrator rights, asks for passwords, changes system settings, or looks through your files.

## Every day

| To… | Do this |
|---|---|
| **Start** | Press the **Windows key**, type **I like turtles**, press **Enter** |
| **Stop** | Close the small minimized **TurtleMaxxxing** window on your taskbar |
| **Update** | Start menu → **TurtleMaxxxing** → **Update TurtleMaxxxing** |
| **Check that everything's OK** | Start menu → **TurtleMaxxxing** → **Check my TurtleMaxxxing install** |

**Updating** downloads the newest release from GitHub and checks it against its published SHA-256 fingerprint. It then swaps the new version in, re-runs the tests, and restarts the app. **If anything fails, it puts your previous version back automatically.** Your data is never touched, because it lives in its own folder, not the app's.

The updater is the only part of TurtleMaxxxing that goes on the internet, and only when you run it. The app itself never does.

## Get help

1. Run **Check my TurtleMaxxxing install** from the Start menu. It makes a short report and copies it to your clipboard.
   - The report has **no data from the app**: no accounts, amounts, tasks or contacts. Your user name is replaced with `<you>`.
2. Then either:
   - **Fix it yourself:** follow the matching [troubleshooting guide](troubleshooting/README.md), or
   - **Ask a free Claude chat:** paste the [help prompt](HELP_PROMPT.md) and your report into [claude.ai](https://claude.ai). Claude tells you what to try, one step at a time, and you do the clicking.
3. Found a bug? [Open an issue](https://github.com/jefflovell/TurtleMaxxxing/issues) (needs a free GitHub account) and include the report.

## Uninstall

1. Delete the app folder (`C:\Users\<you>\Apps\TurtleMaxxxing`), plus `TurtleMaxxxing.previous` next to it if it's there.
2. Delete the shortcuts: Start menu → right-click **I like turtles** → **Open file location**, then delete **I like turtles** and the **TurtleMaxxxing** folder.
3. **Only if you also want your data gone:** delete `%LOCALAPPDATA%\TurtleMaxxxing` (paste that into File Explorer's address bar). This can't be undone.

uv can stay. Other apps may use it, and it's harmless.

## Manual steps, if something's missing

**"winget is not available."** winget comes with Windows' **App Installer**. Open the **Microsoft Store**, search for **App Installer**, and install or update it. Then run the installer again.

**uv installed but "this window can't see it yet."** Close the installer window and double-click **Install TurtleMaxxxing** again. New tools only show up in new windows.

**Something else stopped the installer?** It never leaves things half-done outside its own folder. Run **Install TurtleMaxxxing** again, or delete the half-made app folder and start over. Your data folder isn't touched.

## Other ways to install
- **Have a paid Claude plan with Claude Code?** The [one-paste setup prompt](SETUP_PROMPT.md) has Claude do all of this for you and explain each step.
- **Technical?** See [Install by hand](../README.md#install-by-hand-for-the-technical) in the README.
- **Mac or Linux?** The app runs there, but this installer is Windows-only for now. Use the by-hand steps.
