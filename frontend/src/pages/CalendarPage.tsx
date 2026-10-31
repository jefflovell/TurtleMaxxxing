import { useEffect, useState } from 'react'
import type { PageProps } from '../App'
import MonthPicker from '../components/MonthPicker'
import TaskEditor from '../components/TaskEditor'
import { api } from '../lib/api'
import { dayLabel, money, thisMonth } from '../lib/format'
import { STATUS_META } from '../lib/tasks'
import type { LedgerEvent, Task } from '../lib/types'

const DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const SHOW_KEY = 'turtle.calendar.show'

type Show = { bills: boolean; tasks: boolean }

function loadShow(): Show {
  try {
    const saved = JSON.parse(localStorage.getItem(SHOW_KEY) ?? '{}')
    return { bills: saved.bills !== false, tasks: saved.tasks !== false }
  } catch {
    return { bills: true, tasks: true }
  }
}

export default function CalendarPage({ accounts, rules, labels, lists, refresh, version }: PageProps) {
  const [month, setMonth] = useState(thisMonth())
  const [show, setShowState] = useState<Show>(loadShow)
  const [events, setEvents] = useState<LedgerEvent[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [today, setToday] = useState('')
  const [selected, setSelected] = useState<LedgerEvent | null>(null)
  const [editing, setEditing] = useState<Task | 'new' | null>(null)
  const [newOn, setNewOn] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const setShow = (next: Show) => {
    setShowState(next)
    try { localStorage.setItem(SHOW_KEY, JSON.stringify(next)) } catch { /* per-viewer convenience only */ }
  }

  const [year, mon] = month.split('-').map(Number)
  const daysInMonth = new Date(year, mon, 0).getDate()
  const firstDay = `${month}-01`
  const lastDay = `${month}-${String(daysInMonth).padStart(2, '0')}`

  useEffect(() => {
    Promise.all([api.calendar(month), api.tasksDue(firstDay, lastDay)])
      .then(([c, t]) => { setEvents(c.events); setToday(c.today); setTasks(t); setError(null) })
      .catch((err: Error) => setError(err.message))
  }, [month, firstDay, lastDay, version])

  const firstDow = new Date(year, mon - 1, 1).getDay()
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
  const tasksByDay = new Map<string, Task[]>()
  for (const t of tasks) {
    if (t.due_date) tasksByDay.set(t.due_date, [...(tasksByDay.get(t.due_date) ?? []), t])
  }

  const dueTotal = events
    .filter((e) => e.amount_cents < 0 && e.status !== 'confirmed')
    .reduce((sum, e) => sum + e.amount_cents, 0)
  const openTasks = tasks.filter((t) => t.status !== 'done').length
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

  function addTaskOn(iso: string) {
    setNewOn(iso)
    setEditing('new')
  }

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Calendar</h1>
          <p>
            Bills and tasks by day. Click a bill to mark it paid, a task to open it, or a day's number to add a task.
            {show.bills && <> Unpaid this month: <strong className="num">{money(Math.abs(dueTotal))}</strong>.</>}
            {show.tasks && <> Open tasks: <strong className="num">{openTasks}</strong>.</>}
          </p>
        </div>
        <div className="row">
          <div className="segmented" role="group" aria-label="Show on the calendar">
            <button aria-pressed={show.bills} onClick={() => setShow({ ...show, bills: !show.bills })}>💸 Bills</button>
            <button aria-pressed={show.tasks} onClick={() => setShow({ ...show, tasks: !show.tasks })}>✅ Tasks</button>
          </div>
          <MonthPicker month={month} onChange={setMonth} />
        </div>
      </div>
      {error && <div className="error" role="alert">{error}</div>}

      <div className="calendar" role="grid" aria-label="Bills and tasks by day">
        {DOW.map((d) => <div key={d} className="dow" role="columnheader">{d}</div>)}
        {cells.map((iso, i) => iso === null ? (
          <div key={`b${i}`} className="day blank" />
        ) : (
          <div key={iso} className={`day ${iso === today ? 'today' : ''}`} role="gridcell">
            <button className="date" onClick={() => addTaskOn(iso)} title={`Add a task on ${dayLabel(iso)}`}
              aria-label={`${dayLabel(iso)}: add a task`}>
              {Number(iso.slice(8))}
            </button>
            {show.tasks && (tasksByDay.get(iso) ?? []).map((t) => {
              const done = t.status === 'done'
              const late = !done && iso < today
              return (
                <button
                  key={`t${t.id}`}
                  className={`pill task ${done ? 'paid' : ''} ${late ? 'late' : ''}`}
                  onClick={() => setEditing(t)}
                  title={`${late ? 'Overdue. ' : ''}${STATUS_META[t.status].label}: ${t.title}${t.due_time ? ` at ${t.due_time}` : ''}${t.contacts.length ? `, with ${t.contacts.map((c) => c.name).join(', ')}` : ''}${t.is_private ? ' (Private)' : ''}`}
                >
                  {late && <span aria-label="Overdue">⚠ </span>}<span aria-hidden>{STATUS_META[t.status].icon}</span> {t.due_time && <span className="num">{t.due_time} </span>}
                  {t.title}{t.is_private && <span aria-label="Private"> 🔒</span>}
                </button>
              )
            })}
            {show.bills && (byDay.get(iso) ?? []).map((e, j) => {
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
      <p className="small muted">
        Tasks show their status icon ({Object.values(STATUS_META).map((m) => `${m.icon} ${m.label.toLowerCase()}`).join(', ')}).
        ⚠ means overdue. Money pills have a bar on the left: green for money in, gray for money out. ✓ means paid.
      </p>

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

      {editing && (
        <TaskEditor
          task={editing === 'new' ? null : editing}
          defaults={editing === 'new' && newOn ? { due_date: newOn } : undefined}
          labels={labels} lists={lists}
          onClose={() => setEditing(null)} onSaved={() => { setEditing(null); refresh() }}
        />
      )}
    </div>
  )
}
