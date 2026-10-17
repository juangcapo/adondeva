# Taxes — Uruguay

Tax revenue data. Put each source in its own subfolder, as `inflation/ine-ipc/` does, for example `dgi-recaudacion/` for DGI collections. Keep downloaded files in that subfolder's `raw/`.

`catalog.csv` lists every tax, fee and contribution found so far: national (DGI), customs (DNA), social security (BPS and the independent pension funds), departmental (intendencias) and repealed ones. `verificado = no` marks entries not yet confirmed against an official source.

Each catalog entry has a file in `rates/` (named in the `archivo` column), one row per rate, bracket or fixed amount:

| Column | Meaning |
|---|---|
| `condicion` | who or what the row applies to (sector, product, import, family situation, …) |
| `base` | what the rate is applied to |
| `desde`, `hasta`, `unidad_tramo` | bracket limits when the rate depends on the amount (BPC, UI, UYU, …); empty `hasta` = no upper limit |
| `tasa_pct` | percentage |
| `monto`, `unidad_monto` | fixed amount instead of, or alongside, a percentage |
| `vigencia` | period the value applies to |
| `confianza` | `oficial` (law, decree or agency page), `guia_oficial` (Uruguay XXI investor guide, June 2026), `secundaria` (press or private guide, verify), `sin_datos` |
| `fuente` | URL the value came from |

`rates/` is generated: edit the `RATES` table in `build_rates.py` and run `python3 build_rates.py` (standard library only). Do not edit the CSVs by hand, they are overwritten.
