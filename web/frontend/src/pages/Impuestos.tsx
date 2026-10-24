import { useEffect, useState, type ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import { apiUrl, useApi, type NcmLine, type TaxResult } from '../api.ts'
import { useColors } from '../chart.tsx'
import { fmt, pct, rate } from '../format.ts'

type Accion = 'sueldo' | 'compra' | 'importar' | 'alquiler'

const ACCIONES: { id: Accion; label: string; monto: string; inicial: number }[] = [
  { id: 'sueldo', label: 'Sueldo', monto: 'Sueldo nominal mensual (UYU)', inicial: 80000 },
  { id: 'compra', label: 'Compra', monto: 'Precio (UYU)', inicial: 1500 },
  { id: 'importar', label: 'Importación', monto: 'Valor (USD)', inicial: 300 },
  { id: 'alquiler', label: 'Alquiler', monto: 'Alquiler mensual cobrado (UYU)', inicial: 30000 },
]

const PAGA: Record<string, string> = { empresa: 'la empresa' }
const article = (who: string) => PAGA[who] ?? `el ${who}`

function useDebounced<T>(value: T, ms = 300) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

export default function Impuestos() {
  const [params, setParams] = useSearchParams()
  const accion = (ACCIONES.find((a) => a.id === params.get('accion'))?.id ?? 'sueldo') as Accion

  return (
    <>
      <h1>¿Cuánto se lleva el Estado?</h1>
      <p className="lede">
        Elegí una situación y un monto para ver cada impuesto y aporte que se paga, con las tasas vigentes en 2026.
      </p>
      <div className="segmented" role="tablist" style={{ marginBottom: 16 }}>
        {ACCIONES.map((a) => (
          <button key={a.id} role="tab" aria-pressed={a.id === accion} aria-selected={a.id === accion}
            onClick={() => setParams({ accion: a.id }, { replace: true })}>{a.label}</button>
        ))}
      </div>
      <Calculadora key={accion} accion={ACCIONES.find((a) => a.id === accion)!} />
    </>
  )
}

function Calculadora({ accion }: { accion: (typeof ACCIONES)[number] }) {
  const [monto, setMonto] = useState(String(accion.inicial))
  const [hijos, setHijos] = useState('0')
  const [conyuge, setConyuge] = useState(false)
  const [tasa, setTasa] = useState('basica')
  const [neto, setNeto] = useState(false)
  const [envio, setEnvio] = useState(true)
  const [eeuu, setEeuu] = useState(false)
  const [cupo, setCupo] = useState('800')
  const [ncm, setNcm] = useState<NcmLine | null>(null)
  const [arancel, setArancel] = useState('')
  const [mercosur, setMercosur] = useState(false)
  const [contribuyente, setContribuyente] = useState(false)

  const id = accion.id
  const general = id === 'importar' && !envio
  const ready = Number(monto) > 0 && (!general || ncm || arancel !== '')
  const url = useDebounced(ready ? apiUrl(`tax/${id}`, {
    monto,
    ...(id === 'sueldo' && { hijos, conyuge }),
    ...(id === 'compra' && { tasa, neto }),
    ...(id === 'importar' && envio && { envio, eeuu, cupo }),
    ...(general && { tasa, mercosur, contribuyente, ...(ncm ? { ncm: ncm.ncm } : { arancel }) }),
  }) : null)
  const { data, error, loading } = useApi<TaxResult>(url)
  const moneda = id === 'importar' ? 'USD' : '$'

  return (
    <div className="grid-2">
      <section className="card">
        <h2>Datos</h2>
        <div className="controls" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
          <label className="field">
            {accion.monto}
            <input type="number" min="0" step="any" inputMode="decimal" value={monto} onChange={(e) => setMonto(e.target.value)} />
          </label>
          {id === 'sueldo' && <>
            <label className="field">
              Hijos menores a cargo
              <input type="number" min="0" step="1" value={hijos} onChange={(e) => setHijos(e.target.value)} />
            </label>
            <Check checked={conyuge} onChange={setConyuge}>Cónyuge a cargo en FONASA</Check>
          </>}
          {id === 'compra' && <>
            <label className="field">
              IVA
              <select value={tasa} onChange={(e) => setTasa(e.target.value)}>
                <option value="basica">Tasa básica</option>
                <option value="minima">Tasa mínima</option>
                <option value="debito">Pago con débito o dinero electrónico</option>
                <option value="exento">Exento</option>
              </select>
            </label>
            <Check checked={neto} onChange={setNeto}>El precio todavía no incluye IVA</Check>
          </>}
          {id === 'importar' && <>
            <div className="segmented" role="group" aria-label="Régimen">
              <button aria-pressed={envio} onClick={() => setEnvio(true)}>Courier o correo</button>
              <button aria-pressed={!envio} onClick={() => setEnvio(false)}>Régimen general</button>
            </div>
            {envio ? <>
              <Check checked={eeuu} onChange={setEeuu}>Vendedor de EE.UU. registrado en la DNA</Check>
              <label className="field">
                Cupo de franquicia que te queda este año (USD)
                <input type="number" min="0" step="any" value={cupo} onChange={(e) => setCupo(e.target.value)} />
              </label>
            </> : <>
              <NcmPicker value={ncm} onChange={setNcm} />
              {!ncm && (
                <label className="field">
                  …o arancel en %
                  <input type="number" min="0" step="any" value={arancel} onChange={(e) => setArancel(e.target.value)} />
                </label>
              )}
              <label className="field">
                IVA
                <select value={tasa === 'minima' ? 'minima' : 'basica'} onChange={(e) => setTasa(e.target.value)}>
                  <option value="basica">Tasa básica</option>
                  <option value="minima">Tasa mínima</option>
                </select>
              </label>
              <Check checked={mercosur} onChange={setMercosur}>Origen Mercosur</Check>
              <Check checked={contribuyente} onChange={setContribuyente}>El importador es contribuyente de IRAE</Check>
            </>}
          </>}
        </div>
      </section>
      <section className={`card ${loading ? 'loading' : ''}`} aria-live="polite">
        <h2>Resultado</h2>
        {!ready && <p className="muted">{general ? 'Buscá un código NCM o indicá el arancel.' : 'Ingresá un monto.'}</p>}
        {ready && error && <p className="error">{error}</p>}
        {ready && data && !error && <Resultado data={data} accion={id} moneda={moneda} />}
      </section>
    </div>
  )
}

function Check({ checked, onChange, children }: { checked: boolean; onChange: (v: boolean) => void; children: ReactNode }) {
  return (
    <label className="field inline">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      {children}
    </label>
  )
}

function NcmPicker({ value, onChange }: { value: NcmLine | null; onChange: (v: NcmLine | null) => void }) {
  const [q, setQ] = useState('')
  const query = useDebounced(q.trim())
  const { data } = useApi<NcmLine[]>(query.length >= 2 && !value ? apiUrl('ncm', { q: query }) : null)

  if (value) {
    return (
      <div className="field">
        Producto
        <div>
          <strong>{value.ncm}</strong> {value.descripcion}{' '}
          <span className="muted">(arancel {value.tga_extrazona_pct}% extrazona)</span>{' '}
          <button onClick={() => onChange(null)}>Cambiar</button>
        </div>
      </div>
    )
  }
  return (
    <div className="field">
      <label htmlFor="ncm">Producto: código NCM o descripción</label>
      <input id="ncm" type="search" placeholder="8471.30 o «café»" value={q} onChange={(e) => setQ(e.target.value)} />
      {data && query.length >= 2 && (
        data.length ? (
          <ul className="ncm-results">
            {data.map((r) => (
              <li key={r.ncm}>
                <button onClick={() => onChange(r)}><strong>{r.ncm}</strong> {r.descripcion}</button>
              </li>
            ))}
          </ul>
        ) : <span className="muted">Sin resultados.</span>
      )}
    </div>
  )
}

function Resultado({ data, accion, moneda }: { data: TaxResult; accion: Accion; moneda: string }) {
  const money = (x: number | null) => (x == null ? '' : `${moneda} ${fmt(x, 2)}`)
  const isPct = (name: string) => name.startsWith('%')
  return (
    <>
      <div className="stats">
        {data.totales.map((t) => (
          <div className="stat" key={t.nombre}>
            <div className="label">{t.nombre}</div>
            <div className="value">{isPct(t.nombre) ? pct(t.valor) : money(t.valor)}</div>
          </div>
        ))}
      </div>
      {accion === 'sueldo' && <SueldoSplit data={data} />}
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Concepto</th><th className="num">Tasa</th><th className="num">Monto</th></tr>
          </thead>
          <tbody>
            {data.filas.map((f, i) => [
              f.paga !== data.filas[i - 1]?.paga && <tr key={`g${i}`} className="group"><td colSpan={3}>Paga {article(f.paga)}</td></tr>,
              <tr key={i}>
                <td>{f.concepto}{f.base != null && <div className="muted">sobre {money(f.base)}</div>}</td>
                <td className="num">{f.tasa == null ? '' : rate(f.tasa)}</td>
                <td className="num">{money(f.monto)}</td>
              </tr>,
            ])}
          </tbody>
        </table>
      </div>
      <p className="muted" style={{ marginTop: 12 }}>{data.unidad}.</p>
    </>
  )
}

/** Where the employer's total cost goes: take-home pay, worker's taxes, employer's taxes. */
function SueldoSplit({ data }: { data: TaxResult }) {
  const colors = useColors()
  const by = (who: string) => data.filas.filter((f) => f.paga === who).reduce((s, f) => s + f.monto, 0)
  const liquido = data.totales.find((t) => t.nombre === 'sueldo líquido')?.valor ?? 0
  const parts = [
    { label: 'Sueldo líquido', value: liquido, color: colors['series-1'] },
    { label: 'Impuestos y aportes del trabajador', value: by('trabajador'), color: colors['series-2'] },
    { label: 'Aportes de la empresa', value: by('empresa'), color: colors['series-3'] },
  ]
  const total = parts.reduce((s, p) => s + p.value, 0)
  if (!total) return null
  return (
    <div style={{ marginBottom: 16 }}>
      <div className="legend">
        {parts.map((p) => (
          <span key={p.label}><span className="swatch" style={{ background: p.color }} />{p.label} {pct((p.value / total) * 100)}</span>
        ))}
      </div>
      <div className="split" role="img" aria-label={parts.map((p) => `${p.label} ${pct((p.value / total) * 100)}`).join(', ')}>
        {parts.filter((p) => p.value > 0).map((p) => (
          <div key={p.label} title={`${p.label}: $ ${fmt(p.value, 2)}`} style={{ width: `${(p.value / total) * 100}%`, background: p.color }} />
        ))}
      </div>
      <div className="muted">De cada $100 que la empresa gasta en este sueldo.</div>
    </div>
  )
}
