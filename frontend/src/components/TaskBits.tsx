// Small shared pieces for tasks: label chips, status, due date and the label picker.

import { useState } from 'react'
import { dayLabel } from '../lib/format'
import { STATUS_META } from '../lib/tasks'
import type { Contact, ContactSummary, Label, Task, TaskStatus } from '../lib/types'

export function LabelChip({ label }: { label: Label }) {
  return (
    <span className="label-chip" title={label.auto_private ? 'Auto-Private: hidden from AI' : undefined}>
      <span className="dot" style={{ background: `var(--label-${label.color})` }} aria-hidden />
      {label.emoji && <span aria-hidden>{label.emoji}</span>}
      {label.name}
    </span>
  )
}

export function StatusText({ status }: { status: TaskStatus }) {
  const meta = STATUS_META[status]
  return <span className={`status ${status}`}><span aria-hidden>{meta.icon}</span>{meta.label}</span>
}

export function DueText({ task, today }: { task: Task; today: string }) {
  if (!task.due_date) return null
  const overdue = task.status !== 'done' && task.due_date < today
  const when = task.due_date === today ? 'Today' : dayLabel(task.due_date)
  return (
    <span className={`due ${overdue ? 'overdue' : ''}`}>
      {overdue ? '⚠ Overdue · ' : '📅 '}{when}{task.due_time ? ` · ${task.due_time}` : ''}
    </span>
  )
}

/** "👤 Mr. Anderson · Smith Agency", with 🔒 on people who are Private. */
export function PeopleChips({ people }: { people: ContactSummary[] }) {
  return (
    <>
      {people.map((p) => (
        <span key={p.id} className="small muted person" title={[p.role, p.organization, p.location].filter(Boolean).join(' · ')}>
          👤 {p.name}{p.organization && ` · ${p.organization}`}{p.is_private && <span aria-label="Private"> 🔒</span>}
        </span>
      ))}
    </>
  )
}

/** Pick people for a task: type to find someone, or add a new name on the spot. */
export function PeoplePicker({
  contacts, selected, onChange, onCreate,
}: {
  contacts: Contact[]
  selected: number[]
  onChange: (ids: number[]) => void
  onCreate: (name: string) => Promise<Contact>
}) {
  const [search, setSearch] = useState('')
  const term = search.trim().toLowerCase()
  const matches = term
    ? contacts.filter((c) => !selected.includes(c.id)
      && `${c.name} ${c.organization}`.toLowerCase().includes(term)).slice(0, 6)
    : []
  const exact = contacts.some((c) => c.name.toLowerCase() === term)
  const add = (id: number) => { onChange([...selected, id]); setSearch('') }

  return (
    <div className="stack" style={{ gap: 6 }}>
      <div className="row" style={{ gap: 6 }}>
        {selected.map((id) => {
          const c = contacts.find((x) => x.id === id)
          if (!c) return null
          return (
            <span key={id} className="label-chip">
              👤 {c.name}{c.organization && <span className="muted"> · {c.organization}</span>}{c.is_private && ' 🔒'}
              <button type="button" className="btn small ghost" aria-label={`Remove ${c.name}`}
                onClick={() => onChange(selected.filter((x) => x !== id))}>✕</button>
            </span>
          )
        })}
        <input placeholder="Add a person" value={search} onChange={(e) => setSearch(e.target.value)}
          aria-label="Add a person" style={{ width: 180 }}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); if (matches[0]) add(matches[0].id) } }} />
      </div>
      {term && (
        <div className="row" style={{ gap: 6 }}>
          {matches.map((c) => (
            <button type="button" key={c.id} className="label-chip" onClick={() => add(c.id)}>
              + {c.name}{c.organization && <span className="muted"> · {c.organization}</span>}
            </button>
          ))}
          {!exact && (
            <button type="button" className="btn small" onClick={async () => add((await onCreate(search.trim())).id)}>
              + New contact "{search.trim()}"
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export function PrivateBadge({ task }: { task: Task }) {
  if (!task.is_private) return null
  return <span className="label-chip" title="Private: never shared with AI">🔒 Private</span>
}

/** Favorites as one-click chips; everything else behind a searchable "More labels". */
export function LabelPicker({
  labels, selected, onChange,
}: { labels: Label[]; selected: number[]; onChange: (ids: number[]) => void }) {
  const [more, setMore] = useState(false)
  const [search, setSearch] = useState('')
  const favorites = labels.filter((l) => l.favorite)
  const others = labels.filter((l) => !l.favorite)
  const toggle = (id: number) =>
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id])

  const chip = (l: Label) => (
    <button
      type="button" key={l.id} className="label-chip" aria-pressed={selected.includes(l.id)}
      onClick={() => toggle(l.id)} title={l.auto_private ? 'Auto-Private: tasks with this label are hidden from AI' : undefined}
    >
      <span className="dot" style={{ background: `var(--label-${l.color})` }} aria-hidden />
      {l.emoji && <span aria-hidden>{l.emoji}</span>}
      {l.name}{l.auto_private ? ' 🔒' : ''}
    </button>
  )

  const selectedOthers = others.filter((l) => selected.includes(l.id))
  const shownOthers = others.filter((l) => l.name.includes(search.trim().toLowerCase()))

  return (
    <div className="stack" style={{ gap: 6 }}>
      <div className="row" style={{ gap: 6 }}>
        {favorites.map(chip)}
        {!more && selectedOthers.map(chip)}
        {others.length > 0 && (
          <button type="button" className="btn small ghost" onClick={() => setMore(!more)} aria-expanded={more}>
            {more ? 'Fewer' : 'More labels…'}
          </button>
        )}
      </div>
      {more && (
        <div className="row" style={{ gap: 6 }}>
          <input placeholder="Search labels" value={search} onChange={(e) => setSearch(e.target.value)} style={{ width: 160 }} aria-label="Search labels" />
          {shownOthers.map(chip)}
        </div>
      )}
    </div>
  )
}
