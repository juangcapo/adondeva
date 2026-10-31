import { useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { apiUrl, useApi } from '../api.ts'
import { axisProps, Tip, useColors } from '../chart.tsx'
import { fmt } from '../format.ts'

type Fila = { nombre: string | null; n: number; visitantes?: number }
type Stats = {
  dias: number
  totales: { visitantes: number; paginas: number; consultas: number; eventos: number }
  por_dia: { dia: string; visitantes: number; paginas: number; consultas: number }[]
  paginas: Fila[]; referrers: Fila[]; navegadores: Fila[]; dispositivos: Fila[]; idiomas: Fila[]; regiones: Fila[]; paises: Fila[]
  api: Fila[]; eventos: Fila[]; desglose: Fila[]; ncm: Fila[]
  impuestos: { sigla: string; nombre: string; visitantes: number; agregado: number; quitado: number }[]
  calculadora: (Fila & { monto_min: number | null; monto_max: number | null })[]
  errores: (Fila & { estado: number })[]
  bots: number
}

const RANGOS = [7, 30, 90, 365]
const PAIS = new Intl.DisplayNames(['es'], { type: 'region' })
// Cloudflare's codes: XX unknown, T1 Tor.
const paisNombre = (code: string | null) => {
  if (!code || code === 'XX') return 'desconocido'
  if (code === 'T1') return 'red Tor'
  try {
    return `${PAIS.of(code) ?? code} (${code})`
  } catch {
    return code
  }
}

/** Private usage dashboard: the server asks for the admin password before serving this page. */
export default function Admin() {
  const colors = useColors()
  const [dias, setDias] = useState(30)
  const { data, error, loading } = useApi<Stats>(apiUrl('admin/stats', { dias }))

  return (
    <>
      <h1>Uso del sitio</h1>
      <p className="lede">Visitas y consultas registradas, sin bots. Visitante: una persona por día (no se guardan IP ni cookies).</p>
      <div className="controls">
        <div className="segmented" role="group" aria-label="Período">
          {RANGOS.map((d) => <button key={d} aria-pressed={d === dias} onClick={() => setDias(d)}>{d} días</button>)}
        </div>
        <a href={apiUrl('admin/export.csv', { dias })}>Descargar CSV ({dias} días)</a>
        <a href={apiUrl('admin/export.csv')}>Descargar todo</a>
      </div>
      {error && <div className="card error">{error}</div>}
      {!data && !error && <div className="card muted">Cargando…</div>}
      {data && (
        <div className={loading ? 'loading' : ''}>
          <div className="stats">
            <Stat label="Visitantes (suma por día)" value={data.por_dia.reduce((s, d) => s + d.visitantes, 0)} />
            <Stat label="Páginas vistas" value={data.totales.paginas} />
            <Stat label="Consultas a la API" value={data.totales.consultas} />
            <Stat label="Interacciones" value={data.totales.eventos} />
            <Stat label="Requests de bots (excluidos)" value={data.bots} />
          </div>
          <section className="card">
            <h2>Por día</h2>
            <div className="legend">
              <span><span className="swatch" style={{ background: colors['series-1'] }} />Visitantes</span>
              <span><span className="swatch" style={{ background: colors['series-2'] }} />Páginas vistas</span>
            </div>
            <div style={{ height: 260 }}>
              <ResponsiveContainer>
                <LineChart data={data.por_dia} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
                  <CartesianGrid stroke={colors.grid} vertical={false} />
                  <XAxis dataKey="dia" {...axisProps(colors)} minTickGap={24} />
                  <YAxis {...axisProps(colors)} axisLine={false} allowDecimals={false} width={40} />
                  <Tooltip cursor={{ stroke: colors.axis }} content={({ active, payload }) => {
                    const r = active && (payload?.[0]?.payload as Stats['por_dia'][number] | undefined)
                    if (!r) return null
                    return <Tip title={r.dia} rows={[
                      { color: colors['series-1'], label: 'visitantes', value: fmt(r.visitantes) },
                      { color: colors['series-2'], label: 'páginas vistas', value: fmt(r.paginas) },
                      { label: 'consultas', value: fmt(r.consultas) },
                    ]} />
                  }} />
                  <Line dataKey="visitantes" stroke={colors['series-1']} strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line dataKey="paginas" stroke={colors['series-2']} strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
          <section className="card">
            <h2>Impuestos que interesan</h2>
            <div className="muted">Los que la gente elige en Recaudación › Cada impuesto, ordenados por cuántas personas lo eligieron.</div>
            {data.impuestos.length ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Impuesto</th><th className="num">Personas que lo eligieron</th><th className="num">Veces agregado</th><th className="num">Veces quitado</th></tr>
                  </thead>
                  <tbody>
                    {data.impuestos.map((t) => (
                      <tr key={t.sigla}>
                        <td>{t.nombre}</td>
                        <td className="num">{fmt(t.visitantes)}</td>
                        <td className="num">{fmt(t.agregado)}</td>
                        <td className="num">{fmt(t.quitado)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <p className="muted">Nadie eligió impuestos todavía.</p>}
          </section>
          <div className="grid-2">
            <Top titulo="Páginas" filas={data.paginas} />
            <Top titulo="De dónde vienen" filas={data.referrers} vacio="Nadie llegó desde otro sitio." />
            <Top titulo="Desglose del gasto (año · camino)" filas={data.desglose} />
            <section className="card">
              <h2>Calculadora</h2>
              <Tabla filas={data.calculadora.map((c) => ({
                ...c, extra: c.monto_min == null ? '' : `${fmt(c.monto_min)} – ${fmt(c.monto_max ?? 0)}`,
              }))} extra="Montos" />
            </section>
            <Top titulo="Interacciones" filas={data.eventos} />
            <Top titulo="Búsquedas NCM" filas={data.ncm} />
            <Top titulo="Consultas por endpoint" filas={data.api} />
            <Top titulo="Navegadores" filas={data.navegadores} />
            <Top titulo="Dispositivos" filas={data.dispositivos} />
            <Top titulo="Idiomas" filas={data.idiomas} />
            <Top titulo="Países" filas={data.paises.map((p) => ({ ...p, nombre: paisNombre(p.nombre) }))}
              vacio="Sin datos: el país llega solo a través de Cloudflare." />
            <Top titulo="Región de Fly (ubicación aproximada)" filas={data.regiones} />
            <section className="card">
              <h2>Errores</h2>
              {data.errores.length ? <Tabla filas={data.errores.map((e) => ({ ...e, extra: String(e.estado) }))} extra="Estado" />
                : <p className="muted">Sin errores.</p>}
            </section>
          </div>
        </div>
      )}
    </>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return <div className="stat"><div className="label">{label}</div><div className="value">{fmt(value)}</div></div>
}

function Top({ titulo, filas, vacio = 'Sin datos todavía.' }: { titulo: string; filas: Fila[]; vacio?: string }) {
  return (
    <section className="card">
      <h2>{titulo}</h2>
      {filas.length ? <Tabla filas={filas} /> : <p className="muted">{vacio}</p>}
    </section>
  )
}

function Tabla({ filas, extra }: { filas: (Fila & { extra?: string })[]; extra?: string }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th></th><th className="num">Veces</th><th className="num">Visitantes</th>{extra && <th className="num">{extra}</th>}</tr>
        </thead>
        <tbody>
          {filas.map((f, i) => (
            <tr key={i}>
              <td style={{ minWidth: '8em', overflowWrap: 'anywhere' }}>{f.nombre || '—'}</td>
              <td className="num">{fmt(f.n)}</td>
              <td className="num">{f.visitantes == null ? '' : fmt(f.visitantes)}</td>
              {extra && <td className="num">{f.extra}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
