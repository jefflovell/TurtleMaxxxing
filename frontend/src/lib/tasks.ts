import type { TaskStatus } from './types'

// Status is always shown with an icon + word, never color alone.
export const STATUS_META: Record<TaskStatus, { label: string; icon: string }> = {
  todo: { label: 'To do', icon: '○' },
  in_progress: { label: 'In progress', icon: '◐' },
  blocked: { label: 'Blocked', icon: '⛔' },
  done: { label: 'Done', icon: '✓' },
}

export const STATUSES: TaskStatus[] = ['todo', 'in_progress', 'blocked', 'done']

export function greeting(hour: number): string {
  return hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
}
