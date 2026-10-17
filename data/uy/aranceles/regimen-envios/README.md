# Compras en el exterior por envío postal o courier — régimen 2024 vs 2026

How a person importing a small online purchase is taxed, before and after the 2026 change (the "impuesto Temu").

| | 2024 | 2026 |
|---|---|---|
| Norm | Decreto 356/014, amended by Decretos 336/015 and 453/016 | Ley 20.446 arts. 627–635 and Decreto 50/026 |
| In force | until 22/3/2026 (simplified regime) and 30/4/2026 (franchise) | from 23/3/2026 (simplified regime) and 1/5/2026 (franchise) |

| File | Contents |
|---|---|
| `raw/` | Decreto 50/026 (PDF) and the official Aduanas texts of Decreto 356/014 and of the regime notices |
| `comparacion.csv` | Rule by rule: `concepto`, `regimen_2024`, `regimen_2026` and the article each comes from |
| `escenarios.csv` | One purchase by `canal` (courier or ordinary post), `origen` (US or other) and `valor_usd`: cheapest legal option and tax in each regime, the difference and the total cost |
| `perfiles.csv` | Total tax over a year for a few typical buyers |
| `build_comparacion.py` | Rebuilds the three CSVs; the rules are in the script |

Assumptions in the scenarios:

- The cheapest legal option is chosen; the franchise is assumed unused at the start of the year.
- 2026 franchise: 22% VAT on the invoice value with a minimum of USD 20 per shipment. The minimum comes from the Uruguay XXI guide (citing Ley 20.446); Decreto 50/026 does not state it.
- US purchases are VAT-exempt only up to USD 200 per shipment and, from 3/11/2026, only if the seller is registered with Aduanas.
- Blank tax means the shipment falls into the general import regime (tariff, VAT, IMESI and fees with a customs broker), which these files do not calculate.
- Goods subject to IMESI (alcohol, tobacco, perfumes, etc.) are outside both regimes.
