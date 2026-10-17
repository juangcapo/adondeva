"""Build clean tariff tables from the MEF national tariff workbooks.

Reads raw/arancel_nacional_2025-02_10digitos.xlsx (simplified national tariff, 10 digits),
raw/lne_2026.xlsx (national list of exceptions to the AEC) and
raw/normas/anticipo_irae_importacion_anexo.pdf (codes subject to the 4% IRAE advance, via pdftotext)
applies the later changes transcribed in cambios.csv (by hand, from scanned MEF resolutions), and writes:
  arancel.csv  one row per 10-digit code in force, with AEC, applied extra/intra-zone tariff and flags
  lne.csv      the exception list with its notes resolved
  normas.csv   tariff norms after the February 2025 base, with whether arancel.csv reflects them

Standard library only (plus the pdftotext command for the IRAE annex). Run: python3 build_arancel.py
"""
import csv
import re
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "raw"
BASE = RAW / "arancel_nacional_2025-02_10digitos.xlsx"
LNE = RAW / "lne_2026.xlsx"
IRAE_ANNEX = RAW / "normas" / "anticipo_irae_importacion_anexo.pdf"
CHANGES = HERE / "cambios.csv"
ANTIDUMPING = HERE / "antidumping.csv"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
MEF = "https://www.gub.uy/ministerio-economia-finanzas/sites/ministerio-economia-finanzas/files"

# Norms published after the February 2025 base.
NORMAS = [
    ("2025-07-29", "Resolución MEF 1434/025", "apertura de códigos a 10 dígitos para luminarias LED",
     "normas/res_mef_1434-025_luminarias_led.pdf", f"{MEF}/2026-09/RES%20MEF%20-%201434%20-%20LUMINARIAS%20LED.pdf", "aplicada (cambios.csv)"),
    ("2025-12-30", "Decreto anticipo IRAE en la importación", "anticipo de IRAE del 4% sobre valor en aduana más arancel para los códigos del anexo",
     "normas/anticipo_irae_importacion_decreto_2025-12-30.pdf", f"{MEF}/2026-01/Decreto%2030_12_25%20mef_230.pdf", "aplicada (columna anticipo_irae)"),
    ("2026-01-22", "Resolución MEF 2322/026", "modificaciones de códigos a 10 dígitos",
     "normas/res_mef_2322-026_mod_arancelaria.pdf", f"{MEF}/2026-09/RES%20MEF%202322-26_Mod%20arancelaria_DO280126.pdf", "aplicada (cambios.csv)"),
    ("2026-02-18", "Decreto 36/026", "incorpora Resoluciones GMC 09/25, 17/25, 18/25 y 19/25 (modificaciones NCM y AEC)",
     "normas/decreto_036-026_res_gmc_09_17_18_19-25.pdf", f"{MEF}/2026-10/DTO%2036-26_Res%20GMC%2009%2C17%2C18%20y%2019-25_180226_DO020326.pdf", "aplicada a 10 dígitos por la Res. MEF 4417/026"),
    ("2026-05-29", "Decreto 110/026 y Resolución MEF 3635/026", "nueva Lista Nacional de Excepciones al AEC",
     "normas/res_mef_3635-026_lne_2026.pdf", f"{MEF}/2026-09/Res%20MEF_3635_%20LNE_100726_DO210726.pdf", "aplicada (lne.csv y columna lne)"),
    ("2026-09-23", "Resolución MEF 4417/026", "traslado a 10 dígitos del Decreto 36/026",
     "normas/res_mef_4417-026_res_arancelaria.pdf", f"{MEF}/2026-09/RES%20MEF%204417-26_Res%20arancelaria_DO300926.pdf", "aplicada (cambios.csv)"),
    ("2022-05-01", "Resolución 113/022 (antidumping)", "derechos antidumping a calentadores eléctricos de agua de China",
     "normas/antidumping_res_113-022_calentadores_china.pdf", "https://medios.presidencia.gub.uy/legal/2022/resoluciones/05/mef_689.pdf", "en antidumping.csv (vencida)"),
    ("2024-11-01", "Resolución 300/024 (antidumping)", "derechos antidumping a expeller de soja de Argentina (2304.00.90.00)",
     "normas/antidumping_res_300-024_expeller_soja_argentina.pdf", f"{MEF}/2024-11/Resolucion%20PE%20300_24.pdf", "en antidumping.csv y columna antidumping"),
]


def read_sheet(path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
        for row in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).iter(f"{{{NS['m']}}}row"):
            cells = {}
            for c in row.findall("m:c", NS):
                v = c.find("m:v", NS)
                if v is not None:
                    col = re.match(r"[A-Z]+", c.get("r")).group(0)
                    cells[col] = (shared[int(v.text)] if c.get("t") == "s" else v.text).strip()
            yield cells


def irae_codes():
    text = subprocess.run(["pdftotext", str(IRAE_ANNEX), "-"], capture_output=True, text=True, check=True).stdout
    return {code.zfill(10) for code in re.findall(r"\b\d{9,10}\b", text)}


def read_lne():
    rows, notes = [], {}
    for cells in read_sheet(LNE):
        a, b = cells.get("A", ""), cells.get("B", "")
        if re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", b):
            rows.append({"ncm8": b, "notas": cells.get("C", ""), "tga_extrazona_pct": cells.get("D", "")})
        elif a.isdigit() and b:
            notes[a] = b
    for r in rows:
        r["notas"] = "; ".join(notes.get(n.strip(), n.strip()) for n in r["notas"].split(",") if n.strip())
    return rows


def apply_changes(rows):
    """Apply cambios.csv in date order: `alta` adds or replaces a code, `baja` removes it."""
    by_code = {}
    for r in rows:
        by_code.setdefault(r["ncm"], []).append(r)
    with open(CHANGES, encoding="utf-8") as f:
        changes = sorted(csv.DictReader(f), key=lambda c: c["fecha"])
    for c in changes:
        ncm = c["ncm"]
        if c["accion"] == "baja":
            if by_code.pop(ncm, None) is None:
                print(f"warning: {c['norma']} removes {ncm}, which is not in the tariff")
            continue
        by_code[ncm] = [{
            "ncm": ncm, "ncm8": ncm[:10], "capitulo": ncm[:2], "descripcion": c["descripcion"],
            "aec_pct": c["aec_pct"], "lista_especial": c["lista_especial"],
            "tga_extrazona_pct": c["tga_extrazona_pct"], "tga_intrazona_pct": c["tga_intrazona_pct"],
            "uvf": c["uvf"], "norma": c["norma"],
        }]
    return [r for code in sorted(by_code) for r in by_code[code]]


def main():
    irae = irae_codes()
    lne = read_lne()
    lne_codes = {r["ncm8"] for r in lne}
    out, seen = [], {}
    for cells in read_sheet(BASE):
        ncm = cells.get("A", "")
        if not re.fullmatch(r"\d{4}\.\d{2}\.\d{2}\.\d{2}", ncm):
            continue
        if seen.get(ncm) == cells:
            continue  # the MEF workbook repeats some rows verbatim
        if ncm in seen:
            print(f"warning: {ncm} appears twice with different values in the MEF workbook; both rows kept")
        seen[ncm] = cells
        ncm8 = ncm[:10]
        out.append({
            "ncm": ncm, "ncm8": ncm8, "capitulo": ncm[:2], "descripcion": cells.get("B", ""),
            "aec_pct": cells.get("C", ""), "lista_especial": cells.get("D", ""),
            "tga_extrazona_pct": cells.get("E", ""), "tga_intrazona_pct": cells.get("F", ""),
            "uvf": cells.get("G", ""), "norma": "base febrero 2025",
        })
    if not out:
        raise SystemExit("No tariff rows parsed; check the workbook layout.")
    with open(ANTIDUMPING, encoding="utf-8") as f:
        antidumping = {r["ncm"] for r in csv.DictReader(f) if r["estado"].startswith("vigente")}
    out = apply_changes(out)
    for r in out:
        r["lne"] = "si" if r["ncm8"] in lne_codes else ""
        r["anticipo_irae_pct"] = "4" if r["ncm"].replace(".", "") in irae else ""
        r["antidumping"] = "si" if r["ncm"] in antidumping else ""
    missing = irae - {r["ncm"].replace(".", "") for r in out}
    for name, rows in (("arancel.csv", out), ("lne.csv", lne)):
        with open(HERE / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    with open(HERE / "normas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["fecha", "norma", "contenido", "archivo", "url", "estado_en_arancel_csv"])
        w.writerows(NORMAS)
    print(f"arancel.csv: {len(out)} codes; lne.csv: {len(lne)}; IRAE annex codes no longer in force: {sorted(missing) or 0}")


if __name__ == "__main__":
    main()
