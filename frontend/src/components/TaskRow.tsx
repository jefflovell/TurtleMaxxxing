import { api } from '../lib/api'
import type { Task, TaskList } from '../lib/types'
import { DueText, LabelChip, PeopleChips, PrivateBadge, StatusText } from './TaskBits'

interface Props {
  task: Task
  today: string
  lists?: TaskList[]
  onOpen: (task: Task) => void
  onChanged: () => void
}

export default function TaskRow({ task, today, lists, onOpen, onChanged }: Props) {
  const done = task.status === 'done'
  const list = lists?.find((l) => l.id === task.list_id)

  async function toggleDone() {
    await api.updateTask(task.id, { status: done ? 'todo' : 'done' })
    onChanged()
  }

  return (
    <div className={`task-row ${done ? 'done' : ''}`}>
      <input
        type="checkbox" className="task-check" checked={done} onChange={toggleDone}
        aria-label={done ? `Mark "${task.title}" not done` : `Mark "${task.title}" done`}
      />
      <div>
        <button className="title" onClick={() => onOpen(task)}>{task.title}</button>
        <div className="meta">
          {task.status !== 'todo' && task.status !== 'done' && <StatusText status={task.status} />}
          {task.status === 'blocked' && task.blocked_note && <span className="small muted">{task.blocked_note}</span>}
          <DueText task={task} today={today} />
          {task.labels.map((l) => <LabelChip key={l.id} label={l} />)}
          <PeopleChips people={task.contacts} />
          <PrivateBadge task={task} />
          {list && <span className="small muted">{list.emoji ?? '📋'} {list.name}</span>}
          {task.reminders.some((r) => !r.dismissed) && <span className="small muted" title="Has a reminder">🔔</span>}
        </div>
      </div>
    </div>
  )
}
