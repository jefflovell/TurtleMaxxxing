import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { dayLabel } from '../lib/format'
import type { DueReminder } from '../lib/types'

const CHECK_EVERY_MS = 30_000

/** Shows task reminders when they come due, while the app is open. */
export default function ReminderToasts({ version, onChanged }: { version: number; onChanged: () => void }) {
  const [due, setDue] = useState<DueReminder[]>([])

  useEffect(() => {
    let alive = true
    const check = () => api.dueReminders().then((d) => { if (alive) setDue(d) }).catch(() => { /* backend restarting */ })
    check()
    const timer = window.setInterval(check, CHECK_EVERY_MS)
    return () => { alive = false; window.clearInterval(timer) }
  }, [version])

  async function act(action: () => Promise<unknown>, id: number) {
    setDue((d) => d.filter((x) => x.reminder_id !== id))
    await action()
    onChanged()
  }

  if (due.length === 0) return null
  return (
    <div className="toasts" role="status" aria-live="polite">
      {due.slice(0, 3).map((r) => (
        <div className="toast stack" style={{ gap: 6 }} key={r.reminder_id}>
          <div><strong>🔔 {r.task.title}</strong></div>
          {r.task.due_date && <div className="small muted">Due {dayLabel(r.task.due_date)}{r.task.due_time ? ` at ${r.task.due_time}` : ''}</div>}
          <div className="row" style={{ gap: 6 }}>
            <button className="btn small primary" onClick={() => act(() => api.updateTask(r.task.id, { status: 'done' }), r.reminder_id)}>✓ Done</button>
            <button className="btn small" onClick={() => act(() => api.snoozeReminder(r.reminder_id, 10), r.reminder_id)}>10 min</button>
            <button className="btn small" onClick={() => act(() => api.snoozeReminder(r.reminder_id, 60), r.reminder_id)}>1 hour</button>
            <button className="btn small ghost" onClick={() => act(() => api.dismissReminder(r.reminder_id), r.reminder_id)}>Dismiss</button>
          </div>
        </div>
      ))}
      {due.length > 3 && <div className="toast small">+ {due.length - 3} more reminders</div>}
    </div>
  )
}
