# myrmidon-harvesters

Agents that harvest public state records and turn them into data you can analyze.

The first target is **Uruguay's public finances**: how much the national budget allocated and actually spent, by agency, program and year, and how that compares once inflation is taken out.

## Purpose

Governments publish their money numbers, but across many portals, formats and conventions, each with its own quirks. Some are CSVs, some spreadsheets, some PDFs. Some files are only partial, and some sites have broken certificates. This repo gathers the official files in one place, records where each one came from and what is wrong with it, and gives one command-line tool to query them.

The name comes from the Myrmidons of Greek myth: an army of ants turned into soldiers. Here the soldiers are many small workers, each going out to one source and bringing its records back.

## What's inside

```
myrmidon-harvesters/
├── myrmidon.py                     command-line tool (see "How to use")
├── opp/
│   ├── credito-presupuestal/       OPP budget detail, 2011–2024
│   └── historico/                  OPP executed budget by agency, 1961–2010
├── mef/rendicion-cuentas/2025/     MEF Rendición de Cuentas 2025 open data
└── inflation/ine-ipc/              INE consumer price index (IPC), 1937–today
```

### `opp/credito-presupuestal/` — national budget, 2011–2024

Source: [Portal de Transparencia Presupuestaria (OPP)](https://transparenciapresupuestaria.opp.gub.uy/inicio/datos-abiertos).

- One CSV per year: `credito_presupuestal_detalle_{year}.csv`. Each row is one combination of agency (*inciso*), executing unit, program, project, funding source and spending item.
- Amounts: `apertura` (initial budget), `credito` (final budget), `ejecutado` (spent).
- UTF-8, comma-separated, fully quoted. Amounts use a decimal comma (`"37997270,00"`).
- `Metadatos_CreditoPresupuestalDesde2011.csv` describes every column.
- OPP also publishes a 2025 file, but it only runs to mid-2025, so it is not included. Use MEF for 2025.

### `opp/historico/` — executed budget by agency, 1961–2010

- One row per agency, one column per year, in thousands of current pesos (semicolon-separated).
- Values from before the 1975 and 1993 currency changes are already converted to current pesos (see the methodology PDF).
- Less detail than 2011 onward: there is no program or spending-item breakdown.
- Until 1984, debt repayments were counted under agency 20. From 1985 they are excluded, so 1980–1984 read slightly high.

### `mef/rendicion-cuentas/2025/` — full-year 2025

Source: [MEF – Rendición de Cuentas 2025, Datos Abiertos](https://www.gub.uy/ministerio-economia-finanzas/comunicacion/publicaciones/rendicion-cuentas-balance-ejecucion-presupuestal-ejercicio-2025-datos), published 30 June 2026.

- `bal_gastos.ods` is the main file: 2025 budget (`CREDITO`) and spending (`OBLIGADO`) at the same level of detail as OPP, plus the 2024 figures (`*_ANTERIOR`).
- `Metadata RC2025.ods` describes every column. The other files cover revenue, science, donations, civil-service headcount and the Tomo I tables.
- MEF only publishes open data for 2025. Earlier years are PDFs only, so 2011–2024 come from OPP.
- MEF counts one funding source that OPP leaves out, **"Fondos de Terceros Declarados por Ley"** (9.7 bn in 2025, about 1% of spending). Drop it when comparing with OPP years.

### `inflation/ine-ipc/` — consumer price index

Source: [INE – IPC base Octubre 2022=100](https://www.gub.uy/instituto-nacional-estadistica/datos-y-estadisticas/estadisticas/series-historicas-ipc-base-octubre-2022100).

- `ipc_mensual.csv`: monthly index from July 1937.
- `ipc_anual.csv`: complete years only, with the average index, the December index and inflation measured both ways (average vs average, December vs December).
- `build_ipc.py` rebuilds both CSVs from the workbooks in `raw/`. See that folder's [README](inflation/ine-ipc/README.md).

### Coverage

The data has the following limits:

- It covers the **national budget** only: the 34 agencies of the Presupuesto Nacional.
- It does **not** include state companies (UTE, ANCAP, OSE), departmental governments, or the BPS's own accounts. The BPS appears only through the transfers it receives.
- "Spent" means committed spending (`ejecutado` in OPP, `OBLIGADO` in MEF), not cash paid out.

## How to use

You only need Python 3. No packages to install.

```bash
git clone https://github.com/juangcapo/myrmidon-harvesters.git
cd myrmidon-harvesters
python3 myrmidon.py --help
```

### Commands

| Command | What it does |
|---|---|
| `sources` | Which years each data source covers |
| `inflation` | Yearly inflation from the INE index |
| `spending` | Total national budget spending per year, nominal and adjusted for inflation |

`inflation` and `spending` both take:

| Option | Meaning |
|---|---|
| `--since YEAR` / `--until YEAR` | Limit the range of years |
| `--every N` | Only years divisible by N (e.g. `--every 5`) |
| `--csv` | Print CSV instead of a table |

`spending` also takes:

| Option | Meaning |
|---|---|
| `--base YEAR` | Show real values in pesos of this year (default: latest year) |
| `--include-fondos-terceros` | Keep MEF's "Fondos de Terceros" (makes 2025 not comparable with earlier years) |

### Examples

```bash
# Inflation every five years since 1980
python3 myrmidon.py inflation --since 1980 --every 5

# Spending every five years since 1980, in 2025 pesos
python3 myrmidon.py spending --since 1980 --every 5

# Spending since 2019 in 2020 pesos, saved as CSV
python3 myrmidon.py spending --since 2019 --base 2020 --csv > spending.csv
```

Sample output:

```
year         source  nominal_bn  real_2025_bn  vs_prev_row  per_year  vs_first
1980  opp-historico       0.016         254.6                            +0.0%
...
2020            opp     631.493         862.4       +13.4%     +2.6%   +238.7%
2025            mef     998.253         998.3       +15.8%     +3.0%   +292.1%
```

For each year, `spending` picks the best source available: **MEF** first, then **OPP detail** (2011–2024), then **OPP historic** (1961–2010). Real values use the yearly average CPI:

```
real = nominal × IPC[base year] / IPC[year]
```

The first run takes about 15–20 seconds while it reads the large files. Results are cached in `.cache/` (not tracked by git) and refresh automatically when a file changes.

### Adding a command

Write a function in `myrmidon.py` and register it with `@command`:

```python
@command("what it does", arg("--inciso", type=int, help="agency code"))
def by_agency(args):
    ...
```

The function name becomes the command name (`by-agency`) and appears in `--help` automatically.

## Notes for harvesting

- **Some sites have incomplete certificate setups.** `www5.ine.gub.uy` and `www.bcu.gub.uy` don't send their intermediate certificate, so `curl` refuses to connect. Fetch the missing certificate from the address in the server certificate's AIA field, and pass it with `--cacert`. Never turn off verification.
- **Files get replaced without notice.** OPP's 2021 file was replaced more than a year after it first appeared. Check `Last-Modified` and keep each version.
- **The national data catalog is behind.** [catalogodatos.gub.uy](https://catalogodatos.gub.uy) only lists OPP files up to 2021. The newer years exist only on the OPP site.

## License of the data

The data is published under the [Licencia de Datos Abiertos – Uruguay](https://www.gub.uy/agencia-gobierno-electronico-sociedad-informacion-conocimiento/sites/agencia-gobierno-electronico-sociedad-informacion-conocimiento/files/documentos/publicaciones/licencia_de_datos_abiertos_0.pdf). It requires you to credit the publishing agency (OPP, MEF, INE) and the dataset used.
