# Security and Privacy 🐢🔒

This guide explains, in plain language, how TurtleMaxxxing keeps your work and personal life separate, what the AI can and can't see, and the few habits that keep it that way.

**The short version:**
1. **Work files never go in the app.** Work tasks are short text labels only.
2. **Normal items may be seen by your AI. 🔒 Private items never are.**
3. **Nothing leaves your computer unless you turn it on.**
4. **The AI suggests, and you approve.** Nothing is saved without your click.

---

## 1. Three zones

| Zone | What goes here | Can AI see it? |
|---|---|---|
| 🐢 **Normal** | Personal tasks, budget, calendar, notes, public documents, and *short* work reminders like "Review Smith St proposal by Friday" | ✅ Yes, if you've connected an AI, and every access is logged |
| 🔒 **Private** | Anything you flag Private, or tag with an auto-Private label | ❌ Never |
| 🚫 **Never in the app** | Work files, drawings, documents, file paths, network paths, links into work systems | ❌ The app won't store them at all |

## 2. What's OK to tell an AI: the sticky-note test

> **Would you be fine writing it on a sticky note and leaving it on your fridge while friends are over?**
> - **Yes** → a normal item is fine. *"Dentist Tuesday 3pm"*, *"Pay water bill"*, *"Prep for client meeting Monday"*
> - **Not sure, or no** → mark it 🔒 **Private**, or write it more vaguely. *"Prep for meeting Monday"* instead of naming a sensitive client or project.
> - **It comes from a work document or system** → **leave it out.** Keep it at work.

**Tips:**
- Use **vague but useful** wording: "Client call 2pm" works as a reminder without giving details away.
- Make a label like `work-sensitive` and set it to **auto-Private**, so tagging is all you need.
- Your **voice notes and dictation** go to your AI as text, so the sticky-note test applies to what you *say*, too.

## 3. Where your data goes

| What | Where it goes | When |
|---|---|---|
| Everything you enter | A database on **your computer** | Always |
| Normal items | The **AI you chose** (e.g. Claude, a local model) | Only when you use the AI with the app, and logged in the app's **AI audit log** |
| Private items | **Nowhere** | Never |
| Calendar events you approve | Your **one chosen personal calendar** | Only after you approve each one |
| Calendar, email, statement data | Read from services **you connected** | Only for connectors you turned on |
| A bank CSV you import | Read **in memory on your computer**; the file itself is never saved, only the transactions you import | Only when you import one. The app never logs in to your bank. |
| Passwords, tokens, API keys | Your computer's **secure keychain** (Windows Credential Manager) | Never in chat, files or the database |
| Update checks | **github.com**, to download the newest release and its fingerprint | Only when you run *Update TurtleMaxxxing*. The app itself never connects. |
| Anything else | **Nowhere.** No telemetry, no accounts, no servers of ours | Never |

**Using a fully local model (e.g. Ollama)?** Then even normal items never leave your computer.

## 4. Habits that keep you safe

The app guards everything *inside* it. These habits cover the things *around* it.

### ✅ Do
- **Keep work in its own browser or profile** (e.g. one browser for work, another for personal), and never sign your work accounts into your personal profile.
- **Install AI browser extensions only in your personal profile.**
- **Keep your app data folder private.** Don't add it to any AI tool's shared folders.
- **Check the AI audit log now and then** to see what was shared, when, and with which AI.

### ❌ Don't
- **Don't turn on "computer use" or screen control** in AI apps on a computer where work appears on screen. These features can see your *whole screen*, work windows included.
- **Don't paste or drag work files into any AI chat**, inside this app or anywhere else.
- **Don't sign in to work accounts** (work email, work calendar, work Microsoft or Google accounts) in this app. It will warn you if you try.
- **Don't install this app on a work computer.** It's designed for personal machines only.

### If your work is regulated
If your job involves confidential or regulated material, **check your employer's rules** about personal devices and AI tools. This app keeps things separate, but it can't make a setup allowed if your employer doesn't allow it.

## 5. What the app does for you

- **Blocks risky file types:** you choose which (e.g. CAD formats like `.dwg .dxf .rvt`), and the app refuses to attach them.
- **One gate for all AI access:** every request to any AI goes through a single checkpoint that removes Private items and writes to the audit log.
- **Approve before saving:** AI suggestions wait in your **review inbox** until you approve them.
- **Read-only connectors:** the app reads your calendars, email labels and statements, and only writes approved events to the one calendar you picked.
- **Warns about work accounts:** connecting a work or school account requires an explicit "this is personal" confirmation.
- **No network by default:** a fresh install connects to nothing until you turn something on.
- **Only on your computer:** the app listens on `127.0.0.1`, which other devices can't reach. Its address, `http://turtle.localhost:8765`, is a special name that every browser keeps on your own computer.
- **Guards against other websites:** any web page you visit runs on your computer too, so the app only answers to its own address and refuses changes coming from other sites. A malicious page can't read or change your data through your browser.
- **Tested, in public:** every promise on this page has an automated test. See the [testing SOP](TESTING.md) for the full list and how to run them yourself.
- **Scanned for security bugs:** GitHub's CodeQL checks the code on every change and weekly. Results are on the repository's *Security* tab.

## 6. Check your setup

Run the **[separation test](testing/SEPARATION_TEST.md)** after installing, and again whenever you change browsers, AI apps or extensions. It takes about 15 minutes and uses fake test data only.

## 7. Reporting a security problem

Found a way around these protections? Please **don't open a public issue.** Use GitHub's **private vulnerability reporting** on this repository (the *Security* tab → *Report a vulnerability*), and include:
- what you did,
- what you expected,
- what happened instead.
