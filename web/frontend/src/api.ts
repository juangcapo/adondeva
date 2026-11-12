import { useEffect, useRef, useState } from 'react'

export type Dataset = {
  id: string
  nombre: string
  organismo: string
  url: string
  detalle: string
  advertencias: string[]
  cobertura: { desde: number; hasta: number; anios: number } | null
}

export type Impuesto = {
  nivel: string
  recauda: string
  nombre: string
  sigla: string
  tipo: string
  estado: string
  notas: string
}

export type Sources = { datasets: Dataset[]; impuestos: Impuesto[] }

export type Spending = {
  base: number
  anios: { anio: number; fuente: string; nominal: number; real: number }[]
}

export type Revenue = {
  base: number
  grupos: string[]
  impuestos: { sigla: string; nombre: string; grupo: string; desde: string; hasta: string }[]
  /** factor turns that year's pesos into pesos of `base`; montos add up to total. */
  anios: { anio: number; total: number; factor: number; montos: Record<string, number> }[]
}

export type Breakdown = {
  anio: number
  fuente: string
  anios: number[]
  niveles: string[]
  camino: string[]
  nivel: number
  items: { nombre: string; credito: number; gasto: number }[]
  total: { credito: number; gasto: number }
}

export type TaxResult = {
  unidad: string
  filas: { paga: string; concepto: string; base: number | null; tasa: number | null; monto: number }[]
  totales: { nombre: string; valor: number }[]
}

export type NcmLine = { ncm: string; descripcion: string; tga_extrazona_pct: string; tga_intrazona_pct: string }

export function apiUrl(path: string, params: Record<string, string | number | boolean | string[] | undefined> = {}) {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === false || v === '') continue
    for (const one of Array.isArray(v) ? v : [v]) q.append(k, String(one))
  }
  const s = q.toString()
  return `/api/${path}${s ? `?${s}` : ''}`
}

async function fetchJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const r = await fetch(url, { signal })
  const body = await r.json().catch(() => null)
  if (!r.ok) {
    const detail = body?.detail
    const msg = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail[0]?.msg : null
    throw new Error(msg ?? `Error ${r.status}`)
  }
  return body as T
}

/** Fetch `url` whenever it changes. Keeps the previous data while the next request loads. */
export function useApi<T>(url: string | null) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!url) return
    const ctrl = new AbortController()
    setLoading(true)
    fetchJson<T>(url, ctrl.signal)
      .then((d) => {
        setData(d)
        setError(null)
      })
      .catch((e) => {
        if (!ctrl.signal.aborted) setError(e.message)
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setLoading(false)
      })
    return () => ctrl.abort()
  }, [url])

  // A request aborted because url turned null never clears `loading`; there is nothing to load then.
  return { data, error, loading: url !== null && loading }
}

/** Log a page view or an interaction the API doesn't see. Fire and forget: the log never gets in the way. */
export function track(tipo: 'pagina' | 'evento', ruta: string, extra: { referrer?: string; datos?: Record<string, unknown> } = {}) {
  try {
    fetch('/api/hit', {
      method: 'POST', keepalive: true, headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tipo, ruta, ...extra }),
    }).catch(() => {})
  } catch {
    // ignore
  }
}

/** Log `ruta` with the new values whenever they change after the first render (view toggles the API never sees). */
export function useTrackChange(ruta: string, datos: Record<string, string | number | boolean>) {
  const key = JSON.stringify(datos)
  const prev = useRef(key)
  useEffect(() => {
    if (prev.current === key) return
    prev.current = key
    track('evento', ruta, { datos: JSON.parse(key) })
  }, [ruta, key])
}

export type Seccion = 'gasto' | 'recaudacion' | 'impuestos'

/** The site sections a news item can point to. */
export const SECCIONES: Record<Seccion, { label: string; to: string }> = {
  gasto: { label: 'Gasto', to: '/' },
  recaudacion: { label: 'Recaudación', to: '/recaudacion' },
  impuestos: { label: 'Impuestos', to: '/impuestos' },
}

export type Noticia = {
  id: number
  tipo: 'link' | 'propia'
  slug: string | null
  titulo: string
  medio: string | null
  autor: string | null
  fecha: string
  url: string | null
  resumen: string
  cita: string | null
  cuerpo?: string | null
  seccion: Seccion | null
  publicada: boolean
}

/** Send JSON to the API (admin writes); throws the server's message on error. */
export async function sendJson<T>(method: 'POST' | 'PUT' | 'DELETE', url: string, body?: unknown): Promise<T | null> {
  const r = await fetch(url, {
    method, headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = r.status === 204 ? null : await r.json().catch(() => null)
  if (!r.ok) {
    const detail = data?.detail
    const msg = typeof detail === 'string' ? detail
      : Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg?.replace(/^Value error, /, '')).join(' ') : null
    throw new Error(msg || `Error ${r.status}`)
  }
  return data as T | null
}

export type GastoEstado = 'confirmado' | 'estimado' | 'sin_datos' | 'pedido'
export type Moneda = 'UYU' | 'USD'

export type GastoItem = {
  id?: number
  concepto: string
  organismo: string
  inciso: string | null
  tipo_contratacion: string | null
  monto: number | null
  moneda: Moneda
  estado: GastoEstado
  fuente: string | null
  fuente_url: string | null
  nota: string | null
}

export type GastoTotales = { confirmado: Partial<Record<Moneda, number>>; estimado: Partial<Record<Moneda, number>>; pendientes: number }

export type GastoCaso = {
  id: number
  slug: string
  titulo: string
  fecha: string
  resumen: string
  notas: string | null
  publicado: boolean
  totales: GastoTotales
  items?: GastoItem[]
  filtros?: GastoFiltro[]
}

/** On the list, instead of the items: each distinct organismo contratante, unidad ejecutora and procedure type. */
export type GastoFiltro = { inciso: string | null; organismo: string; tipo_contratacion: string | null }

export const ESTADOS: Record<GastoEstado, string> = {
  confirmado: 'Confirmado',
  estimado: 'Estimado por la fuente',
  sin_datos: 'Sin datos',
  pedido: 'Pedido de información en trámite',
}
