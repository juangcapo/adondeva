const LOCALE = 'es-UY'

const number = (digits: number) =>
  new Intl.NumberFormat(LOCALE, { minimumFractionDigits: digits, maximumFractionDigits: digits })

export const fmt = (x: number, digits = 0) => number(digits).format(x)

export const pct = (x: number | null | undefined, digits = 1) => (x == null ? '—' : `${fmt(x, digits)}%`)

/** A tax rate with only the decimals it needs: 15%, 0,1%, 0,025%. */
export const rate = (x: number) =>
  `${new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 3 }).format(x)}%`

export const signedPct = (x: number | null | undefined) =>
  x == null ? '—' : `${x > 0 ? '+' : ''}${fmt(x, 1)}%`

/** Pesos in the largest unit that keeps the number readable: "998,3 mil millones", "1.544 millones". */
export function pesos(x: number) {
  const abs = Math.abs(x)
  if (abs >= 1e9) return `$ ${fmt(x / 1e9, 1)} mil millones`
  if (abs >= 1e6) return `$ ${fmt(x / 1e6, 1)} millones`
  return `$ ${fmt(x)}`
}

/** Short form for chart axes. */
export const axisBillions = (x: number) => `${fmt(x / 1e9)}`
