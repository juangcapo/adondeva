# Recaudación de la DGI por impuesto — 1982–2025

Source: [DGI – Recaudación anual y mensual por impuesto](https://www.gub.uy/direccion-general-impositiva/datos-y-estadisticas/estadisticas/recaudacion-anual-mensual-impuesto), file "Recaudación por impuesto - Series anuales" (CSV and XLSX, `Last-Modified` 11 Feb 2026).

| File | Contents |
|---|---|
| `raw/` | CSV and XLSX as downloaded from DGI (the CSV is Latin-1, semicolon-separated) |
| `recaudacion_anual.csv` | `anio, sigla, monto`: pesos corrientes collected per tax and year; only nonzero amounts |
| `impuestos.csv` | `sigla, nombre, grupo, desde, hasta, nota`: one row per tax |
| `build_recaudacion.py` | Rebuilds both CSVs from `raw/` (standard library only) |

- Amounts are in pesos corrientes of each year. Values from before the 1993 currency change already come converted to pesos uruguayos.
- Cash basis: a repealed tax can keep collecting for years (IRIC was repealed in 2007 and shows amounts until 2019). `hasta` is the last year with collections.
- `grupo` follows the sections of MEF's revenue classification in `bal_recursos.ods`: `renta` (income and profits), `consumo` (goods and services), `propiedad` (property), `otros`. IMEBA goes under `consumo` and the Impuesto de Primaria under `propiedad`, as MEF does. ICOSIFI, which MEF no longer lists, is under `otros`.
- `sigla` `AJUSTES` is DGI's total minus the sum of the taxes it lists. `TOTAL` is DGI's own total, so the parts always add up to it.
- **Before 1990 the detail is thin.** DGI lists only 5 or 6 taxes for 1982–1989 (IVA, IMESI, IRIC, ISAFI, IMAGRO, IRA), so `AJUSTES` is 9–16% of those years' total. From 1990 it is 0.2–3.6%, and under 1.5% from 1994 (under 0.3% from 2008).
- DGI notes that from 2008 the IVA column includes "IVA mínimo" of small businesses, while the IVA mínimo column keeps its own series; the parts still match the total within the `AJUSTES` margin.
- Only taxes DGI collects. Not included: social-security contributions (BPS), import duties (Aduanas), and departmental taxes.
