import type { ReactNode } from 'react'

export default function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="empty">
      <img src="/turtle.png" alt="" />
      <div>{children}</div>
    </div>
  )
}
