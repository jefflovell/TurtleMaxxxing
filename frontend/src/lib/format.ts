// Money and date helpers. Money is integer cents everywhere except on screen.

const currency = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' })

export const money = (cents: number) => currency.format(cents / 100)

/** "1,234.50" or "$1234.5" -> 123450. Returns null if it isn't a number. */
export function toCents(text: string): number | null {
  const cleaned = text.replace(/[$,\s]/g, '')
  if (cleaned === '' || cleaned === '-') return null
  const value = Number(cleaned)
  return Number.isFinite(value) ? Math.round(value * 100) : null
}

export const centsToInput = (cents: number) => (cents / 100).toFixed(2)

export function todayIso(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

export const thisMonth = () => todayIso().slice(0, 7)

export function shiftMonth(month: string, by: number): string {
  const [y, m] = month.split('-').map(Number)
  const index = y * 12 + (m - 1) + by
  return `${Math.floor(index / 12)}-${String((index % 12) + 1).padStart(2, '0')}`
}

export function monthLabel(month: string): string {
  const [y, m] = month.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
}

export function dayLabel(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

export const FREQUENCY_LABELS: Record<string, string> = {
  once: 'Once',
  weekly: 'Every week',
  biweekly: 'Every 2 weeks',
  semimonthly: 'Twice a month',
  monthly: 'Every month',
  quarterly: 'Every 3 months',
  yearly: 'Every year',
}

export const ACCOUNT_KIND_LABELS: Record<string, string> = {
  checking: 'Checking',
  savings: 'Savings',
  credit: 'Credit card',
  hsa: 'HSA',
  retirement: 'Retirement',
  brokerage: 'Brokerage',
  education: 'Education (529)',
  goal: 'Savings goal',
  other: 'Other',
}
