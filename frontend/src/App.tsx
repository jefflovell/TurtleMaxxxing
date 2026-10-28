import { useCallback, useEffect, useState } from 'react'
import { api } from './lib/api'
import type { Account, Label, Rule, TaskList } from './lib/types'
import ReminderToasts from './components/ReminderToasts'
import TodayPage from './pages/TodayPage'
import TasksPage from './pages/TasksPage'
import LabelsPage from './pages/LabelsPage'
import CashFlowPage from './pages/CashFlowPage'
import BillsCalendarPage from './pages/BillsCalendarPage'
import AccountsPage from './pages/AccountsPage'
import RulesPage from './pages/RulesPage'
import ReviewsPage from './pages/ReviewsPage'

export type Page =
  | 'today' | 'tasks' | 'labels'
  | 'cashflow' | 'calendar' | 'reviews' | 'rules' | 'accounts'

const NAV: { heading: string; items: { id: Page; label: string }[] }[] = [
  {
    heading: 'Plan',
    items: [
      { id: 'today', label: '☀️ Today' },
      { id: 'tasks', label: '✅ Tasks' },
      { id: 'labels', label: '🏷️ Labels' },
    ],
  },
  {
    heading: 'Money',
    items: [
      { id: 'cashflow', label: '📈 Cash flow' },
      { id: 'calendar', label: '📅 Bills calendar' },
      { id: 'reviews', label: '📥 Review inbox' },
      { id: 'rules', label: '🔁 Money rules' },
      { id: 'accounts', label: '🏦 Accounts' },
    ],
  },
]

export interface PageProps {
  accounts: Account[]
  rules: Rule[]
  labels: Label[]
  lists: TaskList[]
  /** Call after any change so every page reloads its data. */
  refresh: () => void
  version: number
  goTo: (page: Page) => void
}

export default function App() {
  const [page, setPage] = useState<Page>('today')
  const [accounts, setAccounts] = useState<Account[]>([])
  const [rules, setRules] = useState<Rule[]>([])
  const [labels, setLabels] = useState<Label[]>([])
  const [lists, setLists] = useState<TaskList[]>([])
  const [reviewCount, setReviewCount] = useState(0)
  const [version, setVersion] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(() => setVersion((v) => v + 1), [])

  useEffect(() => {
    Promise.all([api.accounts(), api.rules(), api.reviews(), api.labels(), api.lists()])
      .then(([a, r, rev, lab, li]) => {
        setAccounts(a)
        setRules(r)
        setReviewCount(rev.length)
        setLabels(lab)
        setLists(li.lists)
        setError(null)
      })
      .catch((err: Error) => setError(err.message))
  }, [version])

  const props: PageProps = { accounts, rules, labels, lists, refresh, version, goTo: setPage }

  return (
    <div className="app">
      <nav className="sidebar" aria-label="Main">
        <div className="brand">
          <img src="/turtle.png" alt="" />
          <span>TurtleMaxxxing</span>
        </div>
        {NAV.map((group) => (
          <div key={group.heading} className="nav-group">
            <div className="nav-heading">{group.heading}</div>
            {group.items.map((item) => (
              <button
                key={item.id}
                className={`nav-item ${page === item.id ? 'active' : ''}`}
                onClick={() => setPage(item.id)}
                aria-current={page === item.id ? 'page' : undefined}
              >
                <span>{item.label}</span>
                {item.id === 'reviews' && reviewCount > 0 && (
                  <span className="badge" aria-label={`${reviewCount} to review`}>{reviewCount}</span>
                )}
              </button>
            ))}
          </div>
        ))}
        <div className="sidebar-footer">🔒 Local only. Your data stays on this computer.</div>
      </nav>
      <main className="main">
        {error && (
          <div className="card error" role="alert" style={{ marginBottom: 16 }}>
            Can't reach the TurtleMaxxxing backend: {error}. Is it running?
          </div>
        )}
        {page === 'today' && <TodayPage {...props} />}
        {page === 'tasks' && <TasksPage {...props} />}
        {page === 'labels' && <LabelsPage {...props} />}
        {page === 'cashflow' && <CashFlowPage {...props} />}
        {page === 'calendar' && <BillsCalendarPage {...props} />}
        {page === 'reviews' && <ReviewsPage {...props} />}
        {page === 'rules' && <RulesPage {...props} />}
        {page === 'accounts' && <AccountsPage {...props} />}
      </main>
      <ReminderToasts version={version} onChanged={refresh} />
    </div>
  )
}
