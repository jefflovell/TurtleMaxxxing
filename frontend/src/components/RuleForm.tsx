import { useState } from 'react'
import { api, type RuleInput } from '../lib/api'
import { FREQUENCY_LABELS, money, toCents, todayIso } from '../lib/format'
import type { Account, Frequency, RuleKind } from '../lib/types'

interface SplitDraft { account_id: string; amount: string; label: string }

const KIND_COPY: Record<RuleKind, { title: string; amountLabel: string; accountLabel: string; placeholder: string }> = {
  income: { title: 'Paycheck or income', amountLabel: 'Amount per payday', accountLabel: 'Remainder goes to', placeholder: 'e.g. Paycheck' },
  bill: { title: 'Bill', amountLabel: 'Amount', accountLabel: 'Paid from', placeholder: 'e.g. Rent' },
  subscription: { title: 'Subscription', amountLabel: 'Price', accountLabel: 'Paid from', placeholder: 'e.g. Streaming' },
}

export default function RuleForm({ accounts, onDone }: { accounts: Account[]; onDone: () => void }) {
  const active = accounts.filter((a) => !a.archived)
  const defaultAccount = String(active.find((a) => a.kind === 'checking')?.id ?? active[0]?.id ?? '')
  const [kind, setKind] = useState<RuleKind>('income')
  const [name, setName] = useState('')
  const [amount, setAmount] = useState('')
  const [accountId, setAccountId] = useState(defaultAccount)
  const [frequency, setFrequency] = useState<Frequency>('biweekly')
  const [start, setStart] = useState(todayIso())
  const [secondDay, setSecondDay] = useState('15')
  const [reviewEvery, setReviewEvery] = useState('3')
  const [splits, setSplits] = useState<SplitDraft[]>([])
  const [error, setError] = useState<string | null>(null)
  const copy = KIND_COPY[kind]

  const amountCents = toCents(amount) ?? 0
  const splitCents = splits.map((s) => toCents(s.amount) ?? 0)
  const remainder = amountCents - splitCents.reduce((a, b) => a + b, 0)

  function chooseKind(k: RuleKind) {
    setKind(k)
    setFrequency(k === 'income' ? 'biweekly' : 'monthly')
    if (k !== 'income') setSplits([])
  }

  function updateSplit(i: number, patch: Partial<SplitDraft>) {
    setSplits(splits.map((s, j) => (j === i ? { ...s, ...patch } : s)))
  }

  async function save(ev: React.FormEvent) {
    ev.preventDefault()
    if (toCents(amount) === null) return setError('Amount needs to be a number, like 2450.00')
    if (splits.some((s) => !s.account_id || !toCents(s.amount))) return setError('Each split needs an account and an amount.')
    if (remainder < 0) return setError('The splits add up to more than the paycheck.')
    const body: RuleInput = {
      kind,
      name: name.trim(),
      amount_cents: amountCents,
      account_id: Number(accountId),
      frequency,
      start_date: start,
      end_date: null,
      second_day: frequency === 'semimonthly' ? Number(secondDay) : null,
      review_every_months: kind === 'subscription' && reviewEvery ? Number(reviewEvery) : null,
      splits: splits.map((s, i) => ({
        account_id: Number(s.account_id),
        amount_cents: splitCents[i],
        label: s.label.trim() || accounts.find((a) => a.id === Number(s.account_id))?.name || null,
      })),
    }
    try {
      await api.createRule(body)
      onDone()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <form className="card stack" onSubmit={save}>
      <div className="row" role="radiogroup" aria-label="Rule type">
        {(Object.keys(KIND_COPY) as RuleKind[]).map((k) => (
          <button
            type="button" key={k} role="radio" aria-checked={kind === k}
            className={`btn ${kind === k ? 'primary' : ''}`} onClick={() => chooseKind(k)}
          >
            {KIND_COPY[k].title}
          </button>
        ))}
      </div>

      <div className="form-grid">
        <label className="field">Name
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder={copy.placeholder} required />
        </label>
        <label className="field">{copy.amountLabel}
          <input value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="0.00" inputMode="decimal" required />
        </label>
        <label className="field">How often
          <select value={frequency} onChange={(e) => setFrequency(e.target.value as Frequency)}>
            {Object.entries(FREQUENCY_LABELS).map(([f, label]) => <option key={f} value={f}>{label}</option>)}
          </select>
        </label>
        <label className="field">{frequency === 'once' ? 'Date' : 'First date'}
          <input type="date" value={start} onChange={(e) => setStart(e.target.value)} required />
        </label>
        {frequency === 'semimonthly' && (
          <label className="field">Second day of the month
            <input type="number" min={1} max={31} value={secondDay} onChange={(e) => setSecondDay(e.target.value)} />
          </label>
        )}
        <label className="field">{copy.accountLabel}
          <select value={accountId} onChange={(e) => setAccountId(e.target.value)} required>
            {active.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
        </label>
        {kind === 'subscription' && (
          <label className="field">Ask "still paying for this?"
            <select value={reviewEvery} onChange={(e) => setReviewEvery(e.target.value)}>
              <option value="1">Every month</option>
              <option value="3">Every 3 months</option>
              <option value="6">Every 6 months</option>
              <option value="12">Every year</option>
              <option value="">Never</option>
            </select>
          </label>
        )}
      </div>

      {kind === 'income' && (
        <div className="stack" style={{ gap: 8 }}>
          <h3>Split it up <span className="muted small">(optional)</span></h3>
          <p className="small muted" style={{ margin: 0 }}>
            Send set amounts to other accounts every payday, e.g. HSA, 401(k), a 529. Their balances update automatically.
          </p>
          {splits.map((s, i) => (
            <div className="split-row" key={i}>
              <label className="field">Goes to
                <select value={s.account_id} onChange={(e) => updateSplit(i, { account_id: e.target.value })}>
                  <option value="">Choose…</option>
                  {active.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </label>
              <label className="field">Amount
                <input value={s.amount} onChange={(e) => updateSplit(i, { amount: e.target.value })} placeholder="0.00" inputMode="decimal" />
              </label>
              <label className="field">Label
                <input value={s.label} onChange={(e) => updateSplit(i, { label: e.target.value })} placeholder="optional" />
              </label>
              <button type="button" className="btn small ghost" aria-label="Remove split" onClick={() => setSplits(splits.filter((_, j) => j !== i))}>✕</button>
            </div>
          ))}
          <div className="row">
            <button type="button" className="btn small" onClick={() => setSplits([...splits, { account_id: '', amount: '', label: '' }])}>
              + Add a split
            </button>
            {amountCents > 0 && (
              <span className={`small num ${remainder < 0 ? 'negative' : 'muted'}`}>
                Remainder to {accounts.find((a) => a.id === Number(accountId))?.name ?? 'account'}: {money(remainder)}
              </span>
            )}
          </div>
        </div>
      )}

      {error && <div className="error" role="alert">{error}</div>}
      <div className="row">
        <button className="btn primary" type="submit">Save rule</button>
        <button className="btn" type="button" onClick={onDone}>Cancel</button>
      </div>
    </form>
  )
}
