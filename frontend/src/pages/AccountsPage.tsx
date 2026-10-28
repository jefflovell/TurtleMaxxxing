import { useState } from 'react'
import type { PageProps } from '../App'
import EmptyState from '../components/EmptyState'
import { api } from '../lib/api'
import { ACCOUNT_KIND_LABELS, money, toCents, todayIso } from '../lib/format'
import type { AccountKind } from '../lib/types'

// Sensible check-in defaults: accounts you can't see daily drift the most.
const DEFAULT_CHECKIN: Record<AccountKind, string> = {
  checking: '', savings: '30', credit: '30', hsa: '30', retirement: '90',
  brokerage: '90', education: '90', goal: '', other: '',
}

export default function AccountsPage({ accounts, refresh, goTo }: PageProps) {
  const [name, setName] = useState('')
  const [kind, setKind] = useState<AccountKind>('checking')
  const [balance, setBalance] = useState('')
  const [asOf, setAsOf] = useState(todayIso())
  const [checkin, setCheckin] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function add(ev: React.FormEvent) {
    ev.preventDefault()
    const cents = balance.trim() === '' ? 0 : toCents(balance)
    if (cents === null) return setError('Starting balance needs to be a number, like 1250.00')
    try {
      await api.createAccount({
        name: name.trim(),
        kind,
        opening_balance_cents: cents,
        opening_date: asOf,
        checkin_every_days: checkin ? Number(checkin) : null,
      })
      setName(''); setBalance(''); setError(null)
      refresh()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function toggleArchive(id: number, archived: boolean) {
    await api.updateAccount(id, { archived: !archived })
    refresh()
  }

  async function checkNow(id: number) {
    await api.checkBalanceNow(id)
    refresh()
    goTo('reviews')
  }

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Accounts</h1>
          <p>Everywhere your money lives or goes: checking, HSA, 401(k), a kid's 529, a savings goal.</p>
        </div>
      </div>

      <form className="card stack" onSubmit={add}>
        <h2>Add an account</h2>
        <div className="form-grid">
          <label className="field">Name
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Checking" required />
          </label>
          <label className="field">Type
            <select value={kind} onChange={(e) => {
              const k = e.target.value as AccountKind
              setKind(k); setCheckin(DEFAULT_CHECKIN[k])
            }}>
              {Object.entries(ACCOUNT_KIND_LABELS).map(([k, label]) => <option key={k} value={k}>{label}</option>)}
            </select>
          </label>
          <label className="field">Balance today
            <input value={balance} onChange={(e) => setBalance(e.target.value)} placeholder="0.00" inputMode="decimal" />
          </label>
          <label className="field">As of
            <input type="date" value={asOf} onChange={(e) => setAsOf(e.target.value)} />
          </label>
          <label className="field">Balance check-in
            <select value={checkin} onChange={(e) => setCheckin(e.target.value)}>
              <option value="">Never</option>
              <option value="7">Every week</option>
              <option value="30">Every month</option>
              <option value="90">Every 3 months</option>
            </select>
          </label>
        </div>
        <p className="small muted" style={{ margin: 0 }}>
          Check-ins ask "what does this account actually say?" now and then, so the app's numbers never drift from reality.
        </p>
        {error && <div className="error" role="alert">{error}</div>}
        <div><button className="btn primary" type="submit">Add account</button></div>
      </form>

      <div className="card">
        {accounts.length === 0 ? (
          <EmptyState>No accounts yet. Add one above. 🐢</EmptyState>
        ) : (
          <table>
            <thead>
              <tr><th>Account</th><th>Type</th><th className="amount">Balance</th><th>Check-in</th><th /></tr>
            </thead>
            <tbody>
              {accounts.map((a) => (
                <tr key={a.id} style={{ opacity: a.archived ? 0.55 : 1 }}>
                  <td><strong>{a.name}</strong>{a.archived && <span className="muted small"> (archived)</span>}</td>
                  <td className="muted">{ACCOUNT_KIND_LABELS[a.kind]}</td>
                  <td className={`amount num ${a.balance_cents < 0 ? 'negative' : ''}`}>{money(a.balance_cents)}</td>
                  <td className="muted small">
                    {a.checkin_every_days ? `Every ${a.checkin_every_days} days` : '—'}
                    {a.last_checkin_date && ` · last ${a.last_checkin_date}`}
                  </td>
                  <td className="amount">
                    {!a.archived && (
                      <button className="btn small ghost" onClick={() => checkNow(a.id)} title="Enter the real balance now">
                        Check balance
                      </button>
                    )}
                    <button className="btn small ghost" onClick={() => toggleArchive(a.id, a.archived)}>
                      {a.archived ? 'Restore' : 'Archive'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
