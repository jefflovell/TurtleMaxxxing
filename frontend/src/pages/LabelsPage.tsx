import { useState } from 'react'
import type { PageProps } from '../App'
import { LabelChip } from '../components/TaskBits'
import { api } from '../lib/api'
import type { Label, LabelColor } from '../lib/types'

const COLORS: LabelColor[] = ['red', 'orange', 'yellow', 'green', 'aqua', 'blue', 'violet', 'magenta', 'slate']

function ColorPicker({ value, onChange }: { value: LabelColor; onChange: (c: LabelColor) => void }) {
  return (
    <div className="row" style={{ gap: 4 }} role="radiogroup" aria-label="Color">
      {COLORS.map((c) => (
        <button
          type="button" key={c} role="radio" aria-checked={value === c} aria-label={c} title={c}
          onClick={() => onChange(c)}
          style={{
            width: 22, height: 22, borderRadius: '50%', cursor: 'pointer', background: `var(--label-${c})`,
            border: value === c ? '3px solid var(--text)' : '2px solid var(--surface)', boxShadow: '0 0 0 1px var(--border)',
          }}
        />
      ))}
    </div>
  )
}

export default function LabelsPage({ labels, refresh }: PageProps) {
  const [name, setName] = useState('')
  const [emoji, setEmoji] = useState('')
  const [color, setColor] = useState<LabelColor>('blue')
  const [error, setError] = useState<string | null>(null)

  async function run(action: () => Promise<unknown>) {
    try { await action(); setError(null); refresh() } catch (err) { setError((err as Error).message) }
  }

  async function add(e: React.FormEvent) {
    e.preventDefault()
    await run(() => api.createLabel({ name: name.trim(), color, emoji: emoji.trim() || null }))
    setName(''); setEmoji('')
  }

  async function rename(l: Label) {
    const next = prompt(`Rename "${l.name}" to:`, l.name)
    if (next?.trim() && next.trim() !== l.name) await run(() => api.updateLabel(l.id, { name: next.trim() }))
  }

  async function remove(l: Label) {
    if (confirm(`Delete the label "${l.name}"? It's removed from every task, but the tasks stay.`)) {
      await run(() => api.deleteLabel(l.id))
    }
  }

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>🏷️ Labels</h1>
          <p>Make your own. ⭐ Star the ones you use most so they're one click away everywhere.</p>
        </div>
      </div>

      <form className="card stack" onSubmit={add}>
        <h2>New label</h2>
        <div className="row">
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. wife, taxes, garden" required maxLength={40} aria-label="Label name" />
          <input value={emoji} onChange={(e) => setEmoji(e.target.value)} placeholder="Emoji (optional)" maxLength={8} style={{ width: 130 }} aria-label="Emoji" />
          <ColorPicker value={color} onChange={setColor} />
          <button className="btn primary" type="submit">Add label</button>
        </div>
      </form>
      {error && <div className="error" role="alert">{error}</div>}

      <div className="card">
        <table>
          <thead>
            <tr><th>Label</th><th>Favorite</th><th>Auto-Private</th><th>Color</th><th /></tr>
          </thead>
          <tbody>
            {labels.map((l) => (
              <tr key={l.id}>
                <td><LabelChip label={l} /></td>
                <td>
                  <button className="btn small ghost" aria-pressed={l.favorite} aria-label={`${l.favorite ? 'Unstar' : 'Star'} ${l.name}`}
                    onClick={() => run(() => api.updateLabel(l.id, { favorite: !l.favorite }))}>
                    {l.favorite ? '⭐' : '☆'}
                  </button>
                </td>
                <td>
                  <label className="toggle small" title="Tasks with this label are never shared with AI">
                    <input type="checkbox" checked={l.auto_private}
                      onChange={() => run(() => api.updateLabel(l.id, { auto_private: !l.auto_private }))} />
                    {l.auto_private ? '🔒 On' : 'Off'}
                  </label>
                </td>
                <td><ColorPicker value={l.color} onChange={(c) => run(() => api.updateLabel(l.id, { color: c }))} /></td>
                <td className="amount">
                  <button className="btn small ghost" onClick={() => rename(l)}>Rename</button>
                  <button className="btn small ghost" onClick={() => remove(l)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="small muted" style={{ marginBottom: 0 }}>
          🔒 <strong>Auto-Private</strong>: any task with this label is treated as Private and never shared with AI, even if you forget to tick Private.
        </p>
      </div>
    </div>
  )
}
