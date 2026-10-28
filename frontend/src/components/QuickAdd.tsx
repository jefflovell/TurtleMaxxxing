import { useState } from 'react'
import { api } from '../lib/api'
import { todayIso } from '../lib/format'
import type { Label } from '../lib/types'

/** One line to add a task: title, optional date, and favorite labels as one-click chips. */
export default function QuickAdd({
  labels, listId, onAdded,
}: { labels: Label[]; listId?: number | null; onAdded: () => void }) {
  const [title, setTitle] = useState('')
  const [due, setDue] = useState('')
  const [picked, setPicked] = useState<number[]>([])
  const [error, setError] = useState<string | null>(null)
  const favorites = labels.filter((l) => l.favorite)

  async function add(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    try {
      await api.createTask({ title: title.trim(), due_date: due || null, label_ids: picked, list_id: listId ?? null })
      setTitle(''); setDue(''); setPicked([]); setError(null)
      onAdded()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <form className="card stack" style={{ gap: 8 }} onSubmit={add}>
      <div className="quick-add">
        <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Add a task… e.g. Call the plumber" aria-label="New task" />
        <input type="date" value={due} onChange={(e) => setDue(e.target.value)} aria-label="Due date" />
        <button type="button" className="btn small" onClick={() => setDue(todayIso())}>Today</button>
        <button type="submit" className="btn primary">Add</button>
      </div>
      {favorites.length > 0 && (
        <div className="row" style={{ gap: 6 }}>
          {favorites.map((l) => (
            <button
              type="button" key={l.id} className="label-chip" aria-pressed={picked.includes(l.id)}
              onClick={() => setPicked(picked.includes(l.id) ? picked.filter((x) => x !== l.id) : [...picked, l.id])}
            >
              <span className="dot" style={{ background: `var(--label-${l.color})` }} aria-hidden />
              {l.emoji && <span aria-hidden>{l.emoji}</span>}{l.name}
            </button>
          ))}
        </div>
      )}
      {error && <div className="error" role="alert">{error}</div>}
    </form>
  )
}
