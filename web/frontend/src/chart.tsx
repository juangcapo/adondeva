import { useEffect, useState, type ReactNode } from 'react'

const TOKENS = ['series-1', 'series-2', 'series-3', 'grid', 'axis', 'muted', 'surface'] as const
type Colors = Record<(typeof TOKENS)[number], string>

function readColors(): Colors {
  const style = getComputedStyle(document.documentElement)
  return Object.fromEntries(TOKENS.map((t) => [t, style.getPropertyValue(`--${t}`).trim()])) as Colors
}

/** Chart colors from the CSS tokens; SVG attributes can't take var(), so read them and follow dark mode. */
export function useColors() {
  const [colors, setColors] = useState(readColors)
  useEffect(() => {
    const mq = matchMedia('(prefers-color-scheme: dark)')
    const update = () => setColors(readColors())
    mq.addEventListener('change', update)
    return () => mq.removeEventListener('change', update)
  }, [])
  return colors
}

export const axisProps = (c: Colors) => ({
  stroke: c.axis,
  tick: { fill: c.muted, fontSize: 12 },
  tickLine: false,
})

export function Tip({ title, rows }: { title: ReactNode; rows: { color?: string; label: string; value: string }[] }) {
  return (
    <div className="tip">
      <div className="tip-title">{title}</div>
      {rows.map((r) => (
        <div className="row" key={r.label}>
          {r.color && <span className="key" style={{ background: r.color }} />}
          <strong>{r.value}</strong>
          <span>{r.label}</span>
        </div>
      ))}
    </div>
  )
}
