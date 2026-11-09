import { Link, useParams } from 'react-router-dom'
import { apiUrl, ESTADOS, useApi, type GastoCaso, type GastoTotales, type Moneda } from '../api.ts'
import { money } from '../format.ts'
import { Texto } from './Noticias.tsx'

const fecha = (iso: string) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString('es-UY', { day: 'numeric', month: 'long', year: 'numeric' })

const sumas = (m: Partial<Record<Moneda, number>>) =>
  (Object.entries(m) as [Moneda, number][]).map(([k, v]) => money(v, k)).join(' + ')

export default function GastosRecientes() {
  const { data, error } = useApi<GastoCaso[]>(apiUrl('gastos-recientes'))
  return (
    <>
      <h1>Gastos recientes</h1>
      <p className="lede">
        Cuánto le cuestan al Estado algunos hechos de actualidad, ítem por ítem. Cada monto lleva el link a su fuente
        oficial; lo que todavía no se sabe aparece como «sin datos» o «pedido en trámite», nunca como una estimación nuestra.
      </p>
      {error && <p className="error">{error}</p>}
      {data && !data.length && <p className="muted">Todavía no hay casos publicados.</p>}
      {data?.map((c) => (
        <article className="card noticia" key={c.id}>
          <div className="noticia-meta"><span>{fecha(c.fecha)}</span></div>
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
              <tr><th>Concepto</th><th>Organismo</th><th className="num">Monto</th><th>Estado</th><th>Fuente</th></tr>
            </thead>
            <tbody>
              {c.items?.map((i) => (
                <tr key={i.id}>
                  <td>{i.concepto}{i.nota && <div className="muted">{i.nota}</div>}</td>
                  <td>{i.organismo}</td>
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
