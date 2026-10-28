import { monthLabel, shiftMonth, thisMonth } from '../lib/format'

export default function MonthPicker({ month, onChange }: { month: string; onChange: (m: string) => void }) {
  return (
    <div className="month-picker">
      <button className="btn small ghost" onClick={() => onChange(shiftMonth(month, -1))} aria-label="Previous month">◀</button>
      <span className="label" aria-live="polite">{monthLabel(month)}</span>
      <button className="btn small ghost" onClick={() => onChange(shiftMonth(month, 1))} aria-label="Next month">▶</button>
      {month !== thisMonth() && (
        <button className="btn small" onClick={() => onChange(thisMonth())}>Today</button>
      )}
    </div>
  )
}
