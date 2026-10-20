"""Build clean CPI (IPC) tables from INE's general index workbook.

Reads raw/IPC gral y variaciones_base 2022.xlsx (Total País, base Octubre 2022 = 100)
and writes:
  ipc_mensual.csv  one row per month: anio, mes, ipc
  ipc_anual.csv    one row per complete year: index averages, December index and inflation rates

Standard library only. Run: python3 build_ipc.py
"""
import csv
import datetime
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "raw" / "IPC gral y variaciones_base 2022.xlsx"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_first_sheet(path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
        sheet = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml", n))[0]
        rows = []
        for row in ET.fromstring(z.read(sheet)).iter(f"{{{NS['m']}}}row"):
            cells = {}
            for c in row.findall("m:c", NS):
                col = re.match(r"[A-Z]+", c.get("r")).group(0)
                v = c.find("m:v", NS)
                if v is None:
                    continue
                cells[col] = shared[int(v.text)] if c.get("t") == "s" else v.text
            rows.append(cells)
        return rows


def to_month(value):
    """Column A holds an Excel date serial (first day of the month)."""
    try:
        d = datetime.date(1899, 12, 30) + datetime.timedelta(days=float(value))
    except (TypeError, ValueError):
        return None
    return d.year, d.month


def main():
    monthly = {}
    for cells in read_first_sheet(RAW):
        ym = to_month(cells.get("A"))
        if ym and cells.get("B"):
            monthly[ym] = float(cells["B"])
    if not monthly:
        raise SystemExit("No monthly rows parsed; check the workbook layout.")

    with open(HERE / "ipc_mensual.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "mes", "ipc"])
        for (y, m), v in sorted(monthly.items()):
            w.writerow([y, m, f"{v:.10g}"])

    years = sorted({y for y, _ in monthly})
    complete = [y for y in years if all((y, m) in monthly for m in range(1, 13))]
    annual = {}
    for y in complete:
        vals = [monthly[(y, m)] for m in range(1, 13)]
        annual[y] = (sum(vals) / 12, monthly[(y, 12)])

    with open(HERE / "ipc_anual.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "ipc_promedio", "ipc_diciembre",
                    "inflacion_promedio_pct", "inflacion_dic_dic_pct"])
        for y in complete:
            avg, dec = annual[y]
            prev = annual.get(y - 1)
            inf_avg = f"{(avg / prev[0] - 1) * 100:.4f}" if prev else ""
            inf_dec = f"{(dec / prev[1] - 1) * 100:.4f}" if prev else ""
            w.writerow([y, f"{avg:.10g}", f"{dec:.10g}", inf_avg, inf_dec])

    first, last = min(monthly), max(monthly)
    print(f"monthly: {len(monthly)} rows {first[0]}-{first[1]:02} .. {last[0]}-{last[1]:02}")
    print(f"annual:  {len(complete)} complete years {complete[0]}..{complete[-1]}")


if __name__ == "__main__":
    main()
