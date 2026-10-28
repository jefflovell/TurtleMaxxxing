// Shapes returned by the backend API (backend/turtlemaxxxing/budget/api.py).
// All money is integer cents.

export type AccountKind =
  | 'checking' | 'savings' | 'credit' | 'hsa' | 'retirement'
  | 'brokerage' | 'education' | 'goal' | 'other'

export interface Account {
  id: number
  name: string
  kind: AccountKind
  opening_balance_cents: number
  opening_date: string
  checkin_every_days: number | null
  last_checkin_date: string | null
  archived: boolean
  balance_cents: number
}

export type RuleKind = 'income' | 'bill' | 'subscription'
export type Frequency =
  | 'once' | 'weekly' | 'biweekly' | 'semimonthly' | 'monthly' | 'quarterly' | 'yearly'

export interface Split {
  account_id: number
  amount_cents: number
  label: string | null
}

export interface Rule {
  id: number
  kind: RuleKind
  name: string
  amount_cents: number
  account_id: number
  frequency: Frequency
  start_date: string
  end_date: string | null
  second_day: number | null
  review_every_months: number | null
  last_reviewed_date: string | null
  splits: Split[]
}

export type EventStatus = 'expected' | 'confirmed' | 'adjustment' | 'projected' | 'opening'

export interface LedgerEvent {
  entry_id: number | null
  rule_id: number | null
  rule_kind: RuleKind | null
  account_id: number
  date: string
  amount_cents: number
  description: string
  status: EventStatus
}

export interface CashflowDay {
  date: string
  balance_cents: number
  in_cents: number
  out_cents: number
  projected: boolean
}

export interface Cashflow {
  month: string
  account_ids: number[]
  start_balance_cents: number
  end_balance_cents: number
  low_point: { date: string; balance_cents: number }
  days: CashflowDay[]
  events: LedgerEvent[]
}

export interface Review {
  id: number
  kind: 'balance_checkin' | 'subscription_review'
  account_id: number | null
  rule_id: number | null
  due_date: string
  status: 'open' | 'done' | 'dismissed'
  account_name?: string
  expected_balance_cents?: number
  rule_name?: string
  amount_cents?: number
  frequency?: Frequency
}
