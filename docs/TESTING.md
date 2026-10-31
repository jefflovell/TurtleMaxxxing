# Testing SOP 🐢🧪

**Why this is public:** TurtleMaxxxing asks you to trust it with your money data and to keep work and personal life apart. Promises are cheap, so we publish *how* we check them. Every privacy and security promise in [SECURITY.md](SECURITY.md) maps to an automated test you can run yourself.

This is a **standard operating procedure.** It applies to every change, whether a person or an AI agent makes it. AI agents: this file is binding, and `AGENTS.md` and `CLAUDE.md` point here for that reason.

---

## 1. Ground rules

1. **Tests are the contract.** If a test protects a promise in `SECURITY.md` or `PLAN.md` §3, never weaken, skip or delete it to make a change pass. Fix the change instead. If a promise genuinely changes, update `SECURITY.md` in the same commit and explain why.
2. **Fictional data only.** Tests, demos, screenshots and bug reports use made-up names and amounts ("Kid A 529", "Streaming $15.99"). Never real accounts, names, employers or addresses.
3. **Never touch real data.** Tests run against a temporary data folder (`TURTLE_DATA_DIR` is set by `tests/conftest.py`). Manual testing uses `--demo`, which runs on a throwaway folder that's deleted on exit.
4. **No network in tests.** Tests talk to the app in memory. Nothing in the test suite may contact the internet.
5. **Every bug gets a regression test** that fails before the fix and passes after it.
6. **Report honestly.** If tests fail, say so and show the output. If something wasn't tested, say that too. "It should work" isn't a test result.

## 2. Promise → test map

| Promise | Where it's checked |
|---|---|
| The app makes **no outbound connections**; using every screen's API triggers no non-localhost connection or DNS lookup | `tests/test_privacy.py::test_using_the_app_makes_no_outbound_connections` |
| The server **only listens on 127.0.0.1** | `tests/test_privacy.py::test_server_listens_on_localhost_only` |
| Your **data lives outside the repo** | `tests/test_privacy.py::test_default_data_folder_is_outside_the_repo` |
| **Other websites can't read your data** (DNS rebinding blocked; only our own host names answered) | `tests/test_local_security.py::test_refuses_other_host_names_dns_rebinding` |
| **Other websites can't change your data** (cross-site requests refused) | `tests/test_local_security.py::test_cross_site_changes_are_refused`, `::test_cross_site_fetch_metadata_is_refused` |
| **No CORS**, so other sites can't read responses | `tests/test_local_security.py::test_no_cors_headers_so_other_sites_cannot_read` |
| The friendly address **can never be a real internet name** (only `*.localhost`) | `tests/test_config_and_cli.py::test_rejected_hostnames_can_never_claim_a_real_internet_name` |
| Bad settings **fail loudly** instead of silently opening up | `tests/test_config_and_cli.py::test_bad_settings_fail_loudly` |
| **Paycheck splits** update every account automatically | `tests/test_budget_api.py::test_paycheck_splits_auto_post_and_update_balances` |
| Auto-posting **never double-counts** | `tests/test_budget_api.py::test_auto_posting_is_idempotent`, `::test_rule_dates_before_the_opening_balance_are_not_double_counted` |
| **Editing a rule changes the future, never the past** | `tests/test_budget_api.py::test_rule_edits_change_the_future_not_the_past` |
| **Check-ins and subscription reviews** do what they say | `tests/test_budget_api.py::test_balance_checkin_creates_adjustment`, `::test_subscription_review_keep_cancel_and_change_price` |
| **A task is Private** if flagged Private **or** tagged with an auto-Private label, and turning auto-Private on applies to existing tasks immediately | `tests/test_tasks_api.py::test_private_flag_makes_a_task_private`, `::test_auto_private_label_makes_tagged_tasks_private`, `::test_turning_on_auto_private_applies_to_existing_tasks` |
| **Upgrades keep your data** and back up the old database first | `tests/test_migrations.py::test_upgrade_from_v1_keeps_data_and_backs_up` |
| **CSV import never double-counts:** importing the same or an overlapping file again changes nothing, and rows already marked paid by hand are linked, not added | `tests/test_csv_import.py::test_importing_the_same_file_twice_changes_nothing`, `::test_overlapping_files_only_add_the_new_rows`, `::test_rows_marked_paid_by_hand_are_linked_not_added_again` |
| **CSV preview changes nothing**, and **the file itself is never stored** (rows you skip leave no trace) | `tests/test_csv_import.py::test_preview_changes_nothing`, `::test_the_file_itself_is_never_stored` |
| **Imported balances add up** to the cent, including a bill paid early not being posted again on its due date | `tests/test_csv_import.py::test_apply_confirms_matches_adds_the_rest_and_balances_add_up` |
| **Reminders** fire on time, snooze and dismiss, and never nag about finished tasks | `tests/test_tasks_api.py::test_reminders_fire_dismiss_and_snooze`, `::test_done_tasks_do_not_remind` |

*Coming with later milestones (from [the separation test](testing/SEPARATION_TEST.md)):* Private items never reach any AI path or MCP tool (M3, built on the `is_private` rule tested above), blocked file types are refused (M3), and the work-account warning (M4). Each lands with its tests in the same milestone, or it doesn't land.

## 3. Test layers

| Layer | What | Files |
|---|---|---|
| **Unit** | Pure logic with no database, e.g. which dates a schedule hits, including month ends and leap years | `test_schedule.py` |
| **End-to-end API** | The real app with a temporary database, called over HTTP. A movable `clock` fixture lets tests jump weeks ahead to watch paydays, bills and reviews happen | `test_budget_api.py`, `test_tasks_api.py`, `test_csv_import.py`, `test_demo.py` |
| **Migrations** | Upgrading an older database keeps its data and backs it up first | `test_migrations.py` |
| **Privacy and security** | The guarantees in §2: network guard, host and origin checks, data location | `test_privacy.py`, `test_local_security.py` |
| **Config and CLI** | Settings validation, the port scan, command-line behavior | `test_config_and_cli.py` |
| **Manual walkthrough** | A person or agent uses the real UI in a browser (§5) | — |
| **Separation test** | A human checks the computer around the app: AI extensions, screen access, file access | [testing/SEPARATION_TEST.md](testing/SEPARATION_TEST.md) |
| **CI** | All automated layers above, on Windows and Linux, in public, on every push | [.github/workflows/ci.yml](../.github/workflows/ci.yml) |

**How the network guard works:** during the test, Python's `socket.connect` and `socket.getaddrinfo` are swapped for versions that record and refuse anything that isn't `127.0.0.1`, `::1` or `localhost`. The test then exercises every API area and fails if anything was attempted.

## 4. Run the tests

From the repo root:

```bash
uv run --directory backend pytest -q          # all backend tests (a few seconds)
npm run build --prefix frontend               # type-checks and builds the UI
```

Both must pass. Run one file with `uv run --directory backend pytest -q tests/test_privacy.py`.

### In public, on every push (CI)

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on every push and pull request, and anyone can read the results on the repository's **Actions** tab or via the badge in the README.

| Job | What runs |
|---|---|
| **Backend** × 4 | Windows and Linux × Python 3.12 (oldest supported) and 3.15 (newest). Installs exactly what's in `uv.lock`, runs the **privacy and security tests as their own named step** so they're easy to find, then the full suite. |
| **Frontend** | Installs exactly what's in `package-lock.json`, then lint, type-check and build. |

**CI hygiene:**
- Third-party actions are pinned to exact commit SHAs, and Dependabot proposes updates as pull requests that go through CI first.
- The workflow has read-only access to the repo and uses no secrets.
- **A red CI run blocks "done."** Don't merge or call a change finished while CI is failing.

## 5. Manual walkthrough (for UI changes)

1. Start the demo: `uv run --directory backend turtlemaxxxing --demo`. It uses fictional data in a throwaway folder.
2. Open http://turtle.localhost:8765 (or http://127.0.0.1:8765).
3. Visit **every page** you touched, and at least **Cash flow**, **Calendar** and **Review inbox**. Do one real action on each: mark a bill paid, resolve a check-in, add a rule with a split.
   For CSV import, use a small **made-up** CSV whose dates fit the demo's month. Never use a real bank export for testing.
4. Check **phone width** (about 375px) and **dark mode**.
5. Open developer tools → **Network** and reload. **Every request must go to the app's own address.** Any other domain (fonts, analytics, CDNs) is a bug.
6. Note what you checked in the commit or PR description.

AI agents with a browser should do this too, and report what they saw, including anything that looked wrong.

## 6. Definition of done (any change, any author)

- [ ] Backend tests pass: `uv run --directory backend pytest -q`.
- [ ] The frontend lints and builds: `npm run lint --prefix frontend` and `npm run build --prefix frontend`.
- [ ] CI is green on the pushed commit.
- [ ] New behavior has tests, and a bug fix has a regression test.
- [ ] No test from §2 was weakened, skipped or deleted.
- [ ] UI changes got the manual walkthrough (§5).
- [ ] No real data, PII, secrets, tokens or real URLs in code, tests, docs or screenshots.
- [ ] Module `AGENTS.md` and `docs/SETUP_NOTES.md` are updated if behavior or setup changed.

## 7. Bugs found this way (so far)

Real examples, kept to show the process works and why the rules exist:

| Bug | How it was found | Regression test |
|---|---|---|
| Rule dates before an account's "balance as of" date were counted on top of a balance that already included them | Manual walkthrough with demo data: the checking balance didn't match a hand calculation | `test_rule_dates_before_the_opening_balance_are_not_double_counted` |
| In the month an account was opened, the cash-flow chart started at $0 and never showed the starting balance | Manual walkthrough: the chart's shape was wrong | `test_cashflow_shows_starting_balance_in_the_opening_month` |
| The review inbox briefly showed "All caught up!" while still loading, even with items waiting | Manual walkthrough | Manual check only (frontend tests are a known gap, see §8) |
| One unreadable row (a "Pending" line) made CSV date detection reject the whole file | The CSV import tests, before it shipped | `test_date_format_detection` ("one junk row doesn't sink the file") |

## 8. Known gaps (honest list)

- **No automated frontend tests yet.** The UI is checked by type-checking, the build, and manual walkthroughs. Planned: component tests for money input and forms.
- **Migrations:** upgrades from v1 and v2 → current are tested. Each new migration should extend `test_migrations.py` with data that touches its tables.
- **CSV formats:** tested with common US layouts (one amount column, debit/credit columns, a preamble above the header, card statements with positive purchases). Other banks' layouts will turn up in real use; each one gets a fictional test case when it does.
- **Board drag-and-drop** is checked manually. In-page drag events were verified in the walkthrough, but there's no automated UI test yet.
- **Time zones:** "today" is the computer's local date. Travel across time zones isn't tested.
- **The separation test is manual** and depends on each person's machine.

## 9. Changing this SOP

Changes to this file need a clear reason in the commit message. Loosening a rule needs an explanation of what replaces it.
