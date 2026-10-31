---
name: backlog
description: Add, update, triage or close items in TurtleMaxxxing's QA / UAT backlog (docs/BACKLOG.md). Use when someone reports a bug, asks for a change or small feature while testing, gives UAT feedback, says "backlog:", "add to the backlog", "log this", "QA note", or asks what's open, what to fix next, or to close or verify an item.
---

# QA / UAT backlog 🐢📝

`docs/BACKLOG.md` is the list of revision requests from testing. Its **How items are filled in** section is the rulebook; read it before changing anything. Keep the requester's words in mind, but write the item in plain, neutral language.

**Always:**
- 🔒 **The repo is public.** Use the requester's **alias** from the Requesters table, never a real name. If the person isn't listed, ask which alias to use (suggest `tester-N`) and add it to the table first. Never write down who an alias really is.
- **Scrub the details.** No real amounts, payees, accounts, employers, addresses, file paths, or screenshots of real data. Rewrite with fictional examples and say you did.
- Never read the user's data folder to investigate a report. Reproduce it with `--demo` (TESTING.md §5).
- After any change, run `uv run --directory backend pytest -q tests/test_backlog.py`.

## 1. Add an item
1. **Check for a duplicate** in Open and Closed. If it's already there, add the new requester under *Also requested by* (alias and today's date) instead of a new item, and say so.
2. **Fill in every field yourself**, using the rules in BACKLOG.md:
   - **ID:** the highest `QA-` number in the file plus one.
   - **Requested:** today's date, unless the person says when they first asked.
   - **Milestone:** look up the feature in the milestone map. Use `new` if no existing feature covers it.
   - **Category:** every category that fits. If it builds on an existing feature, include `extension` and fill in **Extends**.
   - **Complexity:** estimate from the table, after a quick look at the code involved (which files, whether it needs a migration). Bump it for money math or the security guard.
   - **Priority:** from its definition. Anything that could leak Private data or lose data is P0.
   - **Privacy impact:** `review` if it touches the Private rule, AI paths, the network, `security.py` or what's stored. Otherwise `none`.
   - **Found in:** `git log -1 --format=%h`, unless the person says otherwise.
   - **Status:** `new`.
   - **Bugs:** also Steps, Actual, Expected and Severity. Try to reproduce it in the demo first, and say whether you could.
3. Add the table row under **Open** (in ID order) and a `### QA-NNN Title` section under **Details**.
4. **Show the person what you filled in** (category, priority, complexity, milestone) in a short list and invite corrections. Those calls are estimates, and they know their priorities better.

## 2. Triage or plan
- **Triage:** check the fields, adjust the priority and complexity, and set Status `triaged`.
- **Plan:** set **Target** to a milestone and Status `planned`.
- **"What's next?"** List open items by priority, then by date. Point out P0s and `review` items first.

## 3. Work on an item
1. Set Status `in-progress`.
2. Fix it following TESTING.md. **Bugs need a regression test.**
3. When it's shipped, set Status `ready-to-verify` and fill in **Fixed in** (the commit) and **Regression test**.
4. If a bug fix's test protects a promise, also add it to TESTING.md §7.

## 4. Close an item
- **Verified:** only when the requester (or the maintainer, for their own items) confirms it works in the app. Fill in **Verified** (`alias, date`).
- **Won't do / duplicate:** add the reason or the other ID to Notes.
- Move the row from **Open** to **Closed**, with the Closed date and Fixed in. Keep the Details section.

Report what you changed in one or two sentences, and don't commit unless asked.
