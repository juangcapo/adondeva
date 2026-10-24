import { useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { apiUrl, useApi, type InflationYear } from '../api.ts'
import { axisProps, Tip, useColors } from '../chart.tsx'
import { fmt, pct } from '../format.ts'

const DESDE = [1938, 1970, 1990, 2005]

export default function Inflacion() {
  const colors = useColors()
  const [desde, setDesde] = useState(1990)
  const { data, error } = useApi<InflationYear[]>(apiUrl('inflation'))
  const rows = useMemo(() => (data ?? []).filter((r) => r.anio >= desde), [data, desde])

  const series = [
    { key: 'promedio' as const, label: 'Promedio anual vs año anterior', color: colors['series-1'] },
    { key: 'dic_dic' as const, label: 'Diciembre vs diciembre', color: colors['series-2'] },
  ]
  const last = rows[rows.length - 1]
  const peak = rows.reduce<InflationYear | null>((m, r) => (r.promedio != null && (!m || r.promedio > (m.promedio ?? 0)) ? r : m), null)

  return (
    <>
      <h1>Inflación</h1>
      <p className="lede">
        Cuánto subieron los precios cada año según el Índice de Precios del Consumo del INE. Es lo que se usa para
        pasar el gasto a pesos de un mismo año.
      </p>
      {error && <p className="error">{error}</p>}
      {data && last && (
        <section className="card">
          <div className="card-head">
            <h2>Inflación anual, en %</h2>
            <label className="field">
              Desde
              <select value={desde} onChange={(e) => setDesde(Number(e.target.value))}>
                {DESDE.map((y) => <option key={y}>{y}</option>)}
              </select>
            </label>
          </div>
          <div className="stats">
            <div className="stat"><div className="label">{last.anio}, promedio</div><div className="value">{pct(last.promedio)}</div></div>
            <div className="stat"><div className="label">{last.anio}, dic. a dic.</div><div className="value">{pct(last.dic_dic)}</div></div>
            {peak && <div className="stat"><div className="label">Máximo desde {desde} ({peak.anio})</div><div className="value">{pct(peak.promedio)}</div></div>}
          </div>
          <div className="legend">
            {series.map((s) => <span key={s.key}><span className="key" style={{ background: s.color }} />{s.label}</span>)}
          </div>
          <div style={{ height: 320 }}>
            <ResponsiveContainer>
              <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
                <CartesianGrid stroke={colors.grid} vertical={false} />
                <XAxis dataKey="anio" {...axisProps(colors)} minTickGap={24} />
                <YAxis {...axisProps(colors)} axisLine={false} width={44} tickFormatter={(v) => `${fmt(v)}%`} />
                <ReferenceLine y={0} stroke={colors.axis} />
                <Tooltip
                  cursor={{ stroke: colors.axis }}
                  content={({ active, payload }) => {
                    const r = active && (payload?.[0]?.payload as InflationYear | undefined)
                    if (!r) return null
                    return <Tip title={r.anio} rows={series.map((s) => ({ color: s.color, label: s.label, value: pct(r[s.key]) }))} />
                  }}
                />
                {series.map((s) => (
                  <Line key={s.key} type="monotone" dataKey={s.key} stroke={s.color} strokeWidth={2} dot={false}
                    connectNulls activeDot={{ r: 5, stroke: colors.surface, strokeWidth: 2 }} isAnimationActive={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="muted">Fuente: INE, IPC base octubre 2022 = 100, Total País. Solo años completos.</p>
          <details>
            <summary>Ver tabla</summary>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Año</th><th className="num">Promedio</th><th className="num">Dic. a dic.</th></tr></thead>
                <tbody>
                  {[...rows].reverse().map((r) => (
                    <tr key={r.anio}><td>{r.anio}</td><td className="num">{pct(r.promedio)}</td><td className="num">{pct(r.dic_dic)}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </section>
      )}
    </>
  )
}
