import { useCallback, useEffect, useState } from 'react'
import { api } from './lib/api'
import type { Account, Rule } from './lib/types'
import CashFlowPage from './pages/CashFlowPage'
import BillsCalendarPage from './pages/BillsCalendarPage'
import AccountsPage from './pages/AccountsPage'
import RulesPage from './pages/RulesPage'
import ReviewsPage from './pages/ReviewsPage'

type Page = 'cashflow' | 'calendar' | 'reviews' | 'rules' | 'accounts'

const NAV: { id: Page; label: string }[] = [
  { id: 'cashflow', label: '📈 Cash flow' },
  { id: 'calendar', label: '📅 Bills calendar' },
  { id: 'reviews', label: '📥 Review inbox' },
  { id: 'rules', label: '🔁 Money rules' },
  { id: 'accounts', label: '🏦 Accounts' },
]

export interface PageProps {
  accounts: Account[]
  rules: Rule[]
  /** Call after any change so every page reloads its data. */
  refresh: () => void
  version: number
  goTo: (page: Page) => void
}

export default function App() {
  const [page, setPage] = useState<Page>('cashflow')
  const [accounts, setAccounts] = useState<Account[]>([])
  const [rules, setRules] = useState<Rule[]>([])
  const [reviewCount, setReviewCount] = useState(0)
  const [version, setVersion] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(() => setVersion((v) => v + 1), [])

  useEffect(() => {
    Promise.all([api.accounts(), api.rules(), api.reviews()])
      .then(([a, r, rev]) => {
        setAccounts(a)
        setRules(r)
        setReviewCount(rev.length)
        setError(null)
      })
      .catch((err: Error) => setError(err.message))
  }, [version])

  const props: PageProps = { accounts, rules, refresh, version, goTo: setPage }

  return (
    <div className="app">
      <nav className="sidebar" aria-label="Main">
        <div className="brand">
          <img src="/turtle.png" alt="" />
          <span>TurtleMaxxxing</span>
        </div>
        {NAV.map((item) => (
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
        <div className="sidebar-footer">🔒 Local only. Your data stays on this computer.</div>
      </nav>
      <main className="main">
        {error && (
          <div className="card error" role="alert" style={{ marginBottom: 16 }}>
            Can't reach the TurtleMaxxxing backend: {error}. Is it running?
          </div>
        )}
        {page === 'cashflow' && <CashFlowPage {...props} />}
        {page === 'calendar' && <BillsCalendarPage {...props} />}
        {page === 'reviews' && <ReviewsPage {...props} />}
        {page === 'rules' && <RulesPage {...props} />}
        {page === 'accounts' && <AccountsPage {...props} />}
      </main>
    </div>
  )
}
