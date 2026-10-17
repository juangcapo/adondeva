# Aranceles de importación — Uruguay

Source: [MEF – Nomenclatura y Aranceles Uruguay](https://www.gub.uy/ministerio-economia-finanzas/nomenclatura-aranceles-uruguay-0). National nomenclature at 10 digits (NCM + national opening, SA 2022) with its tariff regime. The MEF says the spreadsheets are informative only and do not replace the norms.

| File | Contents |
|---|---|
| `raw/` | MEF workbooks: national tariff February 2025 (complete with notes, and simplified at 10 digits) and the 2026 exceptions list |
| `raw/normas/` | Norms published after the February 2025 base, antidumping resolutions and the IRAE import advance decree |
| `cambios.csv` | Changes after the base, transcribed by hand from the annexes of MEF resolutions 1434/025, 2322/026 and 4417/026 (the last one carries Decreto 36/026 to 10 digits). `alta` adds or replaces a code, `baja` removes it |
| `arancel.csv` | One row per 10-digit code in force: `ncm`, `ncm8`, `capitulo`, `descripcion`, `aec_pct` (Mercosur common external tariff), `lista_especial` (BK capital goods, BIT IT/telecom), `tga_extrazona_pct` (tariff Uruguay applies outside Mercosur), `tga_intrazona_pct` (inside Mercosur), `uvf` (DNA physical unit code, as given), `norma` (base or the resolution that last changed the code), `lne` (in the national exceptions list), `anticipo_irae_pct` (4% IRAE advance on customs value plus tariff), `antidumping` (an antidumping duty in force) |
| `lne.csv` | National list of exceptions to the AEC (2026), notes resolved |
| `antidumping.csv` | Antidumping duties by code, origin and exporter, with their term |
| `normas.csv` | Norms after the base and how each is reflected |
| `build_arancel.py` | Rebuilds `arancel.csv`, `lne.csv` and `normas.csv` from `raw/` and `cambios.csv` (standard library plus `pdftotext`) |
| `regimen-envios/` | Comparison of the 2024 and 2026 regimes for online purchases by post or courier (franchise and 60% single tax) |

Notes:

- Code 3207.10.90.00 appears twice in the MEF workbook with different extra-zone tariffs (10,8% and 0%); both rows are kept.
- Resolution 1434/025 reopens 8539.52.00 without code 8539.52.00.10; `cambios.csv` removes it although the resolution does not list it explicitly.
- The IRAE advance annex (December 2025) lists 6506.10.00.00, which Resolution 4417/026 later split into 6506.10.10.00 and 6506.10.90.00; neither new code is flagged.

Other import charges (IVA, IMESI, consular fee, customs fees) are in `../taxes/`.
