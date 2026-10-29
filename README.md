# ¿A dónde va?

**adondeva** follows public money: where the state's money comes from and where it goes. It collects official records and turns them into data you can analyze.

The first target is **Uruguay's public finances**: how much the national budget allocated and actually spent, by agency, program and year, and how that compares once inflation is taken out, and what each tax has collected every year since 1982. The repo also covers **Uruguay's taxes and import tariffs**: every tax, fee and contribution with its rates, and the tariff for every product code.

## Purpose

Governments publish their money numbers, but across many portals, formats and conventions, each with its own quirks. Some are CSVs, some spreadsheets, some PDFs. Some files are only partial, and some sites have broken certificates. This repo gathers the official files in one place, records where each one came from and what is wrong with it, and gives one command-line tool to query them.

## What's inside

Each country's data lives under `data/<ISO 3166-1 alpha-2 code>/`. For Uruguay:

```
adondeva/
├── adondeva.py                          command-line tool (see "How to use")
└── data/uy/
    ├── opp/
    │   ├── credito-presupuestal/        OPP budget detail, 2011–2024
    │   └── historico/                   OPP executed budget by agency, 1961–2010
    ├── mef/rendicion-cuentas/2025/      MEF Rendición de Cuentas 2025 open data
    ├── dgi/recaudacion/                 DGI tax revenue by tax, 1982–2025
    ├── inflation/ine-ipc/               INE consumer price index (IPC), 1937–today
    ├── taxes/                           every tax, fee and contribution, with rates
    └── aranceles/                       import tariffs and the postal/courier regime
```

### `data/uy/opp/credito-presupuestal/` — national budget, 2011–2024

Source: [Portal de Transparencia Presupuestaria (OPP)](https://transparenciapresupuestaria.opp.gub.uy/inicio/datos-abiertos). OPP has since retired the portal (as of October 2026 its file URLs return 404), so these files are kept as downloaded and won't be refreshed.

- One CSV per year: `credito_presupuestal_detalle_{year}.csv`. Each row is one combination of agency (*inciso*), executing unit, program, project, funding source and spending item.
- Amounts: `apertura` (initial budget), `credito` (final budget), `ejecutado` (spent).
- UTF-8, comma-separated, fully quoted. Amounts use a decimal comma (`"37997270,00"`).
- `Metadatos_CreditoPresupuestalDesde2011.csv` describes every column.
- OPP also publishes a 2025 file, but it only runs to mid-2025, so it is not included. Use MEF for 2025.

### `data/uy/opp/historico/` — executed budget by agency, 1961–2010

- One row per agency, one column per year, in thousands of current pesos (semicolon-separated).
- Values from before the 1975 and 1993 currency changes are already converted to current pesos (see the methodology PDF).
- Less detail than 2011 onward: there is no program or spending-item breakdown.
- Until 1984, debt repayments were counted under agency 20. From 1985 they are excluded, so 1980–1984 read slightly high.

### `data/uy/mef/rendicion-cuentas/2025/` — full-year 2025

Source: [MEF – Rendición de Cuentas 2025, Datos Abiertos](https://www.gub.uy/ministerio-economia-finanzas/comunicacion/publicaciones/rendicion-cuentas-balance-ejecucion-presupuestal-ejercicio-2025-datos), published 30 June 2026.

- `bal_gastos.ods` is the main file: 2025 budget (`CREDITO`) and spending (`OBLIGADO`) at the same level of detail as OPP, plus the 2024 figures (`*_ANTERIOR`).
- `Metadata RC2025.ods` describes every column. The other files cover revenue, science, donations, civil-service headcount and the Tomo I tables.
- MEF only publishes open data for 2025. Earlier years are PDFs only, so 2011–2024 come from OPP.
- MEF counts one funding source that OPP leaves out, **"Fondos de Terceros Declarados por Ley"** (9.7 bn in 2025, about 1% of spending). Drop it when comparing with OPP years.

### `data/uy/dgi/recaudacion/` — tax revenue by tax, 1982–2025

Source: [DGI – Recaudación anual y mensual por impuesto](https://www.gub.uy/direccion-general-impositiva/datos-y-estadisticas/estadisticas/recaudacion-anual-mensual-impuesto).

- `recaudacion_anual.csv`: pesos corrientes collected per year and tax (`anio, sigla, monto`), plus DGI's `TOTAL` and an `AJUSTES` row so the taxes add up to it.
- `impuestos.csv`: each tax's name, group (`renta`, `consumo`, `propiedad`, `otros`, following MEF's revenue classification), first year and last year with collections.
- Before 1990 DGI details only 5 or 6 taxes, so 9–16% of those years is unassigned (`AJUSTES`).
- Only taxes DGI collects: no BPS contributions, import duties or departmental taxes. `build_recaudacion.py` rebuilds both CSVs from `raw/`. See the folder's [README](data/uy/dgi/recaudacion/README.md).

### `data/uy/inflation/ine-ipc/` — consumer price index

Source: [INE – IPC base Octubre 2022=100](https://www.gub.uy/instituto-nacional-estadistica/datos-y-estadisticas/estadisticas/series-historicas-ipc-base-octubre-2022100).

- `ipc_mensual.csv`: monthly index from July 1937.
- `ipc_anual.csv`: complete years only, with the average index, the December index and inflation measured both ways (average vs average, December vs December).
- `build_ipc.py` rebuilds both CSVs from the workbooks in `raw/`. See that folder's [README](data/uy/inflation/ine-ipc/README.md).

### `data/uy/taxes/` — taxes, fees and contributions

Every Uruguayan tax, fee and contribution with its rates, by level: national, agencies, customs, social security, departmental and repealed. See [its README](data/uy/taxes/README.md).

### `data/uy/aranceles/` — import tariffs

Import tariff for every product code, pending tariff changes, and the 2024 vs 2026 postal/courier regime comparison. See [its README](data/uy/aranceles/README.md).

### Coverage

The budget data has the following limits:

- It covers the **national budget** only: the 34 agencies of the Presupuesto Nacional.
- It does **not** include state companies (UTE, ANCAP, OSE), departmental governments, or the BPS's own accounts. The BPS appears only through the transfers it receives.
- "Spent" means committed spending (`ejecutado` in OPP, `OBLIGADO` in MEF), not cash paid out.

## How to use

You only need Python 3. No packages to install.

```bash
git clone https://github.com/juangcapo/adondeva.git
cd adondeva
python3 adondeva.py --help
python3 adondeva.py COMMAND --help
```

### Commands

| Command | What it does |
|---|---|
| `sources` | Which years each data source covers |
| `spending` | Total national budget spending per year, nominal and adjusted for inflation |
| `revenue` | DGI tax revenue per year: total and share by group of taxes, or one tax with `--tax` |
| `breakdown` | Drill into one year's spending, one level per argument: area, agency, program, item… |
| `tax` | Tax breakdown for an action (salary, purchase, import, rent) and an amount |

`spending` and `revenue` take:

| Option | Meaning |
|---|---|
| `--since YEAR` / `--until YEAR` | Limit the range of years |
| `--every N` | Only years divisible by N (e.g. `--every 5`) |
| `--csv` | Print CSV instead of a table |
| `--base YEAR` | Show real values in pesos of this year (default: latest year) |
| `--include-fondos-terceros` | `spending` only: keep MEF's "Fondos de Terceros" (makes 2025 not comparable with earlier years) |
| `--tax SIGLA` | `revenue` only: one tax (`IVA`, `IRPF-II`, `IRAE`…; see `data/uy/dgi/recaudacion/impuestos.csv`) |

### `sources`

```
$ python3 adondeva.py sources
          source  from    to  years
   opp-historico  1961  2010     50
             opp  2011  2024     14
             mef  2025  2025      1
ine-ipc (annual)  1938  2025     88
   dgi (revenue)  1982  2025     44
```

### `spending`

```bash
# Spending every five years since 1980, in 2025 pesos
python3 adondeva.py spending --since 1980 --every 5

# Spending since 2019 in 2020 pesos, saved as CSV
python3 adondeva.py spending --since 2019 --base 2020 --csv > spending.csv
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

### `revenue`

```bash
# DGI revenue every five years since 1990, in 2025 pesos, with the share of each group
python3 adondeva.py revenue --since 1990 --every 5

# IVA since 2015
python3 adondeva.py revenue --tax IVA --since 2015
```

```
year  nominal_bn  real_2025_bn  renta  consumo  propiedad  otros
1990       1.427         203.3   8.2%    78.7%       9.5%   3.6%
...
2025     699.960         700.0  35.7%    58.1%       6.0%   0.2%
```

### Caching

The first run takes about 15–20 seconds while it reads the large files. Results are cached in `.cache/` (not tracked by git) and refresh automatically when a file changes.

### `breakdown`

Splits one year's spending (2011–2025) and goes one level deeper with each argument. With no arguments it lists the areas and suggests what to type next.

```
python3 adondeva.py breakdown [--year YEAR] [SELECTION ...]
```

The levels, in order:

```
area › agency › executing unit › program › project › group › subgroup › item › funding source
```

Each selection is either a **rank** from the previous listing (`1` is the largest) or **part of a name**, ignoring case and accents (`salud`, `"servicios publicos"`). If a name matches several values, it lists them. Each listing shows spending, share, final budget and the percentage of the budget spent, and ends with suggested next commands.

```bash
# Areas of the latest year
python3 adondeva.py breakdown

# Agencies inside General Public Services, 2024
python3 adondeva.py breakdown --year 2024 "servicios publicos"

# Pay items of DGI's staff in 2024
python3 adondeva.py breakdown --year 2024 "servicios publicos" economia impositiva 1 1 "servicios personales" 1
```

```
# 2024 (opp) · spent and final budget, millions of current pesos
# all spending › SERVICIOS PÚBLICOS GENERALES › Diversos Créditos
# by executing unit (level 3 of 9)
#  executing unit                           spent  share     budget  executed
1  Dir. Gral. de Secretaría (M.E.F.)    109,246.2  98.0%  111,992.0       98%
2  Presidencia de la República            1,544.1   1.4%    1,572.4       98%
3  Ministerio de Relaciones Exteriores      664.3   0.6%      711.0       93%
   total                                111,454.7   100%  114,275.4       98%
```

Amounts are in current pesos of that year. 2025 comes from MEF and excludes "Fondos de Terceros" unless you pass `--include-fondos-terceros`, as `spending` does. `--csv` prints full amounts in pesos. The first 2025 run takes about 15 seconds; after that it is cached.

### `tax`

Tax breakdown for an action and an amount, with 2026 rates read from `data/uy/taxes/`. Prints who pays each item, its base, rate and amount, then totals. `--csv` prints CSV.

```
python3 adondeva.py tax ACCION MONTO [options]
```

| Action | Amount | Options | What it computes |
|---|---|---|---|
| `sueldo` | monthly nominal salary, UYU | `--hijos N`, `--conyuge` | Employee: pension contribution 15% (up to tope C), FONASA by salary and family, FRL, IRPF withholding by brackets (6% added above 10 BPC; deductions credited at 14% or 8%, children included). Employer: pension 7.5%, FONASA 5%, FRL, FGCL. Totals: net salary, total cost to the employer, share of taxes |
| `compra` | price, UYU | `--tasa basica\|minima\|debito\|exento`, `--neto` | IVA included in the price, or added to it with `--neto` |
| `importar` | CIF value, USD | `--ncm CODE` or `--arancel PCT`, `--mercosur`, `--contribuyente`, `--tasa minima` | General regime: tariff for the product code (from `aranceles/arancel.csv`), consular fee, preferential services fee (max USD 50), IVA on CIF plus tariff, IRAE advance with `--contribuyente` |
| `importar --envio` | value, USD | `--eeuu`, `--cupo USD` | Postal/courier regime 2026: each option (franchise with IVA 22%, or flat 60%) and the cheapest one |
| `alquiler` | monthly rent, UYU | | IRPF on rents (12% of gross), exempt up to 40 BPC a year |

Examples:

```
$ python3 adondeva.py tax sueldo 80000 --hijos 1
      paga                                                        concepto       base    tasa      monto
trabajador                          aporte jubilatorio personal (BPS/AFAP)  80,000.00     15%  12,000.00
trabajador                        FONASA personal (sin cónyuge, con hijos)  80,000.00      6%   4,800.00
trabajador                                   Fondo de Reconversión Laboral  80,000.00    0.1%      80.00
trabajador  IRPF (franjas sobre $84,800, menos 14% de deducciones $28,320)  84,800.00             518.40
   empresa                                     aporte jubilatorio patronal  80,000.00    7.5%   6,000.00
   empresa                                                 FONASA patronal  80,000.00      5%   4,000.00
   empresa                          Fondo de Reconversión Laboral patronal  80,000.00    0.1%      80.00
   empresa                         Fondo de Garantía de Créditos Laborales  80,000.00  0.025%      20.00
                                                            sueldo líquido                     62,601.60
                                               costo total para la empresa                     90,100.00
                                               impuestos y aportes totales                     27,498.40
                                                         % del costo total                         30.52

python3 adondeva.py tax compra 1500
python3 adondeva.py tax compra 1000 --tasa minima --neto
python3 adondeva.py tax importar 1200 --ncm 8471.30.12.00 --contribuyente
python3 adondeva.py tax importar 300 --envio
python3 adondeva.py tax alquiler 30000
```

BPC, UR and UI values come from `data/uy/taxes/valores_referencia.csv`; update it when BPS publishes new values.

Not covered:

- `sueldo` assumes a private-sector employee (Industria y Comercio); no Fondo de Solidaridad or non-BPS funds (Caja Bancaria, Profesional, Notarial, military and police).
- `importar` leaves out IMESI, customs broker fees and the non-intrusive inspection fee (up to 85 UI). The consular fee rate comes from a secondary source.
- `alquiler` taxes the gross rent, without deductible expenses.

### Website

`web/` has a website (FastAPI + React, in Spanish) over the same data: spending charts and drill-down, tax revenue history, the tax calculator and sources. See [web/README.md](web/README.md) for how to run it.

### Adding a command

Write a function in `adondeva.py` and register it with `@command`:

```python
@command("what it does", arg("--inciso", type=int, help="agency code"))
def by_agency(args):
    ...
```

The function name becomes the command name (`by-agency`, underscores turn into dashes) and appears in `--help` automatically.

## Keeping the data up to date

`update.py` checks the official sources, downloads any file that changed and rebuilds the derived CSVs:

```bash
python3 update.py              # every source
python3 update.py --dry-run    # only report what changed
python3 update.py dgi          # one source: dgi, ine or mef
```

| Source | What it checks |
|---|---|
| `dgi` | The annual revenue series by tax; rebuilds `data/uy/dgi/recaudacion/` |
| `ine` | The CPI workbooks; rebuilds `data/uy/inflation/ine-ipc/` |
| `mef` | The Rendición de Cuentas files of the years we have, and next year's once MEF publishes them (usually by 30 June) |

gub.uy file URLs change with each upload, so each file is found by its link on the source's page. A file counts as changed when its bytes differ from the local copy. OPP files, the 1961–2010 history and the compiled tax and tariff datasets are not checked.

A GitHub Actions workflow (`.github/workflows/update-data.yml`) runs it every Monday. If anything changed, it runs the tests and opens or refreshes a pull request from the `data-update` branch, listing each changed file, its `Last-Modified` date and the coverage before and after. If a source can't be read or a build script fails (usually a page or file layout changed), the run fails and GitHub emails you. Enable *Settings → Actions → General → Allow GitHub Actions to create and approve pull requests* for it to open PRs.

## Notes for harvesting

- **Some sites have incomplete certificate setups.** `www5.ine.gub.uy` and `www.bcu.gub.uy` don't send their intermediate certificate, so `curl` refuses to connect. Fetch the missing certificate from the address in the server certificate's AIA field, and pass it with `--cacert`. Never turn off verification.
- **Files get replaced without notice.** OPP's 2021 file was replaced more than a year after it first appeared. Check `Last-Modified` and keep each version.
- **The national data catalog is behind.** [catalogodatos.gub.uy](https://catalogodatos.gub.uy) only lists OPP files up to 2021. The newer years were only on the OPP site, which is now gone.

## License

- **Code** (`adondeva.py`, the `build_*.py` scripts and the website in `web/`): [MIT](LICENSE).
- **Datasets compiled for this repo** (`data/uy/taxes/` and `data/uy/aranceles/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Reuse them freely, crediting this repo.
- **Official files** published by OPP, MEF and INE: the [Licencia de Datos Abiertos – Uruguay](https://www.gub.uy/agencia-gobierno-electronico-sociedad-informacion-conocimiento/sites/agencia-gobierno-electronico-sociedad-informacion-conocimiento/files/documentos/publicaciones/licencia_de_datos_abiertos_0.pdf). It requires you to credit the publishing agency (OPP, MEF, INE) and the dataset used.
