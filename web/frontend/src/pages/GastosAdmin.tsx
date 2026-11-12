import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { apiUrl, ESTADOS, sendJson, useApi, type GastoCaso, type GastoEstado, type GastoItem } from '../api.ts'
import { INCISOS, TIPOS_CONTRATACION } from '../arce.ts'
import { money } from '../format.ts'

type Form = { titulo: string; fecha: string; resumen: string; notas: string; publicado: boolean; items: GastoItem[] }

const hoy = () => new Date().toLocaleDateString('sv-SE')
const VACIO: Form = { titulo: '', fecha: hoy(), resumen: '', notas: '', publicado: false, items: [] }
const ITEM: GastoItem = {
  concepto: '', organismo: '', inciso: '', tipo_contratacion: '', monto: null, moneda: 'UYU', estado: 'sin_datos', fuente: '', fuente_url: '', nota: '',
}
const conMonto = (e: GastoEstado) => e === 'confirmado' || e === 'estimado'

/** Load cases of recent public spending and their itemized breakdown. Password asked by the server. */
export default function GastosAdmin() {
  const [version, setVersion] = useState(0)
  const { data, error } = useApi<GastoCaso[]>(apiUrl('admin/gastos-recientes', { v: version || undefined }))
  const [form, setForm] = useState<Form>(VACIO)
  const [editando, setEditando] = useState<number | null>(null)
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [enviando, setEnviando] = useState(false)

  const set = <K extends keyof Form>(k: K, v: Form[K]) => setForm((f) => ({ ...f, [k]: v }))
  const setItem = (n: number, patch: Partial<GastoItem>) =>
    setForm((f) => ({ ...f, items: f.items.map((it, i) => (i === n ? { ...it, ...patch } : it)) }))
  const mover = (n: number, d: -1 | 1) => setForm((f) => {
    const items = [...f.items]
    if (n + d < 0 || n + d >= items.length) return f
    ;[items[n], items[n + d]] = [items[n + d], items[n]]
    return { ...f, items }
  })
  const limpiar = () => { setForm({ ...VACIO, fecha: hoy() }); setEditando(null) }

  async function guardar(e: FormEvent) {
    e.preventDefault()
    setEnviando(true)
    try {
      const body = { ...form, items: form.items.map(({ id: _id, ...it }) => ({ ...it, monto: conMonto(it.estado) ? it.monto : null })) }
      await sendJson(editando ? 'PUT' : 'POST', apiUrl(editando ? `admin/gastos-recientes/${editando}` : 'admin/gastos-recientes'), body)
      setMsg({ ok: true, text: editando ? 'Cambios guardados.' : 'Caso agregado.' })
      limpiar()
      setVersion((v) => v + 1)
    } catch (err) {
      setMsg({ ok: false, text: (err as Error).message })
    } finally {
      setEnviando(false)
    }
  }

  function editar(c: GastoCaso) {
    setForm({
      titulo: c.titulo, fecha: c.fecha, resumen: c.resumen, notas: c.notas ?? '', publicado: c.publicado,
      items: (c.items ?? []).map((i) => ({ ...i, fuente: i.fuente ?? '', fuente_url: i.fuente_url ?? '', nota: i.nota ?? '' })),
    })
    setEditando(c.id)
    setMsg(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function borrar(c: GastoCaso) {
    if (!confirm(`¿Borrar «${c.titulo}» y todo su desglose? No se puede deshacer.`)) return
    try {
      await sendJson('DELETE', apiUrl(`admin/gastos-recientes/${c.id}`))
      if (editando === c.id) limpiar()
      setVersion((v) => v + 1)
    } catch (err) {
      setMsg({ ok: false, text: (err as Error).message })
    }
  }

  return (
    <>
      <p><Link to="/admin">← Uso del sitio</Link> · <Link to="/admin/noticias">Noticias</Link></p>
      <h1>Gastos recientes</h1>
      <p className="lede">
        Cada monto confirmado o estimado necesita el link a su documento (compra, resolución, respuesta a un pedido
        de acceso). Si no hay dato, dejalo como «sin datos» o «pedido en trámite»: no pongas estimaciones propias.
      </p>

      <form className="card form" onSubmit={guardar}>
        <h2>{editando ? 'Editar caso' : 'Nuevo caso'}</h2>
        <div className="form-row">
          <label className="field" style={{ flex: '3 1 260px' }}>Título
            <input required minLength={3} maxLength={200} value={form.titulo} onChange={(e) => set('titulo', e.target.value)} />
          </label>
          <label className="field">Fecha
            <input required type="date" value={form.fecha} onChange={(e) => set('fecha', e.target.value)} />
          </label>
        </div>
        <label className="field">Resumen ({form.resumen.length}/1000)
          <textarea required minLength={10} maxLength={1000} rows={3} value={form.resumen} onChange={(e) => set('resumen', e.target.value)} />
        </label>
        <label className="field">Cómo lo calculamos: metodología, aclaraciones, qué falta (opcional)
          <textarea maxLength={5000} rows={5} value={form.notas} onChange={(e) => set('notas', e.target.value)} />
        </label>

        <h3>Desglose ({form.items.length} ítems)</h3>
        {form.items.map((it, n) => (
          <fieldset className="item" key={n}>
            <legend>Ítem {n + 1}</legend>
            <div className="form-row">
              <label className="field" style={{ flex: '2 1 220px' }}>Concepto
                <input required minLength={2} maxLength={200} value={it.concepto} onChange={(e) => setItem(n, { concepto: e.target.value })} />
              </label>
              <label className="field" style={{ flex: '2 1 220px' }}>Organismo contratante
                <select value={it.inciso ?? ''} onChange={(e) => setItem(n, { inciso: e.target.value })}>
                  <option value="">—</option>
                  {INCISOS.map(([num, nombre]) => <option key={num} value={nombre}>{num} · {nombre}</option>)}
                </select>
              </label>
              <label className="field" style={{ flex: '2 1 220px' }}>Unidad ejecutora
                <input required minLength={2} maxLength={150} value={it.organismo} onChange={(e) => setItem(n, { organismo: e.target.value })} />
              </label>
              <label className="field">Tipo de contratación
                <select value={it.tipo_contratacion ?? ''} onChange={(e) => setItem(n, { tipo_contratacion: e.target.value })}>
                  <option value="">—</option>
                  {TIPOS_CONTRATACION.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </label>
              <label className="field">Estado
                <select value={it.estado} onChange={(e) => setItem(n, { estado: e.target.value as GastoEstado })}>
                  {Object.entries(ESTADOS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </label>
            </div>
            {conMonto(it.estado) && (
              <div className="form-row">
                <label className="field">Monto
                  <input required type="number" min={0} step="any" value={it.monto ?? ''}
                    onChange={(e) => setItem(n, { monto: e.target.value === '' ? null : Number(e.target.value) })} />
                </label>
                <label className="field">Moneda
                  <select value={it.moneda} onChange={(e) => setItem(n, { moneda: e.target.value as GastoItem['moneda'] })}>
                    <option value="UYU">Pesos</option>
                    <option value="USD">Dólares</option>
                  </select>
                </label>
              </div>
            )}
            <div className="form-row">
              <label className="field">Fuente (nombre del documento)
                <input maxLength={200} placeholder="Compra directa 123/2026" value={it.fuente ?? ''}
                  onChange={(e) => setItem(n, { fuente: e.target.value })} />
              </label>
              <label className="field" style={{ flex: '2 1 260px' }}>Link a la fuente
                <input type="url" required={conMonto(it.estado)} maxLength={1000} placeholder="https://" value={it.fuente_url ?? ''}
                  onChange={(e) => setItem(n, { fuente_url: e.target.value })} />
              </label>
            </div>
            <label className="field">Nota (opcional)
              <input maxLength={600} value={it.nota ?? ''} onChange={(e) => setItem(n, { nota: e.target.value })} />
            </label>
            <div className="acciones">
              <button type="button" className="link" onClick={() => mover(n, -1)} disabled={n === 0}>↑ Subir</button>
              <button type="button" className="link" onClick={() => mover(n, 1)} disabled={n === form.items.length - 1}>↓ Bajar</button>
              <button type="button" className="link" onClick={() => set('items', form.items.filter((_, i) => i !== n))}>Quitar</button>
            </div>
          </fieldset>
        ))}
        <div><button type="button" onClick={() => set('items', [...form.items, { ...ITEM }])}>+ Agregar ítem</button></div>

        <label className="field inline">
          <input type="checkbox" checked={form.publicado} onChange={(e) => set('publicado', e.target.checked)} />
          Publicado (si no, queda como borrador)
        </label>
        <div className="form-row">
          <button type="submit" className="primary" disabled={enviando}>{editando ? 'Guardar cambios' : 'Agregar caso'}</button>
          {editando && <button type="button" onClick={() => { limpiar(); setMsg(null) }}>Cancelar</button>}
        </div>
        {msg && <p className={msg.ok ? 'ok' : 'error'} role="status">{msg.text}</p>}
      </form>

      {error && <p className="error">{error}</p>}
      {data && (
        <section className="card">
          <h2>Cargados ({data.length})</h2>
          {!data.length && <p className="muted">Todavía no hay ninguno.</p>}
          <ul className="admin-lista">
            {data.map((c) => (
              <li key={c.id}>
                <div>
                  <strong>{c.titulo}</strong>
                  <div className="muted">
                    {c.fecha} · {c.items?.length ?? 0} ítems
                    {Object.entries(c.totales.confirmado).map(([m, v]) => ` · ${money(v, m as 'UYU' | 'USD')}`)}
                    {!c.publicado && <> · <span className="badge">borrador</span></>}
                  </div>
                </div>
                <div className="acciones">
                  {c.publicado && <Link to={`/gastos-recientes/${c.slug}`}>Ver</Link>}
                  <button type="button" className="link" onClick={() => editar(c)}>Editar</button>
                  <button type="button" className="link" onClick={() => borrar(c)}>Borrar</button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  )
}
