import { Fragment, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiUrl, SECCIONES, track, useApi, type Noticia } from '../api.ts'

const fecha = (iso: string) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString('es-UY', { day: 'numeric', month: 'long', year: 'numeric' })

export default function Noticias() {
  const { data, error } = useApi<Noticia[]>(apiUrl('noticias'))
  return (
    <>
      <h1>Noticias</h1>
      <p className="lede">
        Notas de prensa e investigaciones sobre el gasto y los impuestos, y las notas propias de ¿A dónde va?.
        Los resúmenes son nuestros; para leer la nota completa, seguí el link al medio.
      </p>
      {error && <p className="error">{error}</p>}
      {data && !data.length && <p className="muted">Todavía no hay noticias.</p>}
      {data?.map((n) => <Tarjeta key={n.id} n={n} />)}
    </>
  )
}

function Tarjeta({ n }: { n: Noticia }) {
  const propia = n.tipo === 'propia'
  return (
    <article className="card noticia">
      <div className="noticia-meta">
        {propia ? <span className="badge">Nota de ¿A dónde va?</span> : <strong>{n.medio}</strong>}
        <span>{fecha(n.fecha)}</span>
        {n.autor && <span>{n.autor}</span>}
      </div>
      <h2>
        {propia
          ? <Link to={`/noticias/${n.slug}`}>{n.titulo}</Link>
          : <a href={n.url ?? undefined} target="_blank" rel="noopener noreferrer"
              onClick={() => track('evento', 'noticia-abrir', { datos: { id: n.id } })}>{n.titulo} ↗</a>}
      </h2>
      <p>{n.resumen}</p>
      {n.cita && (
        <blockquote>
          «{n.cita}»
          <footer>— {[n.autor, n.medio].filter(Boolean).join(', ')}</footer>
        </blockquote>
      )}
      {n.seccion && (
        <p className="muted">Ver los datos: <Link to={SECCIONES[n.seccion].to}>{SECCIONES[n.seccion].label}</Link></p>
      )}
    </article>
  )
}

export function NotaPropia() {
  const { slug = '' } = useParams()
  const { data: n, error } = useApi<Noticia>(apiUrl(`noticias/${encodeURIComponent(slug)}`))
  if (error) return <><p className="error">{error}</p><p><Link to="/noticias">← Volver a noticias</Link></p></>
  if (!n) return <p className="muted">Cargando…</p>
  return (
    <article className="nota">
      <p><Link to="/noticias">← Noticias</Link></p>
      <h1>{n.titulo}</h1>
      <p className="muted">{fecha(n.fecha)}{n.autor && ` · ${n.autor}`}</p>
      <p className="lede">{n.resumen}</p>
      <Texto src={n.cuerpo ?? ''} />
      {n.seccion && (
        <p className="muted">Ver los datos: <Link to={SECCIONES[n.seccion].to}>{SECCIONES[n.seccion].label}</Link></p>
      )}
    </article>
  )
}

/** A small Markdown subset: paragraphs, ## / ### headings, - lists, **bold** and [text](https://...) links.
 *  Rendered as React elements, never as HTML, so the text can't inject markup. */
export function Texto({ src }: { src: string }) {
  const blocks = src.replace(/\r\n/g, '\n').split(/\n\s*\n/).map((b) => b.trim()).filter(Boolean)
  return (
    <div className="texto">
      {blocks.map((b, i) => {
        if (b.startsWith('### ')) return <h3 key={i}>{inline(b.slice(4))}</h3>
        if (b.startsWith('## ')) return <h2 key={i}>{inline(b.slice(3))}</h2>
        const lines = b.split('\n')
        if (lines.every((l) => /^[-*] /.test(l))) return <ul key={i}>{lines.map((l, j) => <li key={j}>{inline(l.slice(2))}</li>)}</ul>
        return <p key={i}>{lines.map((l, j) => <Fragment key={j}>{j > 0 && <br />}{inline(l)}</Fragment>)}</p>
      })}
    </div>
  )
}

function inline(text: string): ReactNode[] {
  const out: ReactNode[] = []
  const re = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|\*\*([^*]+)\*\*/g
  let last = 0
  for (const m of text.matchAll(re)) {
    if (m.index > last) out.push(text.slice(last, m.index))
    out.push(m[1]
      ? <a key={m.index} href={m[2]} target="_blank" rel="noopener noreferrer">{m[1]}</a>
      : <strong key={m.index}>{m[3]}</strong>)
    last = m.index + m[0].length
  }
  if (last < text.length) out.push(text.slice(last))
  return out
}
