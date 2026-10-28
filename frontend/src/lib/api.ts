// The one place the UI talks to the backend. Every call goes to /api on
// this same computer; the UI never contacts any other server.

import type {
  Account, Cashflow, DueReminder, Label, LedgerEvent, Review, Rule, Task, TaskList, TaskStatus, TodayView,
} from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string'
        ? body.detail
        : (body.detail ?? []).map((d: { msg: string }) => d.msg).join('; ')
    } catch {
      // keep statusText
    }
    throw new Error(detail || `Request failed (${res.status})`)
  }
  return (res.status === 204 ? undefined : await res.json()) as T
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
const patch = <T>(path: string, body: unknown) =>
  request<T>(path, { method: 'PATCH', body: JSON.stringify(body) })

export type AccountInput = Pick<Account, 'name' | 'kind' | 'opening_balance_cents' | 'checkin_every_days'> & {
  opening_date?: string
}
export type RuleInput = Omit<Rule, 'id' | 'last_reviewed_date'>

export interface TaskInput {
  title: string
  notes?: string
  status?: TaskStatus
  blocked_note?: string | null
  list_id?: number | null
  due_date?: string | null
  due_time?: string | null
  private?: boolean
  label_ids?: number[]
  reminders?: string[]
}

export interface TaskFilters {
  status?: TaskStatus[]
  labelIds?: number[]
  listId?: number | 'inbox' | null
  q?: string
}

export type LabelInput = Pick<Label, 'name' | 'color'> & Partial<Pick<Label, 'emoji' | 'favorite' | 'auto_private'>>
const del = (path: string) => request<void>(path, { method: 'DELETE' })

export const api = {
  accounts: () => request<Account[]>('/accounts'),
  createAccount: (body: AccountInput) => post<Account>('/accounts', body),
  updateAccount: (id: number, body: Partial<AccountInput> & { archived?: boolean }) =>
    patch<Account>(`/accounts/${id}`, body),
  checkBalanceNow: (id: number) => post<{ review_id: number }>(`/accounts/${id}/checkin`),

  rules: () => request<Rule[]>('/rules'),
  createRule: (body: RuleInput) => post<Rule>('/rules', body),
  updateRule: (id: number, body: Partial<RuleInput>) => patch<Rule>(`/rules/${id}`, body),
  confirmOccurrence: (ruleId: number, date: string) =>
    post(`/rules/${ruleId}/occurrences/${date}/confirm`),

  confirmEntry: (id: number) => patch<LedgerEvent>(`/entries/${id}`, { status: 'confirmed' }),

  cashflow: (month: string, accountIds: number[]) => {
    const params = new URLSearchParams({ month })
    accountIds.forEach((id) => params.append('account_id', String(id)))
    return request<Cashflow>(`/cashflow?${params}`)
  },
  calendar: (month: string) =>
    request<{ month: string; today: string; events: LedgerEvent[] }>(`/calendar?month=${month}`),

  reviews: () => request<Review[]>('/reviews'),
  checkin: (id: number, actualCents: number) =>
    post<{ adjustment_cents: number }>(`/reviews/${id}/checkin`, { actual_balance_cents: actualCents }),
  subscription: (id: number, action: 'keep' | 'cancel' | 'change_price', newAmountCents?: number) =>
    post(`/reviews/${id}/subscription`, { action, new_amount_cents: newAmountCents }),
  dismiss: (id: number) => post(`/reviews/${id}/dismiss`),

  tasks: (f: TaskFilters = {}) => {
    const params = new URLSearchParams()
    f.status?.forEach((s) => params.append('status', s))
    f.labelIds?.forEach((id) => params.append('label_id', String(id)))
    if (f.listId === 'inbox') params.set('inbox', 'true')
    else if (typeof f.listId === 'number') params.set('list_id', String(f.listId))
    if (f.q) params.set('q', f.q)
    return request<Task[]>(`/tasks?${params}`)
  },
  createTask: (body: TaskInput) => post<Task>('/tasks', body),
  updateTask: (id: number, body: Partial<TaskInput>) => patch<Task>(`/tasks/${id}`, body),
  moveTask: (id: number, status: TaskStatus, beforeId: number | null) =>
    post<Task>(`/tasks/${id}/move`, { status, before_id: beforeId }),
  deleteTask: (id: number) => del(`/tasks/${id}`),
  today: () => request<TodayView>('/today'),

  labels: () => request<Label[]>('/labels'),
  createLabel: (body: LabelInput) => post<Label>('/labels', body),
  updateLabel: (id: number, body: Partial<LabelInput>) => patch<Label>(`/labels/${id}`, body),
  deleteLabel: (id: number) => del(`/labels/${id}`),

  lists: () => request<{ inbox_open_count: number; lists: TaskList[] }>('/lists'),
  createList: (name: string, emoji?: string) => post<TaskList>('/lists', { name, emoji }),
  updateList: (id: number, body: Partial<{ name: string; emoji: string; archived: boolean }>) =>
    patch<TaskList>(`/lists/${id}`, body),

  dueReminders: () => request<DueReminder[]>('/reminders/due'),
  dismissReminder: (id: number) => post(`/reminders/${id}/dismiss`),
  snoozeReminder: (id: number, minutes: number) => post(`/reminders/${id}/snooze`, { minutes }),
}
