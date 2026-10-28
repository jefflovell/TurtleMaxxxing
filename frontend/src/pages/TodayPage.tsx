import { useEffect, useState } from 'react'
import type { PageProps } from '../App'
import EmptyState from '../components/EmptyState'
import QuickAdd from '../components/QuickAdd'
import TaskEditor from '../components/TaskEditor'
import TaskRow from '../components/TaskRow'
import { api } from '../lib/api'
import { greeting } from '../lib/tasks'
import type { Task, TodayView } from '../lib/types'

export default function TodayPage({ labels, lists, refresh, version, goTo }: PageProps) {
  const [view, setView] = useState<TodayView | null>(null)
  const [editing, setEditing] = useState<Task | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [hello] = useState(() => greeting(new Date().getHours()))

  useEffect(() => {
    api.today().then((v) => { setView(v); setError(null) }).catch((err: Error) => setError(err.message))
  }, [version])

  const section = (title: string, tasks: Task[], empty?: string) => (
    <div className="card">
      <div className="section-title"><h2>{title}</h2><span className="count">{tasks.length}</span></div>
      {tasks.length === 0
        ? <p className="muted small" style={{ margin: 0 }}>{empty}</p>
        : tasks.map((t) => <TaskRow key={t.id} task={t} today={view!.today} lists={lists} onOpen={setEditing} onChanged={refresh} />)}
    </div>
  )

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>{hello} 🐢</h1>
          <p>
            {view ? <>What's on your plate. {view.done_today_count > 0 && <strong>{view.done_today_count} done today, nice!</strong>}</> : 'Loading…'}
          </p>
        </div>
      </div>

      <QuickAdd labels={labels} onAdded={refresh} />
      {error && <div className="error" role="alert">{error}</div>}

      {view && (
        <>
          {view.overdue.length > 0 && section('⚠ Overdue', view.overdue)}
          {section('Today', view.due_today, 'Nothing due today.')}
          {section('Next 7 days', view.upcoming, 'Nothing coming up this week.')}
          {view.overdue.length + view.due_today.length + view.upcoming.length === 0 && view.no_date_count === 0 && (
            <div className="card"><EmptyState>All clear! Add a task above.</EmptyState></div>
          )}
          {view.no_date_count > 0 && (
            <p className="small muted">
              + {view.no_date_count} task{view.no_date_count === 1 ? '' : 's'} without a date.{' '}
              <button className="btn small ghost" onClick={() => goTo('tasks')}>See all tasks</button>
            </p>
          )}
        </>
      )}

      {editing && (
        <TaskEditor task={editing} labels={labels} lists={lists}
          onClose={() => setEditing(null)} onSaved={() => { setEditing(null); refresh() }} />
      )}
    </div>
  )
}
