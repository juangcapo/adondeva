import { useMemo, useState } from 'react'
import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { apiUrl, useApi, type Revenue } from '../api.ts'
import { axisProps, Tip, useColors } from '../chart.tsx'
import { axisBillions, fmt, pct, pesos, signedPct } from '../format.ts'

const GRUPOS: Record<string, string> = {
  renta: 'Renta (personas y empresas)',
  consumo: 'Consumo (bienes y servicios)',
  propiedad: 'Propiedad (patrimonio e inmuebles)',
  otros: 'Otros y ajustes',
}
const GRUPO_CORTO: Record<string, string> = { renta: 'renta', consumo: 'consumo', propiedad: 'propiedad', otros: 'otros' }
const COLORS = ['series-1', 'series-2', 'series-3', 'series-4', 'series-5'] as const
// Before 1990 DGI details only 5 or 6 taxes, so the default view starts there.
const DESDE = [1982, 1990, 2000, 2007]
// "Por impuesto" stacks the taxes that collected the most over the range shown; the rest go into "Otros".
const TOP = 5

type Modo = 'real' | 'nominal' | 'pct'
type Year = Revenue['anios'][number]
type Serie = { key: string; nombre: string; color: string; of: (y: Year) => number }

export default function Recaudacion() {
  const [base, setBase] = useState<number | undefined>()
  const { data, error, loading } = useApi<Revenue>(apiUrl('revenue', { base }))
  const [elegidos, setElegidos] = useState<string[]>([])

  return (
    <>
      <h1>¿De dónde viene la plata?</h1>
      <p className="lede">
        Lo que recaudó la DGI cada año desde 1982, impuesto por impuesto: IVA, IRPF, IRAE, IMESI, Patrimonio y
        los que ya no existen. No incluye los aportes a la seguridad social (BPS), los aranceles de Aduanas ni
        los tributos de las intendencias.
      </p>
      {error && <div className="card error">{error}</div>}
      {!data && !error && <div className="card muted">Cargando…</div>}
      {data && (
        <>
          <Historia data={data} loading={loading} onBase={setBase} />
          <Impuestos data={data} elegidos={elegidos} onElegir={setElegidos} />
        </>
      )}
    </>
  )
}

function Historia({ data, loading, onBase }: { data: Revenue; loading: boolean; onBase: (y: number) => void }) {
  const colors = useColors()
  const [modo, setModo] = useState<Modo>('real')
  const [vista, setVista] = useState<'grupo' | 'impuesto'>('grupo')
  const [desde, setDesde] = useState(1990)
  const years = useMemo(() => data.anios.filter((y) => y.anio >= desde), [data, desde])

  const series = useMemo<Serie[]>(() => {
    const grupo = Object.fromEntries(data.impuestos.map((t) => [t.sigla, t.grupo]))
    if (vista === 'grupo') {
      const sum = (g: string) => (y: Year) =>
        Object.entries(y.montos).reduce((s, [sigla, x]) => (grupo[sigla] === g ? s + x : s), 0)
      return data.grupos.map((g, i) => ({
        key: g, nombre: GRUPOS[g] ?? g, color: g === 'otros' ? colors.other : colors[COLORS[i]], of: sum(g),
      }))
    }
    const realTotal = (sigla: string) => years.reduce((s, y) => s + (y.montos[sigla] ?? 0) * y.factor, 0)
    const top = data.impuestos.filter((t) => t.sigla !== 'AJUSTES')
      .map((t) => ({ t, total: realTotal(t.sigla) })).sort((a, b) => b.total - a.total).slice(0, TOP).map((x) => x.t)
    const named = new Set(top.map((t) => t.sigla))
    return [
      ...top.map((t, i) => ({ key: t.sigla, nombre: t.nombre, color: colors[COLORS[i]], of: (y: Year) => y.montos[t.sigla] ?? 0 })),
      { key: 'resto', nombre: 'Todos los demás', color: colors.other,
        of: (y: Year) => Object.entries(y.montos).reduce((s, [sigla, x]) => (named.has(sigla) ? s : s + x), 0) },
    ]
  }, [data, vista, years, colors])

  const value = (y: Year, x: number) => (modo === 'real' ? x * y.factor : modo === 'pct' ? (x / y.total) * 100 : x)
  const rows = years.map((y) => ({ anio: y.anio, ...Object.fromEntries(series.map((s) => [s.key, value(y, s.of(y))])) }))
  const show = (x: number) => (modo === 'pct' ? pct(x) : pesos(x))
  const unidad = modo === 'real' ? `miles de millones de pesos de ${data.base}`
    : modo === 'pct' ? '% de lo recaudado por la DGI cada año' : 'miles de millones de pesos corrientes'

  const last = years[years.length - 1]
  const first = years[0]
  const tenAgo = years.find((y) => y.anio === last.anio - 10)
  const real = (y: Year) => y.total * y.factor
  const biggest = [...series].sort((a, b) => b.of(last) - a.of(last))[0]

  return (
    <section className={`card ${loading ? 'loading' : ''}`}>
      <div className="card-head">
        <div>
          <h2>Recaudación por año</h2>
          <div className="muted">{unidad}</div>
        </div>
      </div>
      <div className="controls">
        <div className="segmented" role="group" aria-label="Agrupar">
          <button aria-pressed={vista === 'grupo'} onClick={() => setVista('grupo')}>Por tipo</button>
          <button aria-pressed={vista === 'impuesto'} onClick={() => setVista('impuesto')}>Por impuesto</button>
        </div>
        <div className="segmented" role="group" aria-label="Pesos">
          <button aria-pressed={modo === 'real'} onClick={() => setModo('real')}>Sin inflación</button>
          <button aria-pressed={modo === 'nominal'} onClick={() => setModo('nominal')}>Corrientes</button>
          <button aria-pressed={modo === 'pct'} onClick={() => setModo('pct')}>% del total</button>
        </div>
        {modo === 'real' && (
          <label className="field">
            Pesos de
            <select value={data.base} onChange={(e) => onBase(Number(e.target.value))}>
              {[...data.anios].reverse().map((y) => <option key={y.anio}>{y.anio}</option>)}
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
        <div className="stat"><div className="label">Recaudado {last.anio}</div><div className="value">{pesos(last.total)}</div></div>
        {tenAgo && (
          <div className="stat">
            <div className="label">Cambio real vs {tenAgo.anio}</div>
            <div className="value">{signedPct((real(last) / real(tenAgo) - 1) * 100)}</div>
          </div>
        )}
        <div className="stat">
          <div className="label">Cambio real vs {first.anio}</div>
          <div className="value">{signedPct((real(last) / real(first) - 1) * 100)}</div>
        </div>
        <div className="stat">
          <div className="label">Mayor en {last.anio}: {vista === 'grupo' ? GRUPO_CORTO[biggest.key] : biggest.key}</div>
          <div className="value">{pct((biggest.of(last) / last.total) * 100)}</div>
        </div>
      </div>
      <div className="legend">
        {series.map((s) => <span key={s.key}><span className="swatch" style={{ background: s.color }} />{s.nombre}</span>)}
      </div>
      <div style={{ height: 340 }}>
        <ResponsiveContainer>
          <AreaChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={colors.grid} vertical={false} />
            <XAxis dataKey="anio" {...axisProps(colors)} minTickGap={24} />
            <YAxis {...axisProps(colors)} axisLine={false} width={56}
              tickFormatter={modo === 'pct' ? (x: number) => `${fmt(x)}%` : axisBillions}
              domain={modo === 'pct' ? [0, 100] : [0, 'auto']} allowDataOverflow={modo === 'pct'} />
            <Tooltip
              cursor={{ stroke: colors.axis }}
              content={({ active, payload }) => {
                const r = active && (payload?.[0]?.payload as Record<string, number> | undefined)
                if (!r) return null
                const y = years.find((x) => x.anio === r.anio)!
                return <Tip title={`${r.anio} · ${pesos(modo === 'real' ? real(y) : y.total)}`}
                  rows={[...series].reverse().map((s) => ({ color: s.color, label: s.nombre, value: show(r[s.key]) }))} />
              }}
            />
            {series.map((s) => (
              <Area key={s.key} type="monotone" dataKey={s.key} stackId="1" stroke={s.color} fill={s.color}
                fillOpacity={0.85} strokeWidth={1} isAnimationActive={false} />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <p className="muted">
        Fuente: DGI, recaudación anual por impuesto (criterio de caja). Grupos según la clasificación de recursos
        del MEF. «Sin inflación» ajusta con el IPC promedio anual del INE. Hasta 1989 la DGI detalla solo 5 o 6
        impuestos, así que entre 9% y 16% de esos años queda en «Otros y ajustes».
      </p>
    </section>
  )
}

// With nothing picked every tax is drawn, colored by group; the tooltip lists only the largest ones that year.
const TIP_MAX = 8

function Impuestos({ data, elegidos, onElegir }: { data: Revenue; elegidos: string[]; onElegir: (s: string[]) => void }) {
  const colors = useColors()
  const last = data.anios[data.anios.length - 1]
  const tenAgo = data.anios.find((y) => y.anio === last.anio - 10)
  const porSigla = Object.fromEntries(data.impuestos.map((t) => [t.sigla, t]))
  const grupoColor = (g: string) => {
    const i = data.grupos.indexOf(g)
    return g === 'otros' || i < 0 ? colors.other : colors[COLORS[i % COLORS.length]]
  }
  const todos = elegidos.length === 0
  // Picked taxes keep their color by the order they were picked in.
  const lineas = (todos ? data.impuestos.map((t) => t.sigla) : elegidos).map((sigla, i) => ({
    sigla, nombre: porSigla[sigla].nombre,
    color: todos ? grupoColor(porSigla[sigla].grupo) : colors[COLORS[i % COLORS.length]],
  }))
  const serie = data.anios.map((y) => ({
    anio: y.anio,
    ...Object.fromEntries(lineas.map((l) => [l.sigla, y.montos[l.sigla] == null ? null : y.montos[l.sigla] * y.factor])),
  }))
  const toggle = (sigla: string) =>
    onElegir(elegidos.includes(sigla) ? elegidos.filter((s) => s !== sigla) : [...elegidos, sigla])
  const lista = [...data.impuestos].sort((a, b) =>
    (last.montos[b.sigla] ?? 0) - (last.montos[a.sigla] ?? 0) || Number(b.hasta) - Number(a.hasta))
  // No change for a tax that started in or after the comparison year (its first year is partial),
  // nor for AJUSTES, a residual that can flip sign.
  const change = (t: Revenue['impuestos'][number]) => {
    const now = last.montos[t.sigla]
    const then = tenAgo?.montos[t.sigla]
    if (!now || !then || t.sigla === 'AJUSTES' || Number(t.desde) >= tenAgo!.anio) return '—'
    return signedPct(((now * last.factor) / (then * tenAgo!.factor) - 1) * 100)
  }
  const colorDe = Object.fromEntries(lineas.map((l) => [l.sigla, l.color]))
  const unico = elegidos.length === 1 ? porSigla[elegidos[0]] : undefined

  return (
    <section className="card">
      <div className="card-head">
        <div>
          <h2>Cada impuesto</h2>
          <div className="muted">
            Tocá filas para ver solo esos impuestos; tocá de nuevo para quitarlos. Montos sin inflación, en pesos
            de {data.base}.
          </div>
        </div>
      </div>
      {unico ? (
        <h3>{unico.nombre} <span className="muted">· {GRUPOS[unico.grupo]} · {unico.desde}–{unico.hasta}</span></h3>
      ) : (
        <h3>{todos ? 'Todos los impuestos' : `${elegidos.length} impuestos`}</h3>
      )}
      <div className="legend">
        {todos
          ? data.grupos.map((g) => <span key={g}><span className="swatch" style={{ background: grupoColor(g) }} />{GRUPOS[g] ?? g}</span>)
          : lineas.map((l) => <span key={l.sigla}><span className="swatch" style={{ background: l.color }} />{l.nombre}</span>)}
        {!todos && <button className="link" onClick={() => onElegir([])}>Ver todos</button>}
      </div>
      <div style={{ height: 280 }}>
        <ResponsiveContainer>
          <LineChart data={serie} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={colors.grid} vertical={false} />
            <XAxis dataKey="anio" {...axisProps(colors)} minTickGap={24} />
            <YAxis {...axisProps(colors)} axisLine={false} tickFormatter={axisBillions} width={56} />
            <Tooltip
              cursor={{ stroke: colors.axis }}
              content={({ active, payload }) => {
                const r = active && (payload?.[0]?.payload as Record<string, number | null> | undefined)
                if (!r) return null
                const y = data.anios.find((x) => x.anio === r.anio)!
                const filas = lineas.filter((l) => r[l.sigla] != null).sort((a, b) => r[b.sigla]! - r[a.sigla]!)
                const shown = todos ? filas.slice(0, TIP_MAX) : filas
                const resto = filas.length - shown.length
                return <Tip title={String(r.anio)} rows={[
                  ...shown.map((l) => ({
                    color: l.color,
                    label: todos ? l.sigla : `${l.nombre} · ${pct(((y.montos[l.sigla] ?? 0) / y.total) * 100)} del total`,
                    value: pesos(r[l.sigla]!),
                  })),
                  ...(resto > 0 ? [{ label: `y ${resto} más`, value: '' }] : []),
                ]} />
              }}
            />
            {lineas.map((l) => (
              <Line key={l.sigla} type="monotone" dataKey={l.sigla} stroke={l.color} strokeWidth={todos ? 1.25 : 2}
                strokeOpacity={todos ? 0.8 : 1} dot={false} connectNulls={false}
                activeDot={todos ? false : { r: 5, stroke: colors.surface, strokeWidth: 2 }} isAnimationActive={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="table-wrap">
        <table className="pick">
          <thead>
            <tr>
              <th>Impuesto</th><th>Tipo</th><th>Años</th>
              <th className="num">{last.anio}</th><th className="num">% del total</th>
              {tenAgo && <th className="num">Cambio real vs {tenAgo.anio}</th>}
            </tr>
          </thead>
          <tbody>
            {lista.map((t) => {
              const sel = elegidos.includes(t.sigla)
              return (
                <tr key={t.sigla} aria-selected={sel} onClick={() => toggle(t.sigla)}>
                  <td>
                    <span className="swatch" style={{ background: sel ? colorDe[t.sigla] : 'transparent', marginRight: 6 }} />
                    <button className="link" aria-pressed={sel}>{t.nombre}</button>
                  </td>
                  <td>{GRUPO_CORTO[t.grupo]}</td>
                  <td>{t.desde}–{t.hasta}</td>
                  <td className="num">{last.montos[t.sigla] ? pesos(last.montos[t.sigla]) : '—'}</td>
                  <td className="num">{last.montos[t.sigla] ? pct((last.montos[t.sigla] / last.total) * 100) : '—'}</td>
                  {tenAgo && <td className="num">{change(t)}</td>}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}
