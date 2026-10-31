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

// ---------------------------------------------------------------- tasks
// Shapes from backend/turtlemaxxxing/tasks/api.py.

export type TaskStatus = 'todo' | 'in_progress' | 'blocked' | 'done'
export type LabelColor =
  | 'red' | 'orange' | 'yellow' | 'green' | 'aqua' | 'blue' | 'violet' | 'magenta' | 'slate'

export interface Label {
  id: number
  name: string
  color: LabelColor
  emoji: string | null
  favorite: boolean
  auto_private: boolean
  position: number
}

export interface TaskList {
  id: number
  name: string
  emoji: string | null
  archived: boolean
  open_count: number
}

export interface Reminder {
  id: number
  remind_at: string
  dismissed: boolean
}

export interface Task {
  id: number
  list_id: number | null
  title: string
  notes: string
  status: TaskStatus
  blocked_note: string | null
  due_date: string | null
  due_time: string | null
  private: boolean
  /** True if flagged Private or tagged with an auto-Private label. Never shared with AI. */
  is_private: boolean
  position: number
  completed_at: string | null
  labels: Label[]
  reminders: Reminder[]
  /** The people this task is about. Each has its own is_private. */
  contacts: ContactSummary[]
}

// ---------------------------------------------------------------- contacts
// Shapes from backend/turtlemaxxxing/contacts/api.py.

export interface ContactSummary {
  id: number
  name: string
  organization: string
  role: string
  location: string
  is_private: boolean
}

export interface Contact {
  id: number
  name: string
  organization: string
  role: string
  email: string
  phone: string
  location: string
  notes: string
  private: boolean
  /** True if flagged Private or tagged with an auto-Private label. Never shared with AI. */
  is_private: boolean
  labels: Label[]
  open_task_count: number
  /** Only on GET /contacts/{id}. */
  tasks?: Task[]
}

export interface TodayView {
  today: string
  overdue: Task[]
  due_today: Task[]
  upcoming: Task[]
  no_date_count: number
  done_today_count: number
}

export interface DueReminder {
  reminder_id: number
  remind_at: string
  task: Task
}

export interface FilterSpec {
  scope: 'all' | 'inbox' | number
  statuses: TaskStatus[]
  label_ids: number[]
  q: string
  view: 'list' | 'board'
}

export interface SavedFilter {
  id: number
  name: string
  emoji: string | null
  position: number
  filters: FilterSpec
}

// ---------------------------------------------------------------- CSV import
// Shapes from backend/turtlemaxxxing/budget/csv_import.py.

export interface ImportMapping {
  date_col: string | null
  description_col: string | null
  amount_col: string | null
  debit_col: string | null
  credit_col: string | null
  date_format: string
  flip_sign: boolean
}

export type ImportAction = 'match' | 'match_changed' | 'new' | 'duplicate' | 'before_start' | 'error'

export interface ImportRow {
  row: number
  date: string | null
  description: string
  amount_cents: number | null
  action: ImportAction
  message: string | null
  match: { description: string; date: string; amount_cents: number; confirmed: boolean } | null
}

export interface ImportPlan {
  headers: string[]
  mapping: ImportMapping
  counts: Partial<Record<ImportAction, number>>
  rows: ImportRow[]
}
