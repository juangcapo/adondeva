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
| `departamental/raw/presupuestos_2026/` | Text of the 2026-2030 departmental budgets published in the Diario Oficial, the source of the departmental rows |

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

The rate files are generated: edit `RATES` in `build_rates.py` (national and other levels) or `departamental_data.py` (departments) and run `python3 build_rates.py`. Do not edit the CSVs by hand, they are overwritten.

Departmental coverage: full or main taxes for Rocha, Río Negro, Artigas and Paysandú; partial for Montevideo, Durazno, Cerro Largo and Florida (their 2026 budgets only change some articles of older norms); third-party ranges for Canelones, Colonia and Maldonado. Salto, San José, Soriano, Treinta y Tres, Lavalleja, Flores, Rivera and Tacuarembó did not publish their tax texts in the 2026 Diario Oficial and are still missing.
