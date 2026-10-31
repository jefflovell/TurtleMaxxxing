# Get help from a free Claude chat 🐢

If TurtleMaxxxing isn't working, any Claude chat can walk you through fixing it, including the **free** plan at [claude.ai](https://claude.ai). Claude doesn't need access to your computer: it tells you what to try, and you do it.

1. Run **Check my TurtleMaxxxing install** from the Start menu (Start → TurtleMaxxxing). It copies a short report to your clipboard. The report has no data from the app, and your user name is replaced with `<you>`.
2. Open a new chat at [claude.ai](https://claude.ai).
3. Copy the prompt below, paste it into the chat, then paste your report underneath it and describe what's wrong.

````text
I need help with TurtleMaxxxing, a free, open-source app that runs only on my Windows
computer. Its code and troubleshooting guides are public here:
https://github.com/jefflovell/TurtleMaxxxing
(the guides are in docs/troubleshooting/).

I'm not a programmer. Please:
- Help me one small step at a time, and wait for me to tell you what happened.
- When I need to run a command, give me exactly one at a time to paste into PowerShell,
  and say what it does first.
- Prefer the app's own tools: the Start-menu shortcuts "Check my TurtleMaxxxing install"
  and "Update TurtleMaxxxing", and the steps in its troubleshooting guides.

Ground rules:
- Never ask me for passwords, keys, or account numbers.
- Never ask me to open, copy or paste anything from my data folder
  (%LOCALAPPDATA%\TurtleMaxxxing). That's my private data. Settings.json is OK if needed.
- Don't suggest commands that delete my data folder, change system settings, or need
  administrator rights. If you think one is needed, explain why and let me decide.
- Never suggest pasting a script from the internet straight into PowerShell.
- If you're not sure, say so.

Here's my install report, and what's going wrong:
````

**Remember:** describe the problem, not your data. "My checking balance is off by about $40 after a paycheck" is plenty; there's no need to paste real numbers or names.

Have a paid plan with Claude Code? Open your TurtleMaxxxing folder in Claude Code and say "help". Its `turtle-help` skill can run the fixes for you.
