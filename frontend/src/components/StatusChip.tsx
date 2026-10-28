import type { EventStatus } from '../lib/types'

// Status is shown with an icon + word, never color alone.
const LABELS: Record<EventStatus, string> = {
  confirmed: '✓ Confirmed',
  expected: '◌ Expected',
  projected: '… Upcoming',
  adjustment: '± Adjustment',
  opening: '● Starting balance',
}

export default function StatusChip({ status }: { status: EventStatus }) {
  return <span className={`chip ${status}`}>{LABELS[status]}</span>
}
