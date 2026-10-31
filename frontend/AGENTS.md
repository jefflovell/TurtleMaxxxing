# Frontend guide

React 19, TypeScript, Vite and Recharts. Plain CSS with theme tokens (no CSS framework).

## How it runs
- **Normal use:** `npm run build` writes `dist/`, and the Python backend serves it at http://127.0.0.1:8765. **After any UI change, rebuild**, or the app keeps showing the old version.
- **While developing:** start the backend, then `npm run dev` and open http://127.0.0.1:5173 (live reload; `/api` is forwarded to the backend).

## Files

| File | What it does |
|---|---|
| `src/App.tsx` | Layout, sidebar navigation (including saved filters), shared data (accounts, rules, labels, lists, saved filters, review count). `refresh()` reloads everything after a change. |
| `src/lib/api.ts` | **The only place that calls the backend.** Every call goes to `/api` on this computer. |
| `src/lib/types.ts` | Data shapes, matching `backend/turtlemaxxxing/budget/api.py`. |
| `src/lib/format.ts` | Money (cents ↔ dollars), dates, labels for frequencies and account types. |
| `src/index.css` | Theme tokens (light and dark) and all styles. Change colors here. |
| `src/pages/*.tsx` | One file per screen. Plan: Today (home), Tasks (list and board; also opened from a saved filter), Calendar (tasks and bills), Contacts (list and editor), Labels. Money: Cash flow, Review inbox, Import CSV, Money rules, Accounts. |
| `src/components/*.tsx` | Shared pieces: task editor, task row, quick add, label chips and picker, people chips and picker (`TaskBits.tsx`), reminder pop-ups, month picker, rule form, status chip, empty state. |
| `src/lib/tasks.ts` | Task status names and icons. |

## Common changes

**Change colors or the look:** edit the tokens at the top of `src/index.css`. Dark mode has its own block below. Chart colors (`--series-1`, status colors) come from a color-blind-safe palette, so keep them unless you know why you're changing them.

**Add a field to a form:** add it to the backend model first (see `backend/turtlemaxxxing/budget/AGENTS.md`), then to `types.ts`, then to the form in `pages/` or `components/RuleForm.tsx`.

**Add a page:** create `src/pages/NewPage.tsx` taking `PageProps`, then add it to `NAV` and the page switch in `App.tsx`.

## Rules
- **No external network requests:** no CDN fonts, analytics, or remote images. Everything is bundled.
- Status and meaning are never shown by color alone. Pair color with an icon or word (see `StatusChip.tsx`).
- Money is integer cents in all API calls. Convert only for display (`money()`) and input (`toCents()`).
- Show 🔒 for any task, contact or person on a task where `is_private` is true. Never decide privacy in the UI; the backend's `is_private` is the source of truth.
- Label colors come from `--label-*` tokens in `index.css` (a color-blind-safe palette). Labels show a colored dot, and their text stays in normal text color.
- Board drag-and-drop uses the browser's native drag events. Keyboard and touch users change status in the task editor instead.
- **Saved filters:** clicking one sets `activeFilter` in `App.tsx`, and the Tasks page is remounted (its `key`) so it starts from that filter. The filter's shape is `FilterSpec` in `types.ts`, matching `FilterSpec` in `backend/turtlemaxxxing/tasks/api.py`.
- **CSV import** sends the file's text to the backend on this computer; it is never saved. Preview and import send the *same* column choices, so the import does exactly what the preview showed. In those choices `""` means "no such column" and `null` means "guess".

## Check your work
```bash
npm run build    # type-checks and builds; must pass with no errors
```
