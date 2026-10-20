# Impuestos, tasas y contribuciones — Uruguay

`catalog.csv` lists every tax, fee and contribution found: national (DGI), regulators and agencies, customs, social security, departmental (intendencias) and repealed ones. `verificado = no` marks entries not yet confirmed against an official source. Tariffs by product code are in `../aranceles/`.

Each catalog entry has one rate file (named in the `archivo` column), in a folder by level:

| Folder | Contents |
|---|---|
| `nacional/` | DGI taxes (IVA, IRPF, IRAE, IMESI, Patrimonio, IMEBA, Primaria, IMCD, etc.) |
| `organismos/` | Fees of regulators and agencies: URSEC, URSEA, BCU, INAC, airports, registries |
| `aduana/` | Import and export charges collected by customs, other than the tariff itself |
| `seguridad_social/` | BPS contributions, sector funds and the independent pension funds |
| `departamental/` | Intendencia taxes and fees, with one row per department and rate |
| `derogados/` | Repealed taxes with their historical rates |
| `departamental/raw/` | Source texts of the departmental rows: 2026-2030 budgets and older budgets, decrees and texts ordenados |

Rate file columns, one row per rate, bracket or fixed amount:

| Column | Meaning |
|---|---|
| `departamento` | department for departmental rows, empty otherwise |
| `condicion` | who or what the row applies to (sector, product, zone, family situation, …) |
| `base` | what the rate is applied to |
| `desde`, `hasta`, `unidad_tramo` | bracket limits when the rate depends on the amount (BPC, UI, UYU, ha, …); empty `hasta` = no upper limit |
| `tasa_pct` | percentage |
| `monto`, `unidad_monto` | fixed amount instead of, or alongside, a percentage |
| `vigencia` | period the value applies to |
| `confianza` | `oficial` (law, decree, Diario Oficial or agency page), `guia_oficial` (Uruguay XXI investor guide, June 2026), `secundaria` (press, private guide or academic history, verify), `sin_datos` |
| `fuente` | URL the value came from |

`valores_referencia.csv` holds the current BPC, UR, UI and minimum wage, used to turn BPC brackets into pesos. `python3 myrmidon.py tax ACCION MONTO` (sueldo, compra, importar, alquiler) computes a breakdown from these files.

The rate files are generated: edit `RATES` in `build_rates.py` (national and other levels) or `departamental_data.py` (departments) and run `python3 build_rates.py`. Do not edit the CSVs by hand, they are overwritten.

Departmental coverage. Sources are the Diario Oficial texts of each department's budgets (2001 to 2026, saved in `departamental/raw/`) and, for Maldonado, its online Texto Ordenado de Tributos (TOTIDEM). Many departments set rates in decades-old ordinances and their budgets only change some articles, so a row's `vigencia` says since when it applies and amounts in "UYU de 20xx" are nominal values of that year that the department adjusts by IPC or UR.

| Department | Coverage |
|---|---|
| Montevideo, Rocha, Río Negro, Artigas, Paysandú, Colonia, Durazno, Rivera, Maldonado, Salto, Soriano | property tax rates or scale plus most other tributes |
| Tacuarembó, Canelones, Treinta y Tres, Lavalleja, Cerro Largo, Florida, Flores | some tributes; the general property tax scale is not in any published text found (Canelones has only a third-party range) |
| San José | no rates found: its budgets in the Diario Oficial (2006, 2011, 2016, 2021, 2026) only list revenue amounts |

`departamental/raw/presupuestos_2026/` has the 2026-2030 budget texts; `departamental/raw/normas/` has the tax articles extracted from older budgets and decrees, one file per source with its URL on the first line.
