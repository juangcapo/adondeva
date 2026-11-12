import { useMemo } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { apiUrl, ESTADOS, useApi, type GastoCaso, type GastoFiltro, type GastoTotales, type Moneda } from '../api.ts'
import { incisoNumero } from '../arce.ts'
import { money } from '../format.ts'
import { Texto } from './Noticias.tsx'

const fecha = (iso: string) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString('es-UY', { day: 'numeric', month: 'long', year: 'numeric' })

const sumas = (m: Partial<Record<Moneda, number>>) =>
  (Object.entries(m) as [Moneda, number][]).map(([k, v]) => money(v, k)).join(' + ')

// The filters ARCE's search starts with; each is a query parameter, so a filtered list can be shared.
const FILTROS = ['inciso', 'ue', 'tipo', 'q'] as const
type Filtro = (typeof FILTROS)[number]

const fold = (s: string) => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
const distintos = (xs: (string | null)[]) => [...new Set(xs.filter((x): x is string => !!x))]

const cumple = (t: GastoFiltro, f: Record<Filtro, string>) =>
  (!f.inciso || t.inciso === f.inciso) && (!f.ue || t.organismo === f.ue) && (!f.tipo || t.tipo_contratacion === f.tipo)

export default function GastosRecientes() {
  const { data, error } = useApi<GastoCaso[]>(apiUrl('gastos-recientes'))
  const [params, setParams] = useSearchParams()
  const f = Object.fromEntries(FILTROS.map((k) => [k, params.get(k) ?? ''])) as Record<Filtro, string>
  const set = (k: Filtro, v: string) => {
    const next = new URLSearchParams(params)
    if (v) next.set(k, v); else next.delete(k)
    if (k === 'inciso') next.delete('ue') // the unidad ejecutora belongs to the organismo, as in ARCE
    setParams(next, { replace: true })
  }
  const todos = useMemo(() => (data ?? []).flatMap((c) => c.filtros ?? []), [data])
  const incisos = distintos(todos.map((t) => t.inciso)).sort((a, b) => incisoNumero(a) - incisoNumero(b) || a.localeCompare(b, 'es'))
  const ues = distintos(todos.filter((t) => !f.inciso || t.inciso === f.inciso).map((t) => t.organismo)).sort((a, b) => a.localeCompare(b, 'es'))
  const tipos = distintos(todos.map((t) => t.tipo_contratacion)).sort((a, b) => a.localeCompare(b, 'es'))
  const palabras = fold(f.q).split(/\s+/).filter(Boolean)
  const visibles = (data ?? []).filter((c) =>
    (!(f.inciso || f.ue || f.tipo) || (c.filtros ?? []).some((t) => cumple(t, f)))
    && palabras.every((w) => fold(`${c.titulo} ${c.resumen} ${(c.filtros ?? []).map((t) => t.organismo).join(' ')}`).includes(w)))
  const activos = FILTROS.some((k) => f[k])

  return (
    <>
      <h1>Gastos recientes</h1>
      <p className="lede">
        Cuánto le cuestan al Estado algunos hechos de actualidad, ítem por ítem. Cada monto lleva el link a su fuente
        oficial; lo que todavía no se sabe aparece como «sin datos» o «pedido en trámite», nunca como una estimación nuestra.
      </p>
      {error && <p className="error">{error}</p>}
      {data && !data.length && <p className="muted">Todavía no hay casos publicados.</p>}
      {!!data?.length && (
        <section className="card filtros" aria-label="Filtrar casos">
          <div className="controls">
            <label className="field">Organismo contratante
              <select value={f.inciso} onChange={(e) => set('inciso', e.target.value)}>
                <option value="">Todos los organismos</option>
                {incisos.map((n) => <option key={n} value={n}>{incisoNumero(n) < 1000 ? `${incisoNumero(n)} · ` : ''}{n}</option>)}
              </select>
            </label>
            <label className="field">Unidad ejecutora
              <select value={f.ue} onChange={(e) => set('ue', e.target.value)}>
                <option value="">Todas las unidades</option>
                {ues.map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
            <label className="field">Tipo de contratación
              <select value={f.tipo} onChange={(e) => set('tipo', e.target.value)}>
                <option value="">Todos los tipos</option>
                {tipos.map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
            <label className="field">Buscar
              <input type="search" value={f.q} onChange={(e) => set('q', e.target.value)} placeholder="catering, pasajes…" />
            </label>
          </div>
          <div className="filtros-pie">
            <span className="muted">{visibles.length} de {data.length} casos</span>
            {activos && <button type="button" className="link" onClick={() => setParams({}, { replace: true })}>Limpiar filtros</button>}
          </div>
        </section>
      )}
      {data && !!data.length && !visibles.length && <p className="muted">Ningún caso con estos filtros.</p>}
      {visibles.map((c) => (
        <article className="card noticia" key={c.id}>
          <div className="noticia-meta">
            <span>{fecha(c.fecha)}</span>
            {distintos((c.filtros ?? []).map((t) => t.inciso)).map((n) => <span key={n}>{n}</span>)}
            {distintos((c.filtros ?? []).map((t) => t.tipo_contratacion)).map((n) => <span key={n}>{n}</span>)}
          </div>
          <h2><Link to={`/gastos-recientes/${c.slug}`}>{c.titulo}</Link></h2>
          <p>{c.resumen}</p>
          <Resumen t={c.totales} />
        </article>
      ))}
    </>
  )
}

function Resumen({ t }: { t: GastoTotales }) {
  const conf = sumas(t.confirmado)
  const est = sumas(t.estimado)
  return (
    <div className="stats">
      <div className="stat"><div className="label">Confirmado con documentos</div><div className="value">{conf || '—'}</div></div>
      {est && <div className="stat"><div className="label">Estimado por las fuentes</div><div className="value">{est}</div></div>}
      <div className="stat"><div className="label">Ítems sin dato todavía</div><div className="value">{t.pendientes}</div></div>
    </div>
  )
}

export function GastoCasoPage() {
  const { slug = '' } = useParams()
  const { data: c, error } = useApi<GastoCaso>(apiUrl(`gastos-recientes/${encodeURIComponent(slug)}`))
  if (error) return <><p className="error">{error}</p><p><Link to="/gastos-recientes">← Gastos recientes</Link></p></>
  if (!c) return <p className="muted">Cargando…</p>
  return (
    <>
      <p><Link to="/gastos-recientes">← Gastos recientes</Link></p>
      <h1>{c.titulo}</h1>
      <p className="muted">{fecha(c.fecha)}</p>
      <p className="lede">{c.resumen}</p>
      <Resumen t={c.totales} />
      <section className="card">
        <h2>Desglose</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Concepto</th><th>Organismo</th><th>Contratación</th><th className="num">Monto</th><th>Estado</th><th>Fuente</th></tr>
            </thead>
            <tbody>
              {c.items?.map((i) => (
                <tr key={i.id}>
                  <td>{i.concepto}{i.nota && <div className="muted">{i.nota}</div>}</td>
                  <td>{i.inciso && i.inciso !== i.organismo ? <>{i.inciso}<div className="muted">{i.organismo}</div></> : i.organismo}</td>
                  <td>{i.tipo_contratacion ?? '—'}</td>
                  <td className="num">{i.monto == null ? '—' : money(i.monto, i.moneda)}</td>
                  <td><span className={`badge estado-${i.estado}`}>{ESTADOS[i.estado]}</span></td>
                  <td>{i.fuente_url
                    ? <a href={i.fuente_url} target="_blank" rel="noopener noreferrer">{i.fuente || 'Ver fuente'} ↗</a>
                    : (i.fuente ?? '—')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted">
          Los totales suman solo montos con documento, por moneda: pesos y dólares no se convierten entre sí.
        </p>
      </section>
      {c.notas && <section className="card nota"><h2>Cómo lo calculamos</h2><Texto src={c.notas} /></section>}
    </>
  )
}
