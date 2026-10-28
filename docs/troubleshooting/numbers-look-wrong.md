# A balance or the cash flow looks wrong

TurtleMaxxxing estimates balances from your rules. Small drift is expected, and fixing it is what check-ins are for. Work through these in order.

## 1. Quick fix: check the balance now
Go to **Accounts** → **Check balance** on that account. In the **Review inbox**, enter what the account really says. The app adds a labeled adjustment, and the balance is right from then on.

*(For agents: `POST /api/accounts/{id}/checkin` opens the same check-in.)*

To stop it drifting again, give the account a regular check-in schedule (e.g. every month) when you add it.

## 2. Is the starting balance date right?
The **"Balance today / As of"** you entered when adding an account counts as the balance at the **end** of that day. Anything scheduled on or before that date is assumed to be already included.
- Started a rule *before* the account's "as of" date? Those past dates are ignored on purpose.
- Entered the balance *before* today's paycheck arrived? The app will count the paycheck twice. Fix it with a check-in (step 1).

## 3. Is a rule wrong?
Open **Money rules** and check the amount, schedule and first date.
- **Wrong amount from now on:** use **Change amount**. Only future dates change, and the past stays as it was.
- **It ended:** use **Stop**.
- **Wrong split:** stop the rule and create a new one with the right split, starting on the next payday.

## 4. Was something marked paid that wasn't?
On the **Bills calendar**, paid items show ✓ and are struck through. Paid amounts count toward the balance on their date either way; "paid" just records that you confirmed it.

## 5. Still wrong? Gather facts (no data leaves your computer)
For agents: compare `GET /api/accounts` (balance), `GET /api/entries?start=...&end=...&account_id=...` (ledger) and `GET /api/rules`. Explain the difference to the user in plain language. **Don't paste their financial data anywhere else.**

## Verify
The account's balance in **Accounts** matches what the bank or provider shows.
