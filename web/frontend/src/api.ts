import { useEffect, useState } from 'react'

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
    throw new Error(typeof detail === 'string' ? detail : `Error ${r.status}`)
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

  return { data, error, loading }
}
