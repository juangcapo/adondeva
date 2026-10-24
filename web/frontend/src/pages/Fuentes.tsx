import { useMemo, useState } from 'react'
import { apiUrl, useApi, type Sources } from '../api.ts'

const NIVELES: Record<string, string> = {
  nacional: 'Nacional', organismos: 'Organismos', aduana: 'Aduana', seguridad_social: 'Seguridad social',
  departamental: 'Departamental', derogado: 'Derogados',
}

const fold = (s: string) => s.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase()

export default function Fuentes() {
  const { data, error } = useApi<Sources>(apiUrl('sources'))
  const [q, setQ] = useState('')
  const [nivel, setNivel] = useState('')

  const impuestos = useMemo(() => (data?.impuestos ?? []).filter((t) =>
    (!nivel || t.nivel === nivel) && (!q || fold(`${t.nombre} ${t.sigla} ${t.recauda} ${t.notas}`).includes(fold(q)))),
  [data, q, nivel])

  return (
    <>
      <h1>Fuentes de datos</h1>
      <p className="lede">
        De dónde sale cada número, qué años cubre y qué problemas tiene. Todos los archivos están en el{' '}
        <a href="https://github.com/juangcapo/adondeva">repositorio</a>, con su origen documentado.
      </p>
      {error && <p className="error">{error}</p>}
      {data && <>
        <div className="grid-2" style={{ marginBottom: 24 }}>
          {data.datasets.map((d) => (
            <section className="card" key={d.id}>
              <div className="muted">{d.organismo}</div>
              <h2>{d.nombre}</h2>
              {d.cobertura && (
                <p><strong>{d.cobertura.desde}–{d.cobertura.hasta}</strong> <span className="muted">({d.cobertura.anios} años)</span></p>
              )}
              <p>{d.detalle}</p>
              {d.advertencias.length > 0 && (
                <ul className="muted" style={{ paddingLeft: 18 }}>
                  {d.advertencias.map((a) => <li key={a}>{a}</li>)}
                </ul>
              )}
              <a href={d.url} target="_blank" rel="noreferrer">Ver fuente original</a>
            </section>
          ))}
        </div>
        <section className="card">
          <div className="card-head">
            <div>
              <h2>Catálogo de impuestos, tasas y contribuciones</h2>
              <div className="muted">{impuestos.length} de {data.impuestos.length}</div>
            </div>
          </div>
          <div className="controls">
            <label className="field">
              Buscar
              <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="IVA, contribución, BPS…" />
            </label>
            <label className="field">
              Nivel
              <select value={nivel} onChange={(e) => setNivel(e.target.value)}>
                <option value="">Todos</option>
                {Object.entries(NIVELES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Nombre</th><th>Recauda</th><th>Nivel</th><th>Estado</th></tr></thead>
              <tbody>
                {impuestos.map((t, i) => (
                  <tr key={i}>
                    <td>
                      {t.nombre}{t.sigla && <strong> ({t.sigla})</strong>}
                      {t.notas && <div className="muted">{t.notas}</div>}
                    </td>
                    <td>{t.recauda}</td>
                    <td>{NIVELES[t.nivel] ?? t.nivel}</td>
                    <td>{t.estado}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </>}
    </>
  )
}
