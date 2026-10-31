import { useCallback, useEffect, useState } from 'react'
import { api } from './lib/api'
import type { Account, Label, Rule, SavedFilter, TaskList } from './lib/types'
import ReminderToasts from './components/ReminderToasts'
import TodayPage from './pages/TodayPage'
import TasksPage from './pages/TasksPage'
import LabelsPage from './pages/LabelsPage'
import CashFlowPage from './pages/CashFlowPage'
import CalendarPage from './pages/CalendarPage'
import ImportPage from './pages/ImportPage'
import AccountsPage from './pages/AccountsPage'
import RulesPage from './pages/RulesPage'
import ReviewsPage from './pages/ReviewsPage'

export type Page =
  | 'today' | 'tasks' | 'calendar' | 'labels'
  | 'cashflow' | 'reviews' | 'import' | 'rules' | 'accounts'

const NAV: { heading: string; items: { id: Page; label: string }[] }[] = [
  {
    heading: 'Plan',
    items: [
      { id: 'today', label: '☀️ Today' },
      { id: 'tasks', label: '✅ Tasks' },
      { id: 'calendar', label: '📅 Calendar' },
      { id: 'labels', label: '🏷️ Labels' },
    ],
  },
  {
    heading: 'Money',
    items: [
      { id: 'cashflow', label: '📈 Cash flow' },
      { id: 'reviews', label: '📥 Review inbox' },
      { id: 'import', label: '📄 Import CSV' },
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
  savedFilters: SavedFilter[]
  /** The saved filter the Tasks page was opened from, if any. */
  activeFilter: SavedFilter | null
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
  const [savedFilters, setSavedFilters] = useState<SavedFilter[]>([])
  const [activeFilterId, setActiveFilterId] = useState<number | null>(null)
  // Bumped each time a saved filter is clicked, so the Tasks page starts fresh from it.
  const [filterOpened, setFilterOpened] = useState(0)
  const [reviewCount, setReviewCount] = useState(0)
  const [version, setVersion] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(() => setVersion((v) => v + 1), [])

  useEffect(() => {
    Promise.all([api.accounts(), api.rules(), api.reviews(), api.labels(), api.lists(), api.filters()])
      .then(([a, r, rev, lab, li, sf]) => {
        setAccounts(a)
        setRules(r)
        setReviewCount(rev.length)
        setLabels(lab)
        setLists(li.lists)
        setSavedFilters(sf)
        setError(null)
      })
      .catch((err: Error) => setError(err.message))
  }, [version])

  const activeFilter = savedFilters.find((f) => f.id === activeFilterId) ?? null
  const goTo = (next: Page) => { setActiveFilterId(null); setPage(next) }
  const openFilter = (f: SavedFilter) => { setActiveFilterId(f.id); setFilterOpened((n) => n + 1); setPage('tasks') }
  const props: PageProps = {
    accounts, rules, labels, lists, savedFilters, activeFilter, refresh, version, goTo,
  }

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
            {group.items.map((item) => {
              const current = page === item.id && !(item.id === 'tasks' && activeFilter)
              return (
              <button
                key={item.id}
                className={`nav-item ${current ? 'active' : ''}`}
                onClick={() => goTo(item.id)}
                aria-current={current ? 'page' : undefined}
              >
                <span>{item.label}</span>
                {item.id === 'reviews' && reviewCount > 0 && (
                  <span className="badge" aria-label={`${reviewCount} to review`}>{reviewCount}</span>
                )}
              </button>
              )
            })}
            {group.heading === 'Plan' && savedFilters.length > 0 && (
              <>
                <div className="nav-heading">Saved filters</div>
                {savedFilters.map((f) => {
                  const current = page === 'tasks' && activeFilter?.id === f.id
                  return (
                    <button key={f.id} className={`nav-item sub ${current ? 'active' : ''}`}
                      onClick={() => openFilter(f)} aria-current={current ? 'page' : undefined}>
                      <span>{f.emoji ?? '⭐'} {f.name}</span>
                    </button>
                  )
                })}
              </>
            )}
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
        {page === 'tasks' && <TasksPage key={activeFilter ? `f${activeFilter.id}-${filterOpened}` : 'all'} {...props} />}
        {page === 'labels' && <LabelsPage {...props} />}
        {page === 'cashflow' && <CashFlowPage {...props} />}
        {page === 'calendar' && <CalendarPage {...props} />}
        {page === 'import' && <ImportPage {...props} />}
        {page === 'reviews' && <ReviewsPage {...props} />}
        {page === 'rules' && <RulesPage {...props} />}
        {page === 'accounts' && <AccountsPage {...props} />}
      </main>
      <ReminderToasts version={version} onChanged={refresh} />
    </div>
  )
}
