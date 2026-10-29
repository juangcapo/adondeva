import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { apiUrl, useApi, type Breakdown, type Spending } from '../api.ts'
import { axisProps, Tip, useColors } from '../chart.tsx'
import { axisBillions, fmt, pct, pesos, signedPct } from '../format.ts'

const FUENTES: Record<string, string> = { 'opp-historico': 'OPP histórico', opp: 'OPP', mef: 'MEF' }
const NIVELES = ['área programática', 'inciso', 'unidad ejecutora', 'programa', 'proyecto',
  'grupo', 'subgrupo', 'objeto del gasto', 'fuente de financiamiento']
const DESDE = [1961, 1985, 2005, 2011]

export default function Gasto() {
  const [params, setParams] = useSearchParams()
  const terceros = params.get('terceros') === '1'

  function setTerceros(on: boolean) {
    const next = new URLSearchParams(params)
    if (on) next.set('terceros', '1')
    else next.delete('terceros')
    setParams(next, { replace: true })
  }

  return (
    <>
      <h1>¿A dónde va el gasto público?</h1>
      <p className="lede">
        Lo que gastó el Presupuesto Nacional cada año desde 1961, y en qué: por área, organismo, programa y
        objeto del gasto. No incluye empresas públicas (UTE, ANCAP, OSE), intendencias ni las cuentas propias del BPS.
      </p>
      <label className="field inline" style={{ marginBottom: 16 }}>
        <input type="checkbox" checked={terceros} onChange={(e) => setTerceros(e.target.checked)} />
        Incluir «Fondos de Terceros Declarados por Ley» en 2025 (MEF los cuenta, OPP no: no se comparan con años anteriores)
      </label>
      <Serie terceros={terceros} />
      <Desglose terceros={terceros} />
    </>
  )
}

function Serie({ terceros }: { terceros: boolean }) {
  const colors = useColors()
  const [modo, setModo] = useState<'real' | 'nominal'>('real')
  const [base, setBase] = useState<number | undefined>()
  const [desde, setDesde] = useState(1985)
  const { data, error, loading } = useApi<Spending>(apiUrl('spending', { base, fondos_terceros: terceros }))

  const rows = useMemo(() => (data?.anios ?? []).filter((r) => r.anio >= desde), [data, desde])
  if (error) return <div className="card error">{error}</div>
  if (!data) return <div className="card muted">Cargando la serie (la primera vez tarda unos segundos)…</div>

  const last = rows[rows.length - 1]
  const tenAgo = rows.find((r) => r.anio === last.anio - 10)
  const value = (r: Spending['anios'][number]) => (modo === 'real' ? r.real : r.nominal)
  const unidad = modo === 'real' ? `miles de millones de pesos de ${data.base}` : 'miles de millones de pesos corrientes'

  return (
    <section className={`card ${loading ? 'loading' : ''}`}>
      <div className="card-head">
        <div>
          <h2>Gasto total por año</h2>
          <div className="muted">{unidad}</div>
        </div>
      </div>
      <div className="controls">
        <div className="segmented" role="group" aria-label="Pesos">
          <button aria-pressed={modo === 'real'} onClick={() => setModo('real')}>Sin inflación</button>
          <button aria-pressed={modo === 'nominal'} onClick={() => setModo('nominal')}>Corrientes</button>
        </div>
        {modo === 'real' && (
          <label className="field">
            Pesos de
            <select value={data.base} onChange={(e) => setBase(Number(e.target.value))}>
              {[...data.anios].reverse().map((r) => <option key={r.anio}>{r.anio}</option>)}
            </select>
          </label>
        )}
        <label className="field">
          Desde
          <select value={desde} onChange={(e) => setDesde(Number(e.target.value))}>
            {DESDE.map((y) => <option key={y}>{y}</option>)}
          </select>
        </label>
      </div>
      <div className="stats">
        <div className="stat">
          <div className="label">Gasto {last.anio}</div>
          <div className="value">{pesos(last.nominal)}</div>
        </div>
        {tenAgo && (
          <div className="stat">
            <div className="label">Cambio real vs {tenAgo.anio}</div>
            <div className="value">{signedPct((last.real / tenAgo.real - 1) * 100)}</div>
          </div>
        )}
        <div className="stat">
          <div className="label">Cambio real vs {rows[0].anio}</div>
          <div className="value">{signedPct((last.real / rows[0].real - 1) * 100)}</div>
        </div>
      </div>
      <div style={{ height: 320 }}>
        <ResponsiveContainer>
          <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={colors.grid} vertical={false} />
            <XAxis dataKey="anio" {...axisProps(colors)} minTickGap={24} />
            <YAxis {...axisProps(colors)} axisLine={false} tickFormatter={axisBillions} width={56} />
            <Tooltip
              cursor={{ stroke: colors.axis }}
              content={({ active, payload }) => {
                const r = active && payload?.[0]?.payload
                if (!r) return null
                return <Tip title={`${r.anio} · ${FUENTES[r.fuente]}`} rows={[
                  { color: colors['series-1'], label: modo === 'real' ? `pesos de ${data.base}` : 'pesos corrientes', value: pesos(value(r)) },
                ]} />
              }}
            />
            <Line type="monotone" dataKey={modo} stroke={colors['series-1']} strokeWidth={2} dot={false}
              activeDot={{ r: 5, stroke: colors.surface, strokeWidth: 2 }} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="muted">
        Fuentes: OPP histórico hasta 2010, OPP detallado 2011–2024, MEF 2025. «Sin inflación» ajusta con el IPC
        promedio anual del INE: real = nominal × IPC[base] / IPC[año].
      </p>
      <details>
        <summary>Ver tabla</summary>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Año</th><th>Fuente</th><th className="num">Corrientes</th><th className="num">Pesos de {data.base}</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.anio}>
                  <td>{r.anio}</td><td>{FUENTES[r.fuente]}</td>
                  <td className="num">{pesos(r.nominal)}</td><td className="num">{pesos(r.real)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  )
}

const SHOWN = 25
// A pie reads at a glance only with few slices: the largest five, then everything else as "Otros".
const SLICES = 5
const SLICE_COLORS = ['series-1', 'series-2', 'series-3', 'series-4', 'series-5'] as const

function Desglose({ terceros }: { terceros: boolean }) {
  const [params, setParams] = useSearchParams()
  const anio = params.get('anio') ? Number(params.get('anio')) : undefined
  const camino = params.getAll('n')
  const [todos, setTodos] = useState(false)
  const { data, error, loading } = useApi<Breakdown>(
    apiUrl('breakdown', { year: anio, path: camino, fondos_terceros: terceros }))

  function go(next: { anio?: number; camino: string[] }) {
    const p = new URLSearchParams(params)
    p.delete('n')
    next.camino.forEach((n) => p.append('n', n))
    if (next.anio) p.set('anio', String(next.anio))
    setParams(p)
    setTodos(false)
  }

  const year = data?.anio
  return (
    <section className={`card ${loading ? 'loading' : ''}`}>
      <div className="card-head">
        <div>
          <h2>En qué se gastó</h2>
          <div className="muted">Tocá una fila para entrar un nivel. Montos en pesos corrientes de cada año.</div>
        </div>
        {data && (
          <label className="field">
            Año
            <select value={year} onChange={(e) => go({ anio: Number(e.target.value), camino: [] })}>
              {[...data.anios].reverse().map((y) => <option key={y}>{y}</option>)}
            </select>
          </label>
        )}
      </div>
      {error && (
        <p className="error">
          {error} <button onClick={() => go({ anio, camino: [] })}>Volver al inicio</button>
        </p>
      )}
      {data && <DesgloseLista data={data} todos={todos} onTodos={() => setTodos(true)}
        onPick={(i) => go({ anio: year, camino: i < 0 ? data.camino.slice(0, -i - 1) : [...data.camino, data.items[i].nombre] })} />}
      {!data && !error && <p className="muted">Cargando…</p>}
    </section>
  )
}

/** onPick(i): i >= 0 enters item i; i < 0 goes back to breadcrumb -i - 1. */
function DesgloseLista({ data, todos, onTodos, onPick }: {
  data: Breakdown; todos: boolean; onTodos: () => void; onPick: (i: number) => void
}) {
  const colors = useColors()
  const deepest = data.nivel === data.niveles.length - 1
  const color = (i: number) => (i < SLICES ? colors[SLICE_COLORS[i]] : colors.other)
  const max = Math.max(...data.items.map((i) => i.gasto), 1)
  const items = todos ? data.items : data.items.slice(0, SHOWN)
  const ejecutado = (b: number, s: number) => (b ? pct((s / b) * 100, 0) : '—')

  return (
    <>
      <nav className="crumbs" aria-label="Nivel">
        {['Todo el gasto', ...data.camino].map((name, i) => i === data.camino.length
          ? <span key={i} className="current">{name}</span>
          : <span key={i}><button onClick={() => onPick(-i - 1)}>{name}</button> ›</span>)}
      </nav>
      <div className="stats">
        <div className="stat"><div className="label">Gastado {data.anio}</div><div className="value">{pesos(data.total.gasto)}</div></div>
        <div className="stat"><div className="label">Crédito final</div><div className="value">{pesos(data.total.credito)}</div></div>
        <div className="stat"><div className="label">Ejecutado</div><div className="value">{ejecutado(data.total.credito, data.total.gasto)}</div></div>
      </div>
      <Torta data={data} color={color} onPick={deepest ? undefined : onPick} />
      <h3>Por {NIVELES[data.nivel]} <span className="muted">(nivel {data.nivel + 1} de {data.niveles.length})</span></h3>
      <ol className="bars">
        {items.map((it, i) => (
          <li key={it.nombre}>
            <button className="bar-row" disabled={deepest} onClick={() => onPick(i)}
              title={deepest ? undefined : `Ver por ${NIVELES[data.nivel + 1]}`}>
              <span className="bar-name"><span className="swatch" style={{ background: color(i) }} />{it.nombre}</span>
              <span className="bar-value">{pesos(it.gasto)}</span>
              <span className="bar-track"><span className="bar-fill" style={{ display: 'block', width: `${(it.gasto / max) * 100}%`, background: color(i) }} /></span>
              <span className="bar-meta">
                {pct(data.total.gasto ? (it.gasto / data.total.gasto) * 100 : null)} del total ·
                crédito {pesos(it.credito)} · ejecutado {ejecutado(it.credito, it.gasto)}
              </span>
            </button>
          </li>
        ))}
      </ol>
      {!todos && data.items.length > SHOWN && (
        <button onClick={onTodos} style={{ marginTop: 8 }}>Mostrar los {fmt(data.items.length)}</button>
      )}
      <p className="muted" style={{ marginTop: 12 }}>
        Fuente: {data.fuente === 'mef' ? 'MEF, Rendición de Cuentas' : 'OPP, crédito presupuestal detallado'} {data.anio}.
        «Gastado» es el gasto comprometido (ejecutado u obligado), no lo efectivamente pagado.
      </p>
    </>
  )
}

/** Share of the level's spending: the largest SLICES items plus "Otros". Clicking a named slice drills in. */
function Torta({ data, color, onPick }: { data: Breakdown; color: (i: number) => string; onPick?: (i: number) => void }) {
  const colors = useColors()
  const total = data.total.gasto
  const spent = data.items.filter((it) => it.gasto > 0)
  if (spent.length < 2 || total <= 0) return null
  const named = spent.length <= SLICES + 1 ? spent : spent.slice(0, SLICES)
  const rest = spent.slice(named.length).reduce((s, it) => s + it.gasto, 0)
  const slices = [
    ...named.map((it, i) => ({ nombre: it.nombre, gasto: it.gasto, color: color(i), index: i as number | null })),
    ...(rest > 0 ? [{ nombre: `Otros (${spent.length - named.length})`, gasto: rest, color: colors.other, index: null }] : []),
  ]
  const share = (x: number) => pct((x / total) * 100)
  const pick = (index: number | null) => onPick && index != null && onPick(index)

  return (
    <div className="torta">
      <div style={{ height: 240 }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie data={slices} dataKey="gasto" nameKey="nombre" innerRadius="58%" outerRadius="100%"
              startAngle={90} endAngle={-270} stroke={colors.surface} strokeWidth={2} isAnimationActive={false}
              onClick={(_, i) => pick(slices[i].index)} style={{ cursor: onPick ? 'pointer' : undefined }}>
              {slices.map((s) => <Cell key={s.nombre} fill={s.color} />)}
            </Pie>
            <Tooltip content={({ active, payload }) => {
              const s = active && (payload?.[0]?.payload as (typeof slices)[number] | undefined)
              if (!s) return null
              return <Tip title={s.nombre} rows={[{ color: s.color, label: 'del total', value: share(s.gasto) }, { label: 'gastado', value: pesos(s.gasto) }]} />
            }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="torta-legend">
        {slices.map((s) => (
          <li key={s.nombre}>
            <span className="swatch" style={{ background: s.color }} />
            <span>{s.nombre}</span>
            <span className="pct">{share(s.gasto)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
