import { useEffect, useState } from 'react'
import type { PageProps } from '../App'
import EmptyState from '../components/EmptyState'
import { LabelChip, LabelPicker } from '../components/TaskBits'
import TaskEditor from '../components/TaskEditor'
import { api } from '../lib/api'
import { dayLabel } from '../lib/format'
import { STATUS_META } from '../lib/tasks'
import type { Contact, Label, Task } from '../lib/types'

export default function ContactsPage({ labels, lists, refresh, version }: PageProps) {
  const [q, setQ] = useState('')
  const [labelIds, setLabelIds] = useState<number[]>([])
  const [contacts, setContacts] = useState<Contact[] | null>(null)
  const [editing, setEditing] = useState<Contact | 'new' | null>(null)
  const [error, setError] = useState<string | null>(null)

  const key = JSON.stringify([q.trim(), labelIds])
  useEffect(() => {
    const [query, ids] = JSON.parse(key) as [string, number[]]
    api.contacts(query, ids)
      .then((c) => { setContacts(c); setError(null) })
      .catch((err: Error) => setError(err.message))
  }, [key, version])

  const toggle = (id: number) => setLabelIds(labelIds.includes(id) ? labelIds.filter((x) => x !== id) : [...labelIds, id])
  const usedLabels = labels.filter((l) => contacts?.some((c) => c.labels.some((x) => x.id === l.id)) || labelIds.includes(l.id))

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Contacts</h1>
          <p>The people your tasks are about, and where to find them. Add someone to a task from the task's People field.</p>
        </div>
        <button className="btn primary" onClick={() => setEditing('new')}>+ New contact</button>
      </div>

      <div className="toolbar">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name, organization, place"
          aria-label="Search contacts" style={{ width: 240 }} />
        {usedLabels.map((l) => (
          <button key={l.id} className="label-chip" aria-pressed={labelIds.includes(l.id)} onClick={() => toggle(l.id)}>
            <span className="dot" style={{ background: `var(--label-${l.color})` }} aria-hidden />
            {l.emoji && <span aria-hidden>{l.emoji}</span>}{l.name}
          </button>
        ))}
      </div>
      {error && <div className="error" role="alert">{error}</div>}

      <div className="card table-wrap">
        {contacts === null ? (
          <p className="muted" style={{ padding: 12 }}>Loading…</p>
        ) : contacts.length === 0 ? (
          <EmptyState>{q || labelIds.length ? 'No contacts match.' : 'No contacts yet. Add the people you meet, call or work with.'}</EmptyState>
        ) : (
          <table>
            <thead>
              <tr><th>Name</th><th>Organization</th><th>Where</th><th>Phone / email</th><th>Labels</th><th className="amount">Open tasks</th></tr>
            </thead>
            <tbody>
              {contacts.map((c) => (
                <tr key={c.id}>
                  <td>
                    <button className="contact-name" onClick={() => setEditing(c)}>{c.name}</button>
                    {c.is_private && <span title="Private: never shared with AI"> 🔒</span>}
                    {c.role && <div className="small muted">{c.role}</div>}
                  </td>
                  <td>{c.organization || <span className="muted">—</span>}</td>
                  <td className="small">{c.location || <span className="muted">—</span>}</td>
                  <td className="small">
                    {c.phone && <div className="num">{c.phone}</div>}
                    {c.email && <div>{c.email}</div>}
                    {!c.phone && !c.email && <span className="muted">—</span>}
                  </td>
                  <td><div className="row" style={{ gap: 4 }}>{c.labels.map((l) => <LabelChip key={l.id} label={l} />)}</div></td>
                  <td className="amount num">{c.open_task_count || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {editing && (
        <ContactEditor
          contact={editing === 'new' ? null : editing}
          labels={labels} lists={lists}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); refresh() }}
          onChanged={refresh}
        />
      )}
    </div>
  )
}

function ContactEditor({ contact, labels, lists, onClose, onSaved, onChanged }: {
  contact: Contact | null
  labels: Label[]
  lists: PageProps['lists']
  onClose: () => void
  onSaved: () => void
  onChanged: () => void
}) {
  const start = contact ?? ({} as Partial<Contact>)
  const [name, setName] = useState(start.name ?? '')
  const [organization, setOrganization] = useState(start.organization ?? '')
  const [role, setRole] = useState(start.role ?? '')
  const [email, setEmail] = useState(start.email ?? '')
  const [phone, setPhone] = useState(start.phone ?? '')
  const [location, setLocation] = useState(start.location ?? '')
  const [notes, setNotes] = useState(start.notes ?? '')
  const [isPrivate, setIsPrivate] = useState(start.private ?? false)
  const [labelIds, setLabelIds] = useState<number[]>((start.labels ?? []).map((l) => l.id))
  const [tasks, setTasks] = useState<Task[]>([])
  const [openTask, setOpenTask] = useState<Task | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (contact) api.contact(contact.id).then((c) => setTasks(c.tasks ?? [])).catch(() => { /* list stays empty */ })
  }, [contact])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && !openTask) onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose, openTask])

  const autoPrivate = labels.filter((l) => labelIds.includes(l.id) && l.auto_private)

  async function save(e: React.FormEvent) {
    e.preventDefault()
    const body = {
      name: name.trim(), organization, role, email: email.trim(), phone, location, notes,
      private: isPrivate, label_ids: labelIds,
    }
    try {
      if (contact) await api.updateContact(contact.id, body)
      else await api.createContact(body)
      onSaved()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function remove() {
    if (!contact || !confirm(`Delete ${contact.name}? They'll be removed from their tasks; the tasks stay.`)) return
    await api.deleteContact(contact.id)
    onSaved()
  }

  return (
    <div className="overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <form className="dialog stack" onSubmit={save} role="dialog" aria-modal="true" aria-label={contact ? 'Edit contact' : 'New contact'}>
        <h2>{contact ? 'Edit contact' : 'New contact'}</h2>
        <div className="form-grid">
          <label className="field">Name
            <input value={name} onChange={(e) => setName(e.target.value)} required autoFocus maxLength={100} placeholder="e.g. Mr. Anderson" />
          </label>
          <label className="field">Organization
            <input value={organization} onChange={(e) => setOrganization(e.target.value)} maxLength={100} placeholder="e.g. Smith Agency" />
          </label>
          <label className="field">Role
            <input value={role} onChange={(e) => setRole(e.target.value)} maxLength={100} placeholder="e.g. Project manager" />
          </label>
          <label className="field">Where
            <input value={location} onChange={(e) => setLocation(e.target.value)} maxLength={200} placeholder="Where you meet them" />
          </label>
          <label className="field">Phone
            <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} maxLength={40} />
          </label>
          <label className="field">Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} maxLength={200} />
          </label>
        </div>

        <div className="stack" style={{ gap: 4 }}>
          <span className="small muted">Labels</span>
          <LabelPicker labels={labels} selected={labelIds} onChange={setLabelIds} />
        </div>

        <label className="field">Notes
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={2000} />
        </label>

        <div className="stack" style={{ gap: 4 }}>
          <label className="toggle">
            <input type="checkbox" checked={isPrivate} onChange={(e) => setIsPrivate(e.target.checked)} />
            🔒 Private: never share this person with AI
          </label>
          {!isPrivate && autoPrivate.length > 0 && (
            <span className="small muted">Already Private because of the label "{autoPrivate[0].name}".</span>
          )}
        </div>

        {contact && (
          <div className="stack" style={{ gap: 4 }}>
            <span className="small muted">Tasks with {contact.name}</span>
            {tasks.length === 0 ? <span className="small muted">None yet.</span> : tasks.map((t) => (
              <button type="button" key={t.id} className="contact-name small" style={{ fontWeight: 400 }} onClick={() => setOpenTask(t)}>
                {STATUS_META[t.status].icon} {t.title}{t.due_date && <span className="muted"> · {dayLabel(t.due_date)}</span>}
              </button>
            ))}
          </div>
        )}

        {error && <div className="error" role="alert">{error}</div>}
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <div className="row">
            <button className="btn primary" type="submit">{contact ? 'Save' : 'Add contact'}</button>
            <button className="btn" type="button" onClick={onClose}>Cancel</button>
          </div>
          {contact && <button className="btn ghost" type="button" onClick={remove}>Delete</button>}
        </div>
      </form>

      {openTask && (
        <TaskEditor
          task={openTask} labels={labels} lists={lists}
          onClose={() => setOpenTask(null)}
          onSaved={() => {
            setOpenTask(null)
            if (contact) api.contact(contact.id).then((c) => setTasks(c.tasks ?? [])).catch(() => {})
            onChanged()
          }}
        />
      )}
    </div>
  )
}
