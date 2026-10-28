import { useEffect, useState } from 'react'
import type { PageProps } from '../App'
import EmptyState from '../components/EmptyState'
import { api } from '../lib/api'
import { FREQUENCY_LABELS, centsToInput, money, toCents } from '../lib/format'
import type { Review } from '../lib/types'

export default function ReviewsPage({ refresh, version }: PageProps) {
  const [reviews, setReviews] = useState<Review[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    api.reviews().then(setReviews).catch((err: Error) => setError(err.message))
  }, [version])

  async function run(action: () => Promise<unknown>, message: string) {
    try {
      await action()
      setNotice(message); setError(null)
      refresh()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Review inbox</h1>
          <p>Quick check-ins that keep the numbers honest. A couple of minutes a week is plenty.</p>
        </div>
      </div>
      {notice && <div className="card small" role="status">✓ {notice}</div>}
      {error && <div className="error" role="alert">{error}</div>}
      {reviews === null ? (
        <div className="card muted">Loading…</div>
      ) : reviews.length === 0 ? (
        <div className="card"><EmptyState>All caught up! 🐢 Nothing to review.</EmptyState></div>
      ) : (
        reviews.map((r) =>
          r.kind === 'balance_checkin'
            ? <CheckinCard key={r.id} review={r} run={run} />
            : <SubscriptionCard key={r.id} review={r} run={run} />,
        )
      )}
    </div>
  )
}

type Run = (action: () => Promise<unknown>, message: string) => Promise<void>

function CheckinCard({ review, run }: { review: Review; run: Run }) {
  const expected = review.expected_balance_cents ?? 0
  const [actual, setActual] = useState(centsToInput(expected))
  const cents = toCents(actual)
  const diff = cents === null ? 0 : cents - expected
  return (
    <div className="card stack" style={{ gap: 10 }}>
      <div>
        <h2>🏦 Balance check-in: {review.account_name}</h2>
        <p className="muted" style={{ margin: '4px 0 0' }}>
          We think it's about <strong className="num">{money(expected)}</strong>. What does the account actually say?
        </p>
      </div>
      <div className="row">
        <input aria-label="Actual balance" value={actual} onChange={(e) => setActual(e.target.value)} inputMode="decimal" style={{ width: 140 }} />
        <button
          className="btn primary" disabled={cents === null}
          onClick={() => run(() => api.checkin(review.id, cents!), diff ? `Adjusted ${review.account_name} by ${money(diff)}.` : `${review.account_name} matches. Nice.`)}
        >
          {diff ? `Save (adjust ${diff > 0 ? '+' : ''}${money(diff)})` : 'Looks right'}
        </button>
        <button className="btn ghost" onClick={() => run(() => api.dismiss(review.id), 'Skipped until next time.')}>Skip</button>
      </div>
    </div>
  )
}

function SubscriptionCard({ review, run }: { review: Review; run: Run }) {
  const [changing, setChanging] = useState(false)
  const [price, setPrice] = useState(centsToInput(review.amount_cents ?? 0))
  const cents = toCents(price)
  return (
    <div className="card stack" style={{ gap: 10 }}>
      <div>
        <h2>🔁 Still paying for {review.rule_name}?</h2>
        <p className="muted" style={{ margin: '4px 0 0' }}>
          <span className="num">{money(review.amount_cents ?? 0)}</span> · {FREQUENCY_LABELS[review.frequency ?? 'monthly']}
        </p>
      </div>
      {changing ? (
        <div className="row">
          <input aria-label="New price" value={price} onChange={(e) => setPrice(e.target.value)} inputMode="decimal" style={{ width: 120 }} />
          <button className="btn primary" disabled={cents === null}
            onClick={() => run(() => api.subscription(review.id, 'change_price', cents!), `${review.rule_name} is now ${money(cents!)}.`)}>
            Save new price
          </button>
          <button className="btn" onClick={() => setChanging(false)}>Cancel</button>
        </div>
      ) : (
        <div className="row">
          <button className="btn primary" onClick={() => run(() => api.subscription(review.id, 'keep'), `Keeping ${review.rule_name}.`)}>Yes, keep it</button>
          <button className="btn" onClick={() => setChanging(true)}>Price changed</button>
          <button className="btn" onClick={() => run(() => api.subscription(review.id, 'cancel'), `${review.rule_name} stopped from today.`)}>I cancelled it</button>
          <button className="btn ghost" onClick={() => run(() => api.dismiss(review.id), 'Skipped until next time.')}>Skip</button>
        </div>
      )}
    </div>
  )
}
