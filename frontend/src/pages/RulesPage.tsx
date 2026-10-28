import { useState } from 'react'
import type { PageProps } from '../App'
import EmptyState from '../components/EmptyState'
import RuleForm from '../components/RuleForm'
import { api } from '../lib/api'
import { FREQUENCY_LABELS, centsToInput, money, toCents, todayIso } from '../lib/format'
import type { Rule, RuleKind } from '../lib/types'

const SECTIONS: { kind: RuleKind; title: string }[] = [
  { kind: 'income', title: '💰 Income' },
  { kind: 'bill', title: '🧾 Bills' },
  { kind: 'subscription', title: '🔁 Subscriptions' },
]

export default function RulesPage({ accounts, rules, refresh, goTo }: PageProps) {
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)
  const [newAmount, setNewAmount] = useState('')
  const [error, setError] = useState<string | null>(null)
  const today = todayIso()
  const accountName = (id: number) => accounts.find((a) => a.id === id)?.name ?? '—'
  const isEnded = (r: Rule) => r.end_date !== null && r.end_date < today

  async function saveAmount(rule: Rule) {
    const cents = toCents(newAmount)
    if (cents === null) return setError('Amount needs to be a number.')
    try {
      await api.updateRule(rule.id, { amount_cents: cents })
      setEditing(null); setError(null)
      refresh()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function stop(rule: Rule) {
    if (!confirm(`Stop "${rule.name}" from today? Past entries stay as they are.`)) return
    await api.updateRule(rule.id, { end_date: today })
    refresh()
  }

  if (accounts.length === 0) {
    return (
      <div className="stack">
        <h1>Money rules</h1>
        <div className="card"><EmptyState>
          <p>Add an account first, so rules know where money goes.</p>
          <button className="btn primary" onClick={() => goTo('accounts')}>Add an account</button>
        </EmptyState></div>
      </div>
    )
  }

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Money rules</h1>
          <p>Describe your paychecks, bills and subscriptions once. The app keeps the ledger moving on its own.</p>
        </div>
        {!adding && <button className="btn primary" onClick={() => setAdding(true)}>+ New rule</button>}
      </div>

      {adding && <RuleForm accounts={accounts} onDone={() => { setAdding(false); refresh() }} />}
      {error && <div className="error" role="alert">{error}</div>}

      {SECTIONS.map(({ kind, title }) => {
        const list = rules.filter((r) => r.kind === kind)
        if (list.length === 0) return null
        return (
          <div className="card" key={kind}>
            <h2 style={{ marginBottom: 8 }}>{title}</h2>
            <table>
              <thead>
                <tr><th>Name</th><th>Schedule</th><th>Account</th><th className="amount">Amount</th><th /></tr>
              </thead>
              <tbody>
                {list.map((r) => (
                  <tr key={r.id} style={{ opacity: isEnded(r) ? 0.55 : 1 }}>
                    <td>
                      <strong>{r.name}</strong>
                      {isEnded(r) && <span className="muted small"> (stopped {r.end_date})</span>}
                      {r.splits.length > 0 && (
                        <div className="small muted">
                          {r.splits.map((s) => `${s.label ?? accountName(s.account_id)} ${money(s.amount_cents)}`).join(' · ')}
                        </div>
                      )}
                    </td>
                    <td className="muted small">{FREQUENCY_LABELS[r.frequency]} from {r.start_date}</td>
                    <td className="muted">{accountName(r.account_id)}</td>
                    <td className="amount num">
                      {editing === r.id ? (
                        <span className="row" style={{ justifyContent: 'flex-end' }}>
                          <input style={{ width: 100 }} value={newAmount} onChange={(e) => setNewAmount(e.target.value)} inputMode="decimal" autoFocus />
                          <button className="btn small primary" onClick={() => saveAmount(r)}>Save</button>
                          <button className="btn small" onClick={() => setEditing(null)}>Cancel</button>
                        </span>
                      ) : money(r.amount_cents)}
                    </td>
                    <td className="amount">
                      {!isEnded(r) && editing !== r.id && (
                        <span className="row" style={{ justifyContent: 'flex-end', gap: 4 }}>
                          <button className="btn small ghost" onClick={() => { setEditing(r.id); setNewAmount(centsToInput(r.amount_cents)) }}>
                            Change amount
                          </button>
                          <button className="btn small ghost" onClick={() => stop(r)}>Stop</button>
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      })}

      {rules.length === 0 && !adding && (
        <div className="card"><EmptyState>
          <p>No rules yet. Start with your paycheck. You can split it into HSA, 401(k), 529s and more.</p>
          <button className="btn primary" onClick={() => setAdding(true)}>Add your paycheck</button>
        </EmptyState></div>
      )}
      <p className="small muted">Changing an amount affects future dates only. Everything already posted stays as it was.</p>
    </div>
  )
}
