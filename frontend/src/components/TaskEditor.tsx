import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { STATUSES, STATUS_META } from '../lib/tasks'
import type { Contact, Label, Task, TaskList, TaskStatus } from '../lib/types'
import { LabelPicker, PeoplePicker } from './TaskBits'

interface Props {
  task: Task | null          // null = new task
  labels: Label[]
  lists: TaskList[]
  defaults?: Partial<Task>
  onClose: () => void
  onSaved: () => void
}

export default function TaskEditor({ task, labels, lists, defaults, onClose, onSaved }: Props) {
  const start = task ?? defaults ?? {}
  const [title, setTitle] = useState(start.title ?? '')
  const [notes, setNotes] = useState(start.notes ?? '')
  const [status, setStatus] = useState<TaskStatus>(start.status ?? 'todo')
  const [blockedNote, setBlockedNote] = useState(start.blocked_note ?? '')
  const [listId, setListId] = useState<string>(start.list_id ? String(start.list_id) : '')
  const [dueDate, setDueDate] = useState(start.due_date ?? '')
  const [dueTime, setDueTime] = useState(start.due_time ?? '')
  const [isPrivate, setIsPrivate] = useState(start.private ?? false)
  const [labelIds, setLabelIds] = useState<number[]>((start.labels ?? []).map((l) => l.id))
  const [contactIds, setContactIds] = useState<number[]>((start.contacts ?? []).map((c) => c.id))
  const [contacts, setContacts] = useState<Contact[]>([])
  const [reminders, setReminders] = useState<string[]>((start.reminders ?? []).map((r) => r.remind_at))
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.contacts().then(setContacts).catch(() => { /* the picker just stays empty */ })
  }, [])

  async function createContact(name: string) {
    const created = await api.createContact({ name })
    setContacts((cs) => [...cs, created])
    return created
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const autoPrivate = labels.filter((l) => labelIds.includes(l.id) && l.auto_private)
  const willBePrivate = isPrivate || autoPrivate.length > 0

  async function save(e: React.FormEvent) {
    e.preventDefault()
    const body = {
      title: title.trim(),
      notes,
      status,
      blocked_note: status === 'blocked' ? blockedNote.trim() || null : null,
      list_id: listId ? Number(listId) : null,
      due_date: dueDate || null,
      due_time: dueDate && dueTime ? dueTime : null,
      private: isPrivate,
      label_ids: labelIds,
      contact_ids: contactIds,
      reminders: reminders.filter(Boolean),
    }
    try {
      if (task) await api.updateTask(task.id, body)
      else await api.createTask(body)
      onSaved()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function remove() {
    if (!task || !confirm(`Delete "${task.title}"? This can't be undone.`)) return
    await api.deleteTask(task.id)
    onSaved()
  }

  return (
    <div className="overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <form className="dialog stack" onSubmit={save} role="dialog" aria-modal="true" aria-label={task ? 'Edit task' : 'New task'}>
        <h2>{task ? 'Edit task' : 'New task'}</h2>
        <label className="field">Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} required autoFocus maxLength={200} />
        </label>

        <div className="form-grid">
          <label className="field">Status
            <select value={status} onChange={(e) => setStatus(e.target.value as TaskStatus)}>
              {STATUSES.map((s) => <option key={s} value={s}>{STATUS_META[s].icon} {STATUS_META[s].label}</option>)}
            </select>
          </label>
          <label className="field">List
            <select value={listId} onChange={(e) => setListId(e.target.value)}>
              <option value="">📥 Inbox</option>
              {lists.filter((l) => !l.archived || String(l.id) === listId).map((l) => (
                <option key={l.id} value={l.id}>{l.emoji ?? '📋'} {l.name}</option>
              ))}
            </select>
          </label>
          <label className="field">Due date
            <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </label>
          <label className="field">Time <span className="muted">(optional)</span>
            <input type="time" value={dueTime} onChange={(e) => setDueTime(e.target.value)} disabled={!dueDate} />
          </label>
        </div>

        {status === 'blocked' && (
          <label className="field">Blocked by
            <input value={blockedNote} onChange={(e) => setBlockedNote(e.target.value)} placeholder="e.g. waiting on the landlord" maxLength={300} />
          </label>
        )}

        <div className="stack" style={{ gap: 4 }}>
          <span className="small muted">Labels</span>
          <LabelPicker labels={labels} selected={labelIds} onChange={setLabelIds} />
        </div>

        <div className="stack" style={{ gap: 4 }}>
          <span className="small muted">People</span>
          <PeoplePicker contacts={contacts} selected={contactIds} onChange={setContactIds} onCreate={createContact} />
        </div>

        <div className="stack" style={{ gap: 6 }}>
          <span className="small muted">Reminders</span>
          {reminders.map((r, i) => (
            <div className="row" key={i}>
              <input type="datetime-local" value={r} aria-label={`Reminder ${i + 1}`}
                onChange={(e) => setReminders(reminders.map((x, j) => (j === i ? e.target.value : x)))} />
              <button type="button" className="btn small ghost" aria-label="Remove reminder"
                onClick={() => setReminders(reminders.filter((_, j) => j !== i))}>✕</button>
            </div>
          ))}
          <div className="row">
            <button type="button" className="btn small" onClick={() => setReminders([...reminders, defaultReminder(dueDate, dueTime)])}>
              + Add reminder
            </button>
          </div>
        </div>

        <label className="field">Notes
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={5000} />
        </label>

        <div className="stack" style={{ gap: 4 }}>
          <label className="toggle">
            <input type="checkbox" checked={isPrivate} onChange={(e) => setIsPrivate(e.target.checked)} />
            🔒 Private: never share this task with AI
          </label>
          {!isPrivate && autoPrivate.length > 0 && (
            <span className="small muted">Already Private because of the label "{autoPrivate[0].name}".</span>
          )}
          {!willBePrivate && (
            <span className="small muted">Tip: if you wouldn't write it on a sticky note on your fridge, make it Private.</span>
          )}
        </div>

        {error && <div className="error" role="alert">{error}</div>}
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <div className="row">
            <button className="btn primary" type="submit">{task ? 'Save' : 'Add task'}</button>
            <button className="btn" type="button" onClick={onClose}>Cancel</button>
          </div>
          {task && <button className="btn ghost" type="button" onClick={remove}>Delete</button>}
        </div>
      </form>
    </div>
  )
}

/** A sensible first reminder: 9am on the due date, or an hour before a timed task. */
function defaultReminder(dueDate: string, dueTime: string): string {
  if (dueDate && dueTime) {
    const [h, m] = dueTime.split(':').map(Number)
    const hour = Math.max(0, h - 1)
    return `${dueDate}T${String(hour).padStart(2, '0')}:${String(m).padStart(2, '0')}`
  }
  if (dueDate) return `${dueDate}T09:00`
  const tomorrow = new Date(Date.now() + 86400000)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${tomorrow.getFullYear()}-${pad(tomorrow.getMonth() + 1)}-${pad(tomorrow.getDate())}T09:00`
}
