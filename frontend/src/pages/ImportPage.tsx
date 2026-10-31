import { useEffect, useState } from 'react'
import type { PageProps } from '../App'
import EmptyState from '../components/EmptyState'
import { api } from '../lib/api'
import { dayLabel, money } from '../lib/format'
import type { ImportAction, ImportMapping, ImportPlan, ImportRow } from '../lib/types'

// What each row will do. Icons and words, so meaning never rests on color.
const ACTIONS: Record<ImportAction, { icon: string; label: string; imports: boolean }> = {
  match: { icon: '✓', label: 'Confirms', imports: true },
  match_changed: { icon: '≈', label: 'Confirms at the real amount', imports: true },
  new: { icon: '+', label: 'Adds', imports: true },
  duplicate: { icon: '↺', label: 'Already imported', imports: false },
  before_start: { icon: '⏮', label: 'Before the starting balance', imports: false },
  error: { icon: '⚠', label: "Can't read", imports: false },
}

const DATE_FORMATS: [string, string][] = [
  ['auto', 'Detect'],
  ['%Y-%m-%d', '2026-11-30'],
  ['%m/%d/%Y', '11/30/2026 (month first)'],
  ['%m/%d/%y', '11/30/26'],
  ['%d/%m/%Y', '30/11/2026 (day first)'],
  ['%Y/%m/%d', '2026/11/30'],
  ['%d-%b-%Y', '30-Nov-2026'],
  ['%b %d, %Y', 'Nov 30, 2026'],
]

export default function ImportPage({ accounts, refresh, goTo }: PageProps) {
  const open = accounts.filter((a) => !a.archived)
  const [accountId, setAccountId] = useState<number | null>(null)
  const [fileName, setFileName] = useState('')
  const [text, setText] = useState<string | null>(null)
  const [mapping, setMapping] = useState<Partial<ImportMapping>>({})
  const [plan, setPlan] = useState<ImportPlan | null>(null)
  const [skipped, setSkipped] = useState<Set<number>>(new Set())
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const account = accountId ?? open[0]?.id ?? null

  const mappingKey = JSON.stringify(mapping)
  useEffect(() => {
    if (text === null || account === null) return
    let cancelled = false
    api.importPreview(account, text, JSON.parse(mappingKey))
      .then((p) => { if (!cancelled) { setPlan(p); setSkipped(new Set()); setError(null) } })
      .catch((err: Error) => { if (!cancelled) { setPlan(null); setError(err.message) } })
    return () => { cancelled = true }
  }, [text, account, mappingKey])

  async function pickFile(file: File | undefined) {
    if (!file) return
    setResult(null)
    setMapping({})
    setFileName(file.name)
    setText(await file.text())
  }

  async function doImport() {
    if (!plan || text === null || account === null) return
    setBusy(true)
    try {
      const done = await api.importApply(account, text, mapping, [...skipped])
      setResult(`Done: confirmed ${done.confirmed}, added ${done.added}, skipped ${done.skipped}.`)
      setText(null)
      setPlan(null)
      setFileName('')
      refresh()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const toggleRow = (row: number) => {
    const next = new Set(skipped)
    if (next.has(row)) next.delete(row)
    else next.add(row)
    setSkipped(next)
  }

  const importing = plan ? plan.rows.filter((r) => ACTIONS[r.action].imports && !skipped.has(r.row)).length : 0
  // "" tells the backend "no such column" (null would mean "guess").
  // One Amount column and separate Money out/in columns are either/or.
  const setCol = (key: keyof ImportMapping, value: string) => {
    const next: Partial<ImportMapping> = { ...(plan?.mapping ?? {}), ...mapping, [key]: value }
    if (value && key === 'amount_col') { next.debit_col = ''; next.credit_col = '' }
    if (value && (key === 'debit_col' || key === 'credit_col')) next.amount_col = ''
    setMapping(next)
  }

  if (open.length === 0) {
    return (
      <div className="stack">
        <div className="page-header"><div><h1>Import CSV</h1></div></div>
        <div className="card">
          <EmptyState>Add an account first, then import its transactions.</EmptyState>
          <button className="btn primary" onClick={() => goTo('accounts')}>Go to Accounts</button>
        </div>
      </div>
    )
  }

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Import CSV</h1>
          <p>Download a CSV of transactions from your bank's or card's website, then drop it here. Matching rows confirm what the budget expected; everything else is added. Nothing changes until you press Import.</p>
        </div>
      </div>

      <div className="card stack">
        <div className="row">
          <label className="field">
            <span>Account</span>
            <select value={account ?? ''} onChange={(e) => setAccountId(Number(e.target.value))}>
              {open.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </label>
          <label className="field">
            <span>CSV file</span>
            <input type="file" accept=".csv,text/csv" onChange={(e) => { pickFile(e.target.files?.[0]); e.target.value = '' }} />
          </label>
        </div>
        <p className="small muted">
          🔒 The file is read on this computer and never saved. Only the transactions you import are kept.
          TurtleMaxxxing never logs in to your bank.
        </p>
        {fileName && <p className="small">📄 {fileName}</p>}
      </div>

      {error && <div className="error" role="alert">{error}</div>}
      {result && <div className="card" role="status">✅ {result} <button className="btn small ghost" onClick={() => goTo('cashflow')}>See cash flow</button></div>}

      {text !== null && (plan || error) && (
        <details className="card" open={!plan}>
          <summary>Columns and format{plan && <span className="muted small"> · detected automatically, change if something looks wrong</span>}</summary>
          <div className="row" style={{ marginTop: 10 }}>
            {([
              ['date_col', 'Date'], ['description_col', 'Description'], ['amount_col', 'Amount'],
              ['debit_col', 'Money out (if separate)'], ['credit_col', 'Money in (if separate)'],
            ] as [keyof ImportMapping, string][]).map(([key, label]) => (
              <label key={key} className="field">
                <span>{label}</span>
                <select value={String((mapping[key] ?? plan?.mapping[key]) ?? '')} onChange={(e) => setCol(key, e.target.value)}>
                  <option value="">—</option>
                  {(plan?.headers ?? []).map((h) => <option key={h} value={h}>{h}</option>)}
                </select>
              </label>
            ))}
            <label className="field">
              <span>Date format</span>
              <select value={mapping.date_format ?? plan?.mapping.date_format ?? 'auto'}
                onChange={(e) => setMapping({ ...mapping, date_format: e.target.value })}>
                {DATE_FORMATS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </label>
            <label className="row small" style={{ gap: 6 }}>
              <input type="checkbox" checked={mapping.flip_sign ?? false}
                onChange={(e) => setMapping({ ...mapping, flip_sign: e.target.checked })} />
              Purchases show as positive numbers (common on card statements)
            </label>
          </div>
        </details>
      )}

      {plan && (
        <>
          <div className="toolbar" aria-label="Summary">
            {(Object.keys(ACTIONS) as ImportAction[]).filter((a) => plan.counts[a]).map((a) => (
              <span key={a} className="label-chip"><span aria-hidden>{ACTIONS[a].icon}</span> {ACTIONS[a].label}: {plan.counts[a]}</span>
            ))}
            <span className="spacer" />
            <button className="btn primary" disabled={busy || importing === 0} onClick={doImport}>
              Import {importing} {importing === 1 ? 'row' : 'rows'}
            </button>
          </div>
          <div className="card table-wrap">
            <table>
              <thead>
                <tr><th aria-label="Import this row" /><th>Date</th><th>Description</th><th className="num">Amount</th><th>What happens</th></tr>
              </thead>
              <tbody>
                {plan.rows.map((r) => <PlanRow key={r.row} row={r} skipped={skipped.has(r.row)} onToggle={() => toggleRow(r.row)} />)}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

function PlanRow({ row, skipped, onToggle }: { row: ImportRow; skipped: boolean; onToggle: () => void }) {
  const meta = ACTIONS[row.action]
  const m = row.match
  let what = meta.label
  if (m && row.action === 'match') what = `Confirms ${m.description.split(':')[0]} (expected ${dayLabel(m.date)})`
  if (m && row.action === 'match_changed') what = `Confirms ${m.description.split(':')[0]} at the real amount (expected ${money(Math.abs(m.amount_cents))})`
  if (row.action === 'new') what = 'Adds as a new entry'
  return (
    <tr className={!meta.imports || skipped ? 'muted' : ''}>
      <td>
        {meta.imports && <input type="checkbox" checked={!skipped} onChange={onToggle} aria-label={`Import ${row.description}`} />}
      </td>
      <td>{row.date ? dayLabel(row.date) : '—'}</td>
      <td>{row.description}</td>
      <td className="num">{row.amount_cents === null ? '—' : money(row.amount_cents)}</td>
      <td><span aria-hidden>{meta.icon}</span> {what}{row.message && <span className="small muted"> · {row.message}</span>}</td>
    </tr>
  )
}
