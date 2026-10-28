import { useEffect, useState } from 'react'
import type { PageProps } from '../App'
import MonthPicker from '../components/MonthPicker'
import { api } from '../lib/api'
import { dayLabel, money, thisMonth } from '../lib/format'
import type { LedgerEvent } from '../lib/types'

const DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export default function BillsCalendarPage({ accounts, rules, refresh, version }: PageProps) {
  const [month, setMonth] = useState(thisMonth())
  const [events, setEvents] = useState<LedgerEvent[]>([])
  const [today, setToday] = useState('')
  const [selected, setSelected] = useState<LedgerEvent | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.calendar(month)
      .then((c) => { setEvents(c.events); setToday(c.today); setError(null) })
      .catch((err: Error) => setError(err.message))
  }, [month, version])

  const [year, mon] = month.split('-').map(Number)
  const firstDow = new Date(year, mon - 1, 1).getDay()
  const daysInMonth = new Date(year, mon, 0).getDate()
  const cells: (string | null)[] = [
    ...Array(firstDow).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => `${month}-${String(i + 1).padStart(2, '0')}`),
  ]

  // Show one pill per rule occurrence (income splits fan out to several accounts).
  const byDay = new Map<string, LedgerEvent[]>()
  for (const e of events) {
    const list = byDay.get(e.date) ?? []
    const isSplitLeg = e.rule_kind === 'income' && list.some((x) => x.rule_id === e.rule_id)
    if (!isSplitLeg) byDay.set(e.date, [...list, e])
  }

  const dueTotal = events
    .filter((e) => e.amount_cents < 0 && e.status !== 'confirmed')
    .reduce((sum, e) => sum + e.amount_cents, 0)
  const accountName = (id: number) => accounts.find((a) => a.id === id)?.name ?? '—'
  // Income shows the whole paycheck, not just one split.
  const shownAmount = (e: LedgerEvent) =>
    e.rule_kind === 'income'
      ? rules.find((r) => r.id === e.rule_id)?.amount_cents ?? e.amount_cents
      : Math.abs(e.amount_cents)

  async function markPaid(e: LedgerEvent) {
    try {
      // Confirming a rule date confirms every split of it at once.
      if (e.rule_id) await api.confirmOccurrence(e.rule_id, e.date)
      else if (e.entry_id) await api.confirmEntry(e.entry_id)
      setSelected(null)
      refresh()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Bills calendar</h1>
          <p>What's due when. Click a bill to mark it paid. Still unpaid this month: <strong className="num">{money(Math.abs(dueTotal))}</strong></p>
        </div>
        <MonthPicker month={month} onChange={setMonth} />
      </div>
      {error && <div className="error" role="alert">{error}</div>}

      <div className="calendar" role="grid" aria-label="Bills by day">
        {DOW.map((d) => <div key={d} className="dow" role="columnheader">{d}</div>)}
        {cells.map((iso, i) => iso === null ? (
          <div key={`b${i}`} className="day blank" />
        ) : (
          <div key={iso} className={`day ${iso === today ? 'today' : ''}`} role="gridcell">
            <span className="date">{Number(iso.slice(8))}</span>
            {(byDay.get(iso) ?? []).map((e, j) => {
              const paid = e.status === 'confirmed'
              const income = e.rule_kind === 'income'
              return (
                <button
                  key={j}
                  className={`pill ${income ? 'income' : 'out'} ${paid ? 'paid' : ''}`}
                  onClick={() => setSelected(e)}
                  title={`${e.description.split(':')[0]}: ${money(shownAmount(e))}${paid ? ' (paid)' : ''}`}
                >
                  {paid ? '✓ ' : ''}{e.description.split(':')[0]} {money(shownAmount(e)).replace(/\.00$/, '')}
                </button>
              )
            })}
          </div>
        ))}
      </div>

      {selected && (
        <div className="card row" style={{ justifyContent: 'space-between' }} role="dialog" aria-label="Bill details">
          <div>
            <h3>{selected.description.split(':')[0]}</h3>
            <div className="muted small">
              {dayLabel(selected.date)} · {accountName(selected.account_id)} ·{' '}
              <span className="num">{money(shownAmount(selected))}</span> ·{' '}
              {selected.status === 'confirmed' ? '✓ Paid' : selected.status === 'expected' ? 'Due, not confirmed' : 'Upcoming'}
            </div>
          </div>
          <div className="row">
            {selected.status !== 'confirmed' && (
              <button className="btn primary" onClick={() => markPaid(selected)}>
                {selected.rule_kind === 'income' ? 'Mark received' : 'Mark paid'}
              </button>
            )}
            <button className="btn" onClick={() => setSelected(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  )
}
