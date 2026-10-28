import { useEffect, useMemo, useState } from 'react'
import {
  Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import type { PageProps } from '../App'
import EmptyState from '../components/EmptyState'
import MonthPicker from '../components/MonthPicker'
import StatusChip from '../components/StatusChip'
import { api } from '../lib/api'
import { dayLabel, money, thisMonth, todayIso } from '../lib/format'
import type { Cashflow, LedgerEvent } from '../lib/types'

interface Point {
  date: string
  day: number
  balance: number
  actual: number | null
  upcoming: number | null
  inCents: number
  outCents: number
  events: LedgerEvent[]
}

export default function CashFlowPage({ accounts, refresh, version, goTo }: PageProps) {
  const [month, setMonth] = useState(thisMonth())
  const spending = accounts.filter((a) => !a.archived && ['checking', 'savings', 'credit'].includes(a.kind))
  const [selected, setSelected] = useState<number[] | null>(null)
  const accountIds = selected ?? spending.filter((a) => a.kind === 'checking').map((a) => a.id)
  const [flow, setFlow] = useState<Cashflow | null>(null)
  const [error, setError] = useState<string | null>(null)

  const idsKey = accountIds.join(',')
  useEffect(() => {
    if (!idsKey) { setFlow(null); return }
    api.cashflow(month, idsKey.split(',').map(Number))
      .then((f) => { setFlow(f); setError(null) })
      .catch((err: Error) => setError(err.message))
  }, [month, idsKey, version])

  const points = useMemo<Point[]>(() => {
    if (!flow) return []
    const byDay = new Map<string, LedgerEvent[]>()
    flow.events.forEach((e) => byDay.set(e.date, [...(byDay.get(e.date) ?? []), e]))
    return flow.days.map((d, i) => {
      const next = flow.days[i + 1]
      return {
        date: d.date,
        day: Number(d.date.slice(8)),
        balance: d.balance_cents / 100,
        // The last actual day also starts the upcoming line, so the two join up.
        actual: d.projected ? null : d.balance_cents / 100,
        upcoming: d.projected || (next && next.projected) ? d.balance_cents / 100 : null,
        inCents: d.in_cents,
        outCents: d.out_cents,
        events: byDay.get(d.date) ?? [],
      }
    })
  }, [flow])

  const accountName = (id: number) => accounts.find((a) => a.id === id)?.name ?? '—'
  const today = todayIso()
  const lowIsNegative = (flow?.low_point.balance_cents ?? 0) < 0

  async function confirm(e: LedgerEvent) {
    try {
      // Confirming a rule date confirms every split of it at once.
      if (e.rule_id) await api.confirmOccurrence(e.rule_id, e.date)
      else if (e.entry_id) await api.confirmEntry(e.entry_id)
      refresh()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  if (accounts.length === 0) {
    return (
      <div className="stack">
        <h1>Cash flow</h1>
        <div className="card">
          <EmptyState>
            <p><strong>Welcome!</strong> Start by adding the accounts your money moves through, e.g. checking, HSA, a 529.</p>
            <button className="btn primary" onClick={() => goTo('accounts')}>Add your first account</button>
          </EmptyState>
        </div>
      </div>
    )
  }

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Cash flow</h1>
          <p>Your running balance through the month, with every bill and paycheck on its date.</p>
        </div>
        <MonthPicker month={month} onChange={setMonth} />
      </div>

      <div className="row" role="group" aria-label="Accounts to include">
        {spending.map((a) => (
          <label key={a.id} className="chip" style={{ cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={accountIds.includes(a.id)}
              onChange={(ev) => setSelected(
                ev.target.checked ? [...accountIds, a.id] : accountIds.filter((id) => id !== a.id),
              )}
            />
            {a.name}
          </label>
        ))}
      </div>

      {error && <div className="error" role="alert">{error}</div>}

      {!flow ? (
        <div className="card"><EmptyState>Pick at least one account to see its cash flow.</EmptyState></div>
      ) : (
        <>
          <div className="grid-3">
            <div className="card stat">
              <span className="label">Start of month</span>
              <span className="value num">{money(flow.start_balance_cents)}</span>
            </div>
            <div className="card stat">
              <span className="label">End of month{flow.days.some((d) => d.projected) ? ' (projected)' : ''}</span>
              <span className="value num">{money(flow.end_balance_cents)}</span>
            </div>
            <div className="card stat">
              <span className="label">Lowest point · {dayLabel(flow.low_point.date)}</span>
              <span className={`value num ${lowIsNegative ? 'negative' : ''}`}>
                {lowIsNegative ? '⚠ ' : ''}{money(flow.low_point.balance_cents)}
              </span>
              {lowIsNegative && <span className="small negative">Below zero. Consider moving a bill or transfer.</span>}
            </div>
          </div>

          <div className="card">
            <div className="row small muted" style={{ marginBottom: 8 }}>
              <span><svg width="22" height="8" aria-hidden><line x1="0" y1="4" x2="22" y2="4" stroke="var(--series-1)" strokeWidth="2" /></svg> Actual</span>
              <span><svg width="22" height="8" aria-hidden><line x1="0" y1="4" x2="22" y2="4" stroke="var(--series-1)" strokeWidth="2" strokeDasharray="4 3" /></svg> Upcoming</span>
            </div>
            <div style={{ width: '100%', height: 280 }}>
              <ResponsiveContainer>
                <AreaChart data={points} margin={{ top: 8, right: 12, bottom: 0, left: 8 }}>
                  <CartesianGrid stroke="var(--grid)" vertical={false} />
                  <XAxis dataKey="day" tick={{ fill: 'var(--text-2)', fontSize: 12 }} stroke="var(--axis)" tickLine={false} interval="preserveStartEnd" />
                  <YAxis
                    tick={{ fill: 'var(--text-2)', fontSize: 12 }} stroke="var(--axis)" tickLine={false} axisLine={false} width={70}
                    tickFormatter={(v: number) => money(v * 100).replace(/\.00$/, '')}
                  />
                  {lowIsNegative && (
                    <ReferenceLine y={0} stroke="var(--critical)" strokeWidth={1} label={{ value: '$0', fill: 'var(--text-2)', fontSize: 11, position: 'insideTopLeft' }} />
                  )}
                  {today.startsWith(month) && (
                    <ReferenceLine x={Number(today.slice(8))} stroke="var(--axis)" label={{ value: 'Today', fill: 'var(--text-2)', fontSize: 11, position: 'insideTop' }} />
                  )}
                  <Tooltip content={<ChartTooltip />} cursor={{ stroke: 'var(--axis)' }} />
                  <Area type="stepAfter" dataKey="actual" stroke="var(--series-1)" strokeWidth={2} fill="var(--series-1)" fillOpacity={0.1} connectNulls={false} isAnimationActive={false} activeDot={{ r: 4 }} />
                  <Area type="stepAfter" dataKey="upcoming" stroke="var(--series-1)" strokeWidth={2} strokeDasharray="5 4" fill="var(--series-1)" fillOpacity={0.05} connectNulls={false} isAnimationActive={false} activeDot={{ r: 4 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card">
            <h2 style={{ marginBottom: 10 }}>This month's money moves</h2>
            {flow.events.length === 0 ? (
              <EmptyState>
                Nothing scheduled yet.{' '}
                <button className="btn small" onClick={() => goTo('rules')}>Add a paycheck or bill</button>
              </EmptyState>
            ) : (
              <table>
                <thead>
                  <tr><th>Date</th><th>What</th><th>Account</th><th className="amount">Amount</th><th>Status</th><th /></tr>
                </thead>
                <tbody>
                  {flow.events.map((e, i) => (
                    <tr key={`${e.entry_id ?? 'p'}-${e.rule_id}-${e.date}-${e.account_id}-${i}`}>
                      <td className="num">{dayLabel(e.date)}</td>
                      <td>{e.description}</td>
                      <td className="muted">{accountName(e.account_id)}</td>
                      <td className={`amount num ${e.amount_cents >= 0 ? 'positive' : ''}`}>
                        {e.amount_cents >= 0 ? '+' : ''}{money(e.amount_cents)}
                      </td>
                      <td><StatusChip status={e.status} /></td>
                      <td>
                        {(e.status === 'expected' || (e.status === 'projected' && e.rule_kind !== 'income')) && (
                          <button className="btn small" onClick={() => confirm(e)}>
                            {e.status === 'expected' ? 'Confirm' : 'Paid early'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: Point }[] }) {
  if (!active || !payload?.length) return null
  const p = payload[0].payload
  return (
    <div className="chart-tooltip">
      <div><strong>{dayLabel(p.date)}</strong></div>
      <div className="num">Balance: <strong>{money(Math.round(p.balance * 100))}</strong></div>
      {p.events.map((e, i) => (
        <div key={i} className="small muted num">
          {e.amount_cents >= 0 ? '+' : ''}{money(e.amount_cents)} · {e.description}
        </div>
      ))}
    </div>
  )
}
