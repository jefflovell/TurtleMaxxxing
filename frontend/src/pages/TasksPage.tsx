import { useEffect, useState } from 'react'
import type { PageProps } from '../App'
import EmptyState from '../components/EmptyState'
import QuickAdd from '../components/QuickAdd'
import { DueText, LabelChip, PrivateBadge } from '../components/TaskBits'
import TaskEditor from '../components/TaskEditor'
import TaskRow from '../components/TaskRow'
import { api } from '../lib/api'
import { todayIso } from '../lib/format'
import { STATUSES, STATUS_META } from '../lib/tasks'
import type { FilterSpec, Task, TaskStatus } from '../lib/types'

type View = 'list' | 'board'
type Scope = 'all' | 'inbox' | number

const VIEW_KEY = 'turtle.tasks.view'

function loadView(): View {
  try { return localStorage.getItem(VIEW_KEY) === 'board' ? 'board' : 'list' } catch { return 'list' }
}

export default function TasksPage({ labels, lists, activeFilter, refresh, version, goTo }: PageProps) {
  // Opened from a saved filter: start from it. App remounts this page per filter.
  const saved = activeFilter?.filters
  const [view, setViewState] = useState<View>(saved?.view ?? loadView)
  const [scope, setScope] = useState<Scope>(saved?.scope ?? 'all')
  const [statuses, setStatuses] = useState<TaskStatus[]>(saved?.statuses ?? [])
  const [labelIds, setLabelIds] = useState<number[]>(saved?.label_ids ?? [])
  const [q, setQ] = useState(saved?.q ?? '')
  const [tasks, setTasks] = useState<Task[] | null>(null)
  const [editing, setEditing] = useState<Task | 'new' | null>(null)
  const [error, setError] = useState<string | null>(null)
  const today = todayIso()

  const setView = (v: View) => {
    setViewState(v)
    try { localStorage.setItem(VIEW_KEY, v) } catch { /* per-viewer convenience only */ }
  }

  const filterKey = JSON.stringify([scope, statuses, labelIds, q, view])
  useEffect(() => {
    const [s, st, li, query, v] = JSON.parse(filterKey) as [Scope, TaskStatus[], number[], string, View]
    api.tasks({
      listId: s === 'all' ? null : s,
      // The board always shows every column; the status filter is for the list.
      status: v === 'list' && st.length ? st : undefined,
      labelIds: li,
      q: query.trim() || undefined,
    })
      .then((t) => { setTasks(t); setError(null) })
      .catch((err: Error) => setError(err.message))
  }, [filterKey, version])

  const activeLists = lists.filter((l) => !l.archived)
  const currentList = typeof scope === 'number' ? lists.find((l) => l.id === scope) : undefined

  async function newList() {
    const name = prompt('Name for the new list, e.g. "Home reno"')
    if (!name?.trim()) return
    const created = await api.createList(name.trim())
    refresh()
    setScope(created.id)
  }

  const toggle = <T,>(xs: T[], x: T) => (xs.includes(x) ? xs.filter((y) => y !== x) : [...xs, x])
  const filtersOn = statuses.length > 0 || labelIds.length > 0 || q.trim() !== ''

  const spec: FilterSpec = { scope, statuses, label_ids: labelIds, q: q.trim(), view }
  const changed = activeFilter !== null && JSON.stringify(spec) !== JSON.stringify(activeFilter.filters)

  async function saveFilter() {
    const name = prompt('Name for this saved filter, e.g. "Critical work"')
    if (!name?.trim()) return
    try {
      await api.createFilter(name.trim(), spec)
      refresh()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function updateFilter() {
    if (!activeFilter) return
    await api.updateFilter(activeFilter.id, { filters: spec })
    refresh()
  }

  async function removeFilter() {
    if (!activeFilter || !confirm(`Remove the saved filter "${activeFilter.name}"? Your tasks stay.`)) return
    await api.deleteFilter(activeFilter.id)
    goTo('tasks')
    refresh()
  }

  const heading = activeFilter
    ? `${activeFilter.emoji ?? '⭐'} ${activeFilter.name}`
    : currentList ? `${currentList.emoji ?? '📋'} ${currentList.name}` : scope === 'inbox' ? '📥 Inbox' : 'All tasks'

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>{heading}</h1>
          <p>{activeFilter ? 'A saved filter. Change the filters below, then save the changes.' : 'Every task, by status and label. Drag cards between columns on the board.'}</p>
        </div>
        <div className="row">
          <div className="segmented" role="group" aria-label="View">
            <button aria-pressed={view === 'list'} onClick={() => setView('list')}>☰ List</button>
            <button aria-pressed={view === 'board'} onClick={() => setView('board')}>▦ Board</button>
          </div>
          <button className="btn primary" onClick={() => setEditing('new')}>+ New task</button>
        </div>
      </div>

      <div className="toolbar">
        <select value={String(scope)} aria-label="List"
          onChange={(e) => setScope(e.target.value === 'all' || e.target.value === 'inbox' ? e.target.value : Number(e.target.value))}>
          <option value="all">All lists</option>
          <option value="inbox">📥 Inbox</option>
          {activeLists.map((l) => <option key={l.id} value={l.id}>{l.emoji ?? '📋'} {l.name} ({l.open_count})</option>)}
        </select>
        <button className="btn small" onClick={newList}>+ New list</button>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search" aria-label="Search tasks" style={{ width: 160 }} />
        {view === 'list' && STATUSES.map((s) => (
          <button key={s} className="label-chip" aria-pressed={statuses.includes(s)} onClick={() => setStatuses(toggle(statuses, s))}>
            {STATUS_META[s].icon} {STATUS_META[s].label}
          </button>
        ))}
      </div>
      <div className="toolbar" aria-label="Filter by label">
        {labels.map((l) => (
          <button key={l.id} className="label-chip" aria-pressed={labelIds.includes(l.id)} onClick={() => setLabelIds(toggle(labelIds, l.id))}>
            <span className="dot" style={{ background: `var(--label-${l.color})` }} aria-hidden />
            {l.emoji && <span aria-hidden>{l.emoji}</span>}{l.name}
          </button>
        ))}
        <button className="btn small ghost" onClick={() => goTo('labels')}>🏷️ Manage labels</button>
        {filtersOn && (
          <button className="btn small ghost" onClick={() => { setStatuses([]); setLabelIds([]); setQ('') }}>Clear filters</button>
        )}
        <span className="spacer" />
        {activeFilter ? (
          <>
            {changed && <button className="btn small" onClick={updateFilter}>💾 Save changes</button>}
            <button className="btn small ghost" onClick={removeFilter}>Remove saved filter</button>
          </>
        ) : (
          <button className="btn small" onClick={saveFilter} title="Pin these filters in the sidebar">⭐ Save filter</button>
        )}
      </div>

      <QuickAdd labels={labels} listId={typeof scope === 'number' ? scope : null} onAdded={refresh} />
      {error && <div className="error" role="alert">{error}</div>}

      {tasks === null ? (
        <div className="card muted">Loading…</div>
      ) : view === 'list' ? (
        <div className="card">
          {tasks.length === 0
            ? <EmptyState>{filtersOn ? 'No tasks match these filters.' : 'No tasks here yet. Add one above.'}</EmptyState>
            : tasks.map((t) => <TaskRow key={t.id} task={t} today={today} lists={lists} onOpen={setEditing} onChanged={refresh} />)}
        </div>
      ) : (
        <Board tasks={tasks} today={today} onOpen={setEditing} onMoved={refresh} />
      )}

      {editing && (
        <TaskEditor
          task={editing === 'new' ? null : editing}
          defaults={editing === 'new' && typeof scope === 'number' ? { list_id: scope } : undefined}
          labels={labels} lists={lists}
          onClose={() => setEditing(null)} onSaved={() => { setEditing(null); refresh() }}
        />
      )}
    </div>
  )
}

function Board({ tasks, today, onOpen, onMoved }: {
  tasks: Task[]; today: string; onOpen: (t: Task) => void; onMoved: () => void
}) {
  const [dragging, setDragging] = useState<number | null>(null)
  const [over, setOver] = useState<{ status: TaskStatus; beforeId: number | null } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const columns = STATUSES.map((status) => ({
    status,
    tasks: tasks.filter((t) => t.status === status).sort((a, b) => a.position - b.position || a.id - b.id),
  }))

  async function drop(status: TaskStatus, beforeId: number | null) {
    const id = dragging
    setDragging(null); setOver(null)
    if (id === null || id === beforeId) return
    try {
      await api.moveTask(id, status, beforeId)
      onMoved()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <>
      {error && <div className="error" role="alert">{error}</div>}
      <div className="board">
        {columns.map(({ status, tasks: col }) => (
          <section
            key={status}
            className={`column ${over?.status === status && over.beforeId === null ? 'drag-over' : ''}`}
            aria-label={STATUS_META[status].label}
            onDragOver={(e) => { e.preventDefault(); if (over?.status !== status || over.beforeId !== null) setOver({ status, beforeId: null }) }}
            onDrop={(e) => { e.preventDefault(); drop(status, null) }}
          >
            <div className="column-head">
              <span>{STATUS_META[status].icon} {STATUS_META[status].label}</span>
              <span className="muted small">{col.length}</span>
            </div>
            {col.map((t) => (
              <article
                key={t.id}
                className={`card-task ${dragging === t.id ? 'dragging' : ''} ${over?.beforeId === t.id ? 'drop-before' : ''}`}
                draggable
                onDragStart={(e) => { setDragging(t.id); e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', String(t.id)) }}
                onDragEnd={() => { setDragging(null); setOver(null) }}
                onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); if (over?.beforeId !== t.id) setOver({ status, beforeId: t.id }) }}
                onDrop={(e) => { e.preventDefault(); e.stopPropagation(); drop(status, t.id) }}
              >
                <button className="title" onClick={() => onOpen(t)}>{t.title}</button>
                {t.status === 'blocked' && t.blocked_note && <span className="small muted">⛔ {t.blocked_note}</span>}
                <div className="row" style={{ gap: 5 }}>
                  <DueText task={t} today={today} />
                  {t.labels.map((l) => <LabelChip key={l.id} label={l} />)}
                  <PrivateBadge task={t} />
                </div>
              </article>
            ))}
            {col.length === 0 && <p className="small muted" style={{ textAlign: 'center' }}>Drop tasks here</p>}
          </section>
        ))}
      </div>
      <p className="small muted">Tip: no mouse? Open a task and change its Status.</p>
    </>
  )
}
