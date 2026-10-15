#!/usr/bin/env python3
"""myrmidon — central command line for the harvested Uruguayan public-finance data.

Usage:
  python3 myrmidon.py --help
  python3 myrmidon.py sources
  python3 myrmidon.py inflation --since 1980 --every 5
  python3 myrmidon.py spending --since 1980 --every 5 --base 2025 [--csv]

Adding a command: write a function that takes `args`, decorate it with
@command("help text", arg(...), ...). The function name becomes the command
name (underscores turn into dashes). Standard library only.
"""
import argparse
import csv
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OPP_DETAIL = ROOT / "opp" / "credito-presupuestal"
OPP_HIST = ROOT / "opp" / "historico" / "Ejecucion Presupuestal 1961-2010_PTO NACIONAL.csv"
MEF_RC = ROOT / "mef" / "rendicion-cuentas"
IPC_ANUAL = ROOT / "inflation" / "ine-ipc" / "ipc_anual.csv"
CACHE = ROOT / ".cache" / "totals.json"

# MEF counts this funding source; OPP leaves it out. Excluded by default so years compare.
FONDOS_TERCEROS = "Fondos de Terceros Declarados por Ley"

COMMANDS = {}


def arg(*flags, **kwargs):
    return flags, kwargs


def command(help_text, *arguments):
    def register(fn):
        COMMANDS[fn.__name__.replace("_", "-")] = (fn, help_text, arguments)
        return fn
    return register


YEAR_FILTERS = (
    arg("--since", type=int, help="first year to include"),
    arg("--until", type=int, help="last year to include"),
    arg("--every", type=int, metavar="N", help="only years divisible by N"),
    arg("--csv", action="store_true", help="print CSV instead of a table"),
)


# ---------------------------------------------------------------- parsing helpers

def num_es(s):
    """Spanish-formatted number: '1.234.567,89' -> 1234567.89; '' or ',00' -> 0."""
    s = s.strip()
    return float(s.replace(".", "").replace(",", ".")) if s else 0.0


ODS_TABLE = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
ODS_OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"


def iter_ods_rows(path):
    """Stream rows of the first sheet of an .ods file as lists of strings."""
    cell_tags = (ODS_TABLE + "table-cell", ODS_TABLE + "covered-table-cell")
    with zipfile.ZipFile(path) as z, z.open("content.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == ODS_TABLE + "table-row":
                row = []
                for c in el:
                    if c.tag not in cell_tags:
                        continue
                    repeat = min(int(c.get(ODS_TABLE + "number-columns-repeated", "1")), 1000)
                    value = c.get(ODS_OFFICE + "value")
                    if value is None:
                        value = "".join(c.itertext()).strip()
                    row.extend([value] * repeat)
                while row and row[-1] == "":
                    row.pop()
                if row:
                    yield row
                el.clear()
            elif el.tag == ODS_TABLE + "table":
                return


def cached(path, key, compute):
    """Memoize an expensive per-file result, invalidated when the file changes."""
    st = path.stat()
    stamp = [st.st_size, st.st_mtime_ns]
    try:
        cache = json.loads(CACHE.read_text())
    except (OSError, ValueError):
        cache = {}
    entry = cache.get(f"{path.relative_to(ROOT)}::{key}")
    if entry and entry["stamp"] == stamp:
        return entry["value"]
    value = compute()
    cache[f"{path.relative_to(ROOT)}::{key}"] = {"stamp": stamp, "value": value}
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1))
    return value


# ---------------------------------------------------------------- data loaders

def load_ipc():
    """{year: row} from ipc_anual.csv, with floats where present."""
    out = {}
    with open(IPC_ANUAL, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[int(r["anio"])] = {k: float(v) if v else None for k, v in r.items() if k != "anio"}
    return out


def spending_hist():
    """{year: pesos} executed, 1961–2010. Source values are thousands of current pesos."""
    with open(OPP_HIST, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f, delimiter=";"))
    header = rows[0]
    out = {}
    for i, year in enumerate(header[1:], start=1):
        out[int(year)] = sum(num_es(r[i]) for r in rows[1:] if len(r) > i) * 1000
    return out


def spending_opp_year(path):
    def compute():
        with open(path, encoding="utf-8") as f:
            return sum(num_es(r["ejecutado"]) for r in csv.DictReader(f))
    return cached(path, "ejecutado", compute)


def spending_mef_year(path, include_fondos_terceros=False):
    def compute():
        rows = iter_ods_rows(path)
        header = [h.strip() for h in next(rows)]
        i_amount, i_fin = header.index("OBLIGADO"), header.index("FINANCIAMIENTO_DESC")
        total = terceros = 0.0
        for r in rows:
            v = float(r[i_amount]) if len(r) > i_amount and r[i_amount] else 0.0
            total += v
            if len(r) > i_fin and r[i_fin].strip() == FONDOS_TERCEROS:
                terceros += v
        return {"total": total, "fondos_terceros": terceros}
    t = cached(path, "obligado", compute)
    return t["total"] if include_fondos_terceros else t["total"] - t["fondos_terceros"]


def spending_series(include_fondos_terceros=False):
    """{year: (pesos, source)} preferring MEF > OPP detail > OPP historic.

    OPP's file for the year MEF most recently closed is partial, so MEF wins when both exist.
    """
    series = {y: (v, "opp-historico") for y, v in spending_hist().items()}
    for p in sorted(OPP_DETAIL.glob("credito_presupuestal_detalle_*.csv")):
        series[int(p.stem.rsplit("_", 1)[1])] = (spending_opp_year(p), "opp")
    for p in sorted(MEF_RC.glob("*/bal_gastos.ods")):
        series[int(p.parent.name)] = (spending_mef_year(p, include_fondos_terceros), "mef")
    return series


def filter_years(years, args):
    return [y for y in sorted(years)
            if (args.since is None or y >= args.since)
            and (args.until is None or y <= args.until)
            and (not args.every or y % args.every == 0)]


def emit(headers, rows, as_csv):
    if as_csv:
        w = csv.writer(sys.stdout)
        w.writerow(headers)
        w.writerows(rows)
        return
    widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows)]
    print("  ".join(str(h).rjust(w) for h, w in zip(headers, widths)))
    for r in rows:
        print("  ".join(str(x).rjust(w) for x, w in zip(r, widths)))


def pct(x):
    return "" if x is None else f"{x:+.1f}%"


# ---------------------------------------------------------------- commands

@command("list which years each data source covers")
def sources(args):
    series = spending_series()
    ipc = load_ipc()
    by_source = {}
    for y, (_, src) in series.items():
        by_source.setdefault(src, []).append(y)
    rows = [[src, min(ys), max(ys), len(ys)] for src, ys in by_source.items()]
    rows.append(["ine-ipc (annual)", min(ipc), max(ipc), len(ipc)])
    emit(["source", "from", "to", "years"], rows, False)


@command("yearly CPI inflation (INE, Total País)", *YEAR_FILTERS)
def inflation(args):
    ipc = load_ipc()
    rows = [[y, pct(ipc[y]["inflacion_promedio_pct"]), pct(ipc[y]["inflacion_dic_dic_pct"])]
            for y in filter_years(ipc, args)]
    emit(["year", "avg_vs_avg", "dec_vs_dec"], rows, args.csv)


@command("national budget spending, nominal and inflation-adjusted",
         *YEAR_FILTERS,
         arg("--base", type=int, help="express real values in pesos of this year (default: latest)"),
         arg("--include-fondos-terceros", action="store_true",
             help="keep MEF's 'Fondos de Terceros' (not comparable with OPP years)"))
def spending(args):
    series = spending_series(args.include_fondos_terceros)
    ipc = load_ipc()
    usable = [y for y in series if y in ipc]
    base = args.base or max(usable)
    if base not in ipc:
        sys.exit(f"No annual CPI for base year {base}.")
    years = filter_years(usable, args)
    rows, prev, first = [], None, None
    for y in years:
        nominal, src = series[y]
        real = nominal * ipc[base]["ipc_promedio"] / ipc[y]["ipc_promedio"]
        first = first or (y, real)
        change = annual = None
        if prev:
            change = (real / prev[1] - 1) * 100
            annual = ((real / prev[1]) ** (1 / (y - prev[0])) - 1) * 100
        rows.append([y, src, f"{nominal / 1e9:.3f}", f"{real / 1e9:.1f}",
                     pct(change), pct(annual), pct((real / first[1] - 1) * 100)])
        prev = (y, real)
    print(f"# billions of pesos; real = pesos of {base} (INE annual average CPI)", file=sys.stderr)
    emit(["year", "source", "nominal_bn", f"real_{base}_bn", "vs_prev_row", "per_year", "vs_first"],
         rows, args.csv)


# ---------------------------------------------------------------- entry point

def main(argv=None):
    parser = argparse.ArgumentParser(prog="myrmidon", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    for name, (fn, help_text, arguments) in COMMANDS.items():
        p = sub.add_parser(name, help=help_text, description=help_text)
        for flags, kwargs in arguments:
            p.add_argument(*flags, **kwargs)
        p.set_defaults(func=fn)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
