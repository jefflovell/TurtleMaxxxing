# TurtleMaxxxing

[![CI](https://github.com/jefflovell/TurtleMaxxxing/actions/workflows/ci.yml/badge.svg)](https://github.com/jefflovell/TurtleMaxxxing/actions/workflows/ci.yml)

<p align="center">
  <img src="assets/turtle-i-like-turtles.png" alt="A pixel-art turtle above the words &quot;I like turtles&quot;">
</p>

A free, open-source, **local-first personal assistant and project manager** that keeps work and personal life separate, with AI help only where you allow it.

- 🏠 **Runs locally.** Your data stays on your machine.
- 🔌 **You choose the connectors and the AI:** your own Claude, a fully local model, or another provider.
- 🔒 **Privacy first.** No accounts, no telemetry, nothing in the cloud in our code.
- ✅ **Tasks and reminders** with kanban status, your own labels (star your favorites), a calendar, and the people each task is about.
- 💸 **Budgeting that runs itself:** describe your paychecks, splits, bills and subscriptions once, and the app keeps the ledger moving. Import your bank's CSV to confirm what actually happened.

🚧 **Status:** early. Budgeting, tasks, the calendar, CSV import and contacts are working. AI help comes next.

## Roadmap

| | Milestone | What you get |
|---|---|---|
| ✅ | **M0: Guardrails** | The [security guide](docs/SECURITY.md) and a [separation test](docs/testing/SEPARATION_TEST.md) to check your AI tools can't see your work stuff |
| ✅ | **M1: App + budget** | Accounts, paychecks with splits, bills and subscriptions that post themselves, a cash-flow chart, balance check-ins, the one-paste installer |
| ✅ | **M2: Tasks and people** | Tasks with kanban status, your own labels, lists, reminders, a Today screen, a calendar with tasks and bills, saved filters, bank CSV import, contacts |
| 🔜 | **M3: AI, your way** | Connect your own Claude. Say *"remind me to review the proposal by Friday noon"* and it proposes the task for you to approve. Private items never reach it, and every access is logged. |
| ⬜ | **M4: Connectors** | Read your calendars and bill-alert emails (only the ones you turn on) |
| ⬜ | **M5: Phone** | Use it from your phone over your own private network |
| ⬜ | **M6: Pick your AI** | A chat panel, with fully local models (Ollama) or the provider you choose |
| ⬜ | **M7: Research** | Summarize public documents like building codes and check your notes against them |

After the features are in, the first user tests everything together, and their feedback lands in the [backlog](docs/BACKLOG.md). The full plan, with the reasons behind each choice, is in [PLAN.md](PLAN.md).

## Get it on your computer

**No programming needed.** You paste one message into Claude, and Claude downloads TurtleMaxxxing, installs it and checks it works, explaining each step and asking before it installs anything. Plan on about **30 minutes**, mostly waiting on downloads.

### What's "the codebase", and do I need a GitHub account?

This page is on **GitHub**, a website where people share the files that make up an app (its *code*). Getting the app means copying those files to your computer. Then the app runs **entirely on your computer**: nothing you put in it ever goes back to GitHub.

**You don't need a GitHub account.** TurtleMaxxxing is public, so anyone can download it without signing in. You'd only want an account to [report a problem](https://github.com/jefflovell/TurtleMaxxxing/issues) or ⭐ star the project, and both are optional.

### What you need

| | Why | Cost |
|---|---|---|
| A **personal** Windows 10 or 11 computer | The app runs here. **Never use a work computer.** | — |
| The **Claude desktop app** | Claude does the installing for you | Free download |
| A **Claude account on a paid plan** | Installing uses *Claude Code*, which is included in all paid Claude plans but not the free one. See [Claude's plans](https://claude.com/pricing). | Paid plan |

Mac or Linux? The app itself runs there, but the guided install is Windows-only for now. See [Install by hand](#install-by-hand-for-the-technical).

### Step 1: Get Claude
1. Go to **[claude.ai/download](https://claude.ai/download)** and click **Windows**.
2. Open the downloaded file to install the Claude app.
3. Open Claude and **sign up** (or log in) with your personal email, not a work account.
4. If you're on the free plan, upgrade to a paid plan from Claude's settings.

### Step 2: Open Claude Code in a safe folder
1. In the Claude app, open the **Code** tab.
2. When it asks which folder to work in, choose your **home folder** (`C:\Users\<your name>`).
   - **Don't** pick Documents, Downloads, OneDrive or any folder with work files in it. Claude can look at the folder you choose.
3. Leave the permission setting at its normal mode, so Claude **asks before running anything**.

### Step 3: Paste the setup message
1. Open the **[one-paste setup prompt](docs/SETUP_PROMPT.md)**.
2. Copy everything inside the gray box (there's a copy button in its top-right corner).
3. Paste it into Claude Code and press **Enter**.
4. Answer Claude's questions as it goes:
   - **Where to install** (the suggested folder is fine).
   - **Which browser you use for personal things** (not the one you use for work).
   - **What to name the app's address.**
5. Each time Claude asks to run or install something, read what it says, then approve it. It installs three free tools the app needs (**Git**, which does the downloading, **uv** and **Node.js**), downloads TurtleMaxxxing, runs its built-in privacy tests and shows you the results.

### Step 4: Open it
When Claude is done, press the **Windows key**, type **I like turtles**, and press **Enter**. TurtleMaxxxing opens in your browser. 🐢

Close the small "TurtleMaxxxing" window to stop the app. The same shortcut starts it again.

### Later: updates and help
- **Update:** in Claude Code, open your TurtleMaxxxing folder and say **"update TurtleMaxxxing"**. It downloads the latest version, re-checks everything, and keeps your data.
- **Something wrong?** In that same folder, just describe it ("the page is blank", "my balance looks off"). Claude follows the built-in [troubleshooting guides](docs/troubleshooting/README.md).
- **Want something changed?** Say **"backlog: ..."** and it's added to the [list of requested changes](docs/BACKLOG.md).
- **Safety check:** after installing, the 15-minute [separation test](docs/testing/SEPARATION_TEST.md) confirms your AI tools can't see your work stuff. The [security guide](docs/SECURITY.md) explains it all in plain language.

## Install by hand (for the technical)

You need [Git](https://git-scm.com/), [uv](https://docs.astral.sh/uv/) and [Node.js](https://nodejs.org/) (LTS). Then:

```bash
git clone https://github.com/jefflovell/TurtleMaxxxing.git
cd TurtleMaxxxing
uv sync --directory backend
npm install --prefix frontend
npm run build --prefix frontend
uv run --directory backend turtlemaxxxing
```

Then open **http://turtle.localhost:8765**. Your data stays in your local app-data folder, and the app only listens on your own computer.

Just looking? `uv run --directory backend turtlemaxxxing --demo` runs it with fictional data in a throwaway folder.

No Git? The green **Code** button at the top of this page → **Download ZIP** works too. Unzip it, open a terminal in the `TurtleMaxxxing-main` folder, and start from the `uv sync` line. Updating then means downloading the ZIP again, so Git is easier in the long run.

🧪 **Trust, but verify:** every privacy promise has a test you can run yourself. See the [testing SOP](docs/TESTING.md). For AI agents working on the code, start with [AGENTS.md](AGENTS.md).

I like turtles. 🐢

## License

[MIT](LICENSE)
