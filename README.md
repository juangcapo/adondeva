# myrmidon-harvesters

Harvested public-finance data for Uruguay, and `myrmidon.py`, a command line to query it. Standard library only (Python 3).

```
python3 myrmidon.py --help
python3 myrmidon.py COMMAND --help
```

## Data

Each country's data lives under `data/<ISO 3166-1 alpha-2 code>/`. For Uruguay (`data/uy/`):

| Folder | Contents |
|---|---|
| `opp/` | National budget execution: OPP historic series 1961-2010 and detailed credit files 2011 onwards |
| `mef/` | MEF Rendición de Cuentas spending balances |
| `inflation/ine-ipc/` | INE consumer price index, annual |
| `taxes/` | Every Uruguayan tax, fee and contribution with its rates, by level (national, agencies, customs, social security, departmental, repealed). See [its README](data/uy/taxes/README.md) |
| `aranceles/` | Import tariff for every product code, pending tariff changes, and the 2024 vs 2026 postal/courier regime comparison. See [its README](data/uy/aranceles/README.md) |

## Commands

### `sources`

Which years each data source covers.

```
$ python3 myrmidon.py sources
          source  from    to  years
   opp-historico  1961  2010     50
             opp  2011  2024     14
             mef  2025  2025      1
ine-ipc (annual)  1938  2025     88
```

### `inflation`

Yearly CPI inflation (INE, Total País): annual average vs previous average, and December vs December.

```
python3 myrmidon.py inflation --since 2020
python3 myrmidon.py inflation --since 1980 --every 5 --csv
```

### `spending`

National budget spending per year, nominal and in pesos of a base year (deflated by the INE annual average CPI), with the change against the previous row, per year and against the first row. Uses MEF where available, then OPP detail, then the OPP historic series.

```
python3 myrmidon.py spending --since 2020
python3 myrmidon.py spending --since 1980 --every 5 --base 2025 --csv
```

`--include-fondos-terceros` keeps MEF's "Fondos de Terceros Declarados por Ley", which OPP years leave out (so years stop being comparable).

`inflation` and `spending` take `--since`, `--until`, `--every N` (only years divisible by N) and `--csv`.

### `tax`

Tax breakdown for an action and an amount, with 2026 rates read from `data/uy/taxes/`. Prints who pays each item, its base, rate and amount, then totals. `--csv` prints CSV.

```
python3 myrmidon.py tax ACCION MONTO [options]
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
$ python3 myrmidon.py tax sueldo 80000 --hijos 1
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

python3 myrmidon.py tax compra 1500
python3 myrmidon.py tax compra 1000 --tasa minima --neto
python3 myrmidon.py tax importar 1200 --ncm 8471.30.12.00 --contribuyente
python3 myrmidon.py tax importar 300 --envio
python3 myrmidon.py tax alquiler 30000
```

BPC, UR and UI values come from `data/uy/taxes/valores_referencia.csv`; update it when BPS publishes new values.

Not covered:

- `sueldo` assumes a private-sector employee (Industria y Comercio); no Fondo de Solidaridad or non-BPS funds (Caja Bancaria, Profesional, Notarial, military and police).
- `importar` leaves out IMESI, customs broker fees and the non-intrusive inspection fee (up to 85 UI). The consular fee rate comes from a secondary source.
- `alquiler` taxes the gross rent, without deductible expenses.

## Adding a command

Write a function that takes `args` and decorate it with `@command("help text", arg(...), ...)` in `myrmidon.py`. The function name becomes the command name (underscores turn into dashes).
