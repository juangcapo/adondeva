import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { apiUrl, SECCIONES, sendJson, useApi, type Noticia } from '../api.ts'
import { Texto } from './Noticias.tsx'

type Form = Omit<Noticia, 'id' | 'slug'>

const hoy = () => new Date().toLocaleDateString('sv-SE') // YYYY-MM-DD, local date
const VACIA: Form = {
  tipo: 'link', titulo: '', medio: '', autor: '', fecha: hoy(), url: '', resumen: '', cita: '', cuerpo: '',
  seccion: null, publicada: true,
}

/** Load, edit and delete news board entries. The server asks for the admin password before serving this page. */
export default function NoticiasAdmin() {
  const [version, setVersion] = useState(0)
  const { data, error } = useApi<Noticia[]>(apiUrl('admin/noticias', { v: version || undefined }))
  const [form, setForm] = useState<Form>(VACIA)
  const [editando, setEditando] = useState<number | null>(null)
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [enviando, setEnviando] = useState(false)

  const set = <K extends keyof Form>(k: K, v: Form[K]) => setForm((f) => ({ ...f, [k]: v }))
  const recargar = () => setVersion((v) => v + 1)

  async function guardar(e: FormEvent) {
    e.preventDefault()
    setEnviando(true)
    try {
      await sendJson(editando ? 'PUT' : 'POST', apiUrl(editando ? `admin/noticias/${editando}` : 'admin/noticias'), form)
      setMsg({ ok: true, text: editando ? 'Cambios guardados.' : 'Noticia agregada.' })
      setForm({ ...VACIA, fecha: hoy() })
      setEditando(null)
      recargar()
    } catch (err) {
      setMsg({ ok: false, text: (err as Error).message })
    } finally {
      setEnviando(false)
    }
  }

  function editar(n: Noticia) {
    const { id, slug: _slug, ...rest } = n
    setForm({ ...VACIA, ...Object.fromEntries(Object.entries(rest).map(([k, v]) => [k, v ?? (k === 'seccion' ? null : '')])) } as Form)
    setEditando(id)
    setMsg(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function cambiar(n: Noticia, accion: 'publicar' | 'borrar') {
    if (accion === 'borrar' && !confirm(`¿Borrar «${n.titulo}»? No se puede deshacer.`)) return
    try {
      if (accion === 'borrar') await sendJson('DELETE', apiUrl(`admin/noticias/${n.id}`))
      else {
        const { id, slug: _slug, ...rest } = n
        await sendJson('PUT', apiUrl(`admin/noticias/${id}`), { ...rest, publicada: !n.publicada })
      }
      if (editando === n.id && accion === 'borrar') { setEditando(null); setForm(VACIA) }
      recargar()
    } catch (err) {
      setMsg({ ok: false, text: (err as Error).message })
    }
  }

  const propia = form.tipo === 'propia'
  return (
    <>
      <p><Link to="/admin">← Uso del sitio</Link></p>
      <h1>Noticias</h1>
      <p className="lede">
        Los links a medios llevan un resumen escrito por nosotros y, como mucho, una cita corta.
        No copies el texto de la nota ni uses sus fotos.
      </p>

      <form className="card form" onSubmit={guardar}>
        <h2>{editando ? 'Editar noticia' : 'Nueva noticia'}</h2>
        <div className="segmented" role="group" aria-label="Tipo">
          <button type="button" aria-pressed={!propia} onClick={() => set('tipo', 'link')}>Link a un medio</button>
          <button type="button" aria-pressed={propia} onClick={() => set('tipo', 'propia')}>Nota propia</button>
        </div>
        <label className="field">Título
          <input required minLength={3} maxLength={200} value={form.titulo} onChange={(e) => set('titulo', e.target.value)} />
        </label>
        {!propia && <>
          <label className="field">Link a la nota
            <input required type="url" maxLength={1000} placeholder="https://" value={form.url ?? ''}
              onChange={(e) => set('url', e.target.value)} />
          </label>
          <label className="field">Medio
            <input required maxLength={100} placeholder="La Diaria, El País, Búsqueda…" value={form.medio ?? ''}
              onChange={(e) => set('medio', e.target.value)} />
          </label>
        </>}
        <div className="form-row">
          <label className="field">Fecha
            <input required type="date" value={form.fecha} onChange={(e) => set('fecha', e.target.value)} />
          </label>
          <label className="field">Autor (opcional)
            <input maxLength={100} value={form.autor ?? ''} onChange={(e) => set('autor', e.target.value)} />
          </label>
          <label className="field">Sección vinculada
            <select value={form.seccion ?? ''} onChange={(e) => set('seccion', (e.target.value || null) as Form['seccion'])}>
              <option value="">Ninguna</option>
              {Object.entries(SECCIONES).map(([k, s]) => <option key={k} value={k}>{s.label}</option>)}
            </select>
          </label>
        </div>
        <label className="field">Resumen, con nuestras palabras ({form.resumen.length}/600)
          <textarea required minLength={10} maxLength={600} rows={3} value={form.resumen}
            onChange={(e) => set('resumen', e.target.value)} />
        </label>
        {!propia && (
          <label className="field">Cita textual corta, opcional ({(form.cita ?? '').length}/400)
            <textarea maxLength={400} rows={2} value={form.cita ?? ''} onChange={(e) => set('cita', e.target.value)} />
          </label>
        )}
        {propia && <>
          <label className="field">Texto de la nota
            <textarea required rows={14} maxLength={50000} value={form.cuerpo ?? ''} onChange={(e) => set('cuerpo', e.target.value)} />
          </label>
          <p className="muted">
            Párrafos separados por una línea en blanco. <code>## Subtítulo</code>, <code>- ítem</code>,{' '}
            <code>**negrita**</code>, <code>[texto](https://link)</code>.
          </p>
          {form.cuerpo && <details><summary>Vista previa</summary><div className="card"><Texto src={form.cuerpo} /></div></details>}
        </>}
        <label className="field inline">
          <input type="checkbox" checked={form.publicada} onChange={(e) => set('publicada', e.target.checked)} />
          Publicada (si no, queda como borrador)
        </label>
        <div className="form-row">
          <button type="submit" className="primary" disabled={enviando}>{editando ? 'Guardar cambios' : 'Agregar'}</button>
          {editando && <button type="button" onClick={() => { setEditando(null); setForm(VACIA); setMsg(null) }}>Cancelar</button>}
        </div>
        {msg && <p className={msg.ok ? 'ok' : 'error'} role="status">{msg.text}</p>}
      </form>

      {error && <p className="error">{error}</p>}
      {data && (
        <section className="card">
          <h2>Cargadas ({data.length})</h2>
          {!data.length && <p className="muted">Todavía no hay ninguna.</p>}
          <ul className="admin-lista">
            {data.map((n) => (
              <li key={n.id}>
                <div>
                  <strong>{n.titulo}</strong>
                  <div className="muted">
                    {n.fecha} · {n.tipo === 'propia' ? 'nota propia' : n.medio}
                    {!n.publicada && <> · <span className="badge">borrador</span></>}
                  </div>
                </div>
                <div className="acciones">
                  <button type="button" className="link" onClick={() => editar(n)}>Editar</button>
                  <button type="button" className="link" onClick={() => cambiar(n, 'publicar')}>
                    {n.publicada ? 'Despublicar' : 'Publicar'}
                  </button>
                  <button type="button" className="link" onClick={() => cambiar(n, 'borrar')}>Borrar</button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  )
}
