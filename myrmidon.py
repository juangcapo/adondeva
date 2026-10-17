#!/usr/bin/env python3
"""myrmidon — central command line for the harvested Uruguayan public-finance data.

Usage:
  python3 myrmidon.py --help
  python3 myrmidon.py sources
  python3 myrmidon.py inflation --since 1980 --every 5
  python3 myrmidon.py spending --since 1980 --every 5 --base 2025 [--csv]
  python3 myrmidon.py tax sueldo 80000 --hijos 1
  python3 myrmidon.py tax compra 1500 [--tasa minima]
  python3 myrmidon.py tax importar 1200 --ncm 8471.30.12.00

Adding a command: write a function that takes `args`, decorate it with
@command("help text", arg(...), ...). The function name becomes the command
name (underscores turn into dashes). Standard library only.
"""
import argparse
import csv
import importlib.util
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Each country's data lives under data/<ISO 3166-1 alpha-2 code>/.
UY = ROOT / "data" / "uy"
OPP_DETAIL = UY / "opp" / "credito-presupuestal"
OPP_HIST = UY / "opp" / "historico" / "Ejecucion Presupuestal 1961-2010_PTO NACIONAL.csv"
MEF_RC = UY / "mef" / "rendicion-cuentas"
IPC_ANUAL = UY / "inflation" / "ine-ipc" / "ipc_anual.csv"
TAXES = UY / "taxes"
ARANCEL = UY / "aranceles" / "arancel.csv"
ENVIOS = UY / "aranceles" / "regimen-envios" / "build_comparacion.py"
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


# ---------------------------------------------------------------- tax calculator
# Rates come from the generated files in data/uy/taxes/ (see its README); each `rate` call
# names the row it uses, so a change in the data flows into the calculation.

def tax_rows(name):
    """Rows of data/uy/taxes/<name>.csv (name includes the level folder)."""
    with open(TAXES / f"{name}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rate(rows, pattern, field="tasa_pct"):
    """Numeric `field` of the first row whose condicion matches the regex `pattern`."""
    for r in rows:
        if re.search(pattern, r["condicion"], re.I) and r[field]:
            return float(r[field])
    sys.exit(f"tax data: no row matching {pattern!r} with {field}")


def reference_values():
    with open(TAXES / "valores_referencia.csv", encoding="utf-8") as f:
        return {r["unidad"]: float(r["valor"]) for r in csv.DictReader(f)}


def brackets_tax(amount, rows, pattern, unit):
    """Progressive tax: each bracket's rate applies to the part of `amount` inside it."""
    total = 0.0
    for r in rows:
        if not re.search(pattern, r["condicion"], re.I):
            continue
        lo = float(r["desde"]) * unit
        hi = float(r["hasta"]) * unit if r["hasta"] else float("inf")
        if amount > lo:
            total += (min(amount, hi) - lo) * float(r["tasa_pct"]) / 100
    return total


def tax_sueldo(amount, args):
    """Monthly nominal salary of a private-sector employee (Industria y Comercio)."""
    ref = reference_values()
    bpc = ref["BPC"]
    jub_p, jub_e = tax_rows("seguridad_social/aportes-jubilatorios-personales"), tax_rows("seguridad_social/aportes-jubilatorios-patronales")
    fonasa, frl = tax_rows("seguridad_social/aportes-al-fonasa-personal-y-patronal"), tax_rows("seguridad_social/fondo-de-reconversion-laboral")
    fgcl, irpf = tax_rows("seguridad_social/fondo-de-garantia-de-creditos-laborales"), tax_rows("nacional/impuesto-a-la-renta-de-las-personas-fisicas")

    # The personal pension contribution stops at tope C (Ley 16.713 arts. 7-8).
    jub_base = min(amount, rate(jub_p, r"^tope C", "monto"))
    tier = "hasta 2,5 BPC" if amount <= 2.5 * bpc else "mayor a 2,5 BPC"
    family = f"{'con' if args.conyuge else 'sin'} cónyuge, {'con' if args.hijos else 'sin'} hijos"
    lines = [
        ("aporte jubilatorio personal (BPS/AFAP)", jub_base, rate(jub_p, "Industria y Comercio")),
        (f"FONASA personal ({family})", amount, rate(fonasa, f"personal, remuneración {tier}, {family}")),
        ("Fondo de Reconversión Laboral", amount, rate(frl, "^personal")),
    ]
    personal = [(c, b, t, b * t / 100) for c, b, t in lines]
    aportes = sum(x[3] for x in personal)

    # IRPF monthly withholding: salaries above 10 BPC add 6%; deductions credit at 14% or 8%.
    base_irpf = amount * 1.06 if amount > 10 * bpc else amount
    gross_irpf = brackets_tax(base_irpf, irpf, "anticipo mensual", bpc)
    hijos = args.hijos * rate(irpf, "hijo menor a cargo", "monto") / 12 * bpc
    ded_rate = rate(irpf, "hasta 180 BPC" if amount * 12 <= 180 * bpc else "mayor a 180 BPC")
    credit = (aportes + hijos) * ded_rate / 100
    irpf_tax = max(0.0, gross_irpf - credit)
    personal.append((f"IRPF (franjas sobre ${base_irpf:,.0f}, menos {ded_rate:g}% de deducciones ${aportes + hijos:,.0f})",
                     base_irpf, None, irpf_tax))

    employer = [(c, b, t, b * t / 100) for c, b, t in [
        ("aporte jubilatorio patronal", amount, rate(jub_e, "Industria y Comercio")),
        ("FONASA patronal", amount, rate(fonasa, "^patronal")),
        ("Fondo de Reconversión Laboral patronal", amount, rate(frl, "^patronal")),
        ("Fondo de Garantía de Créditos Laborales", amount, rate(fgcl, "^patronal")),
    ]]
    take = sum(x[3] for x in personal)
    cost = sum(x[3] for x in employer)
    return ([("trabajador",) + x for x in personal] + [("empresa",) + x for x in employer],
            [("sueldo líquido", amount - take), ("costo total para la empresa", amount + cost),
             ("impuestos y aportes totales", take + cost), ("% del costo total", (take + cost) / (amount + cost) * 100)],
            f"UYU por mes; BPC ${bpc:,.0f}")


def tax_compra(amount, args):
    """Retail purchase: split the IVA out of the price (or add it with --neto)."""
    iva = tax_rows("nacional/impuesto-al-valor-agregado")
    pattern = {"basica": "^tasa básica", "minima": "^tasa mínima", "debito": "débito o dinero electrónico", "exento": None}[args.tasa]
    t = rate(iva, pattern) if pattern else 0.0
    net = amount if args.neto else amount / (1 + t / 100)
    tax = net * t / 100
    rows = [("consumidor", f"IVA {args.tasa}", net, t, tax)]
    return rows, [("precio sin IVA", net), ("precio final", net + tax), ("% del precio final", tax / (net + tax) * 100 if net else 0)], "UYU"


def load_envios():
    spec = importlib.util.spec_from_file_location("build_comparacion", ENVIOS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tax_importar(amount, args):
    """Import of goods valued `amount` USD CIF: general regime, or postal/courier with --envio."""
    if args.envio:
        opts = load_envios().options_2026(amount, args.eeuu, args.cupo, 1)
        if not opts:
            sys.exit(f"USD {amount:g} supera los USD 800: va al régimen general (sin --envio)")
        rows = [("comprador", name, amount, None, tax) for name, tax in sorted(opts.items(), key=lambda kv: kv[1])]
        best = min(opts.values())
        return rows, [("mejor opción: impuesto", best), ("costo total", amount + best), ("% sobre el valor", best / amount * 100)], \
            "USD por envío; cada fila es una opción alternativa (régimen 2026, Decreto 50/026)"

    if args.arancel is not None:
        tga, label = args.arancel, "arancel indicado"
    elif args.ncm:
        with open(ARANCEL, encoding="utf-8") as f:
            match = [r for r in csv.DictReader(f) if r["ncm"] == args.ncm or r["ncm8"] == args.ncm]
        if not match:
            sys.exit(f"NCM {args.ncm} no está en {ARANCEL.relative_to(ROOT)}")
        row = match[0]
        tga = float(row["tga_intrazona_pct" if args.mercosur else "tga_extrazona_pct"])
        label = f"TGA {row['ncm']} ({row['descripcion'][:40]})"
    else:
        sys.exit("indicá --ncm CODIGO o --arancel PCT (o --envio para compras por courier)")

    consular = tax_rows("aduana/tasa-consular")
    iva = tax_rows("aduana/iva-a-la-importacion")
    prefs = tax_rows("aduana/tasa-por-servicios-preferenciales")
    t_cons = rate(consular, "desde el Mercosur" if args.mercosur else "extrazona")
    t_iva = rate(iva, "^tasa mínima" if args.tasa == "minima" else "^tasa básica")
    duty = amount * tga / 100
    rows = [
        ("importador", label, amount, tga, duty),
        ("importador", "tasa consular", amount, t_cons, amount * t_cons / 100),
        ("importador", "tasa por servicios preferenciales (tope USD 50)", amount, rate(prefs, "permiso"),
         min(amount * rate(prefs, "permiso") / 100, rate(prefs, "permiso", "monto"))),
        ("importador", f"IVA importación ({args.tasa})", amount + duty, t_iva, (amount + duty) * t_iva / 100),
    ]
    if args.contribuyente:
        with open(ARANCEL, encoding="utf-8") as f:
            irae = next((float(r["anticipo_irae_pct"]) for r in csv.DictReader(f) if r["ncm"] == args.ncm and r["anticipo_irae_pct"]), 4.0)
        rows.append(("importador", "anticipo de IRAE (se descuenta del IRAE)", amount, irae, amount * irae / 100))
    tax = sum(r[4] for r in rows)
    return rows, [("total tributos", tax), ("costo puesto en plaza", amount + tax), ("% sobre CIF", tax / amount * 100)], \
        "USD sobre valor CIF; sin IMESI, despachante ni tasa de inspección (hasta 85 UI); tasa consular de fuente secundaria"


def tax_alquiler(amount, args):
    """Monthly rent received by a resident individual (IRPF Categoría I)."""
    bpc = reference_values()["BPC"]
    t = rate(tax_rows("nacional/impuesto-a-la-renta-de-las-personas-fisicas"), "Categoría I: alquileres")
    exempt = amount * 12 <= 40 * bpc  # rents up to 40 BPC a year are exempt (row notes)
    tax = 0.0 if exempt else amount * t / 100
    label = "IRPF alquileres" + (" (exento: hasta 40 BPC al año)" if exempt else " (sobre el bruto, sin gastos deducibles)")
    return [("arrendador", label, amount, t, tax)], [("neto para el arrendador", amount - tax)], "UYU por mes"


TAX_ACTIONS = {"sueldo": tax_sueldo, "compra": tax_compra, "importar": tax_importar, "alquiler": tax_alquiler}


@command("tax breakdown for an action and amount (Uruguay 2026)",
         arg("accion", choices=TAX_ACTIONS, help="sueldo (nominal mensual UYU), compra (precio UYU), importar (CIF USD), alquiler (mensual UYU)"),
         arg("monto", type=float, help="amount"),
         arg("--hijos", type=int, default=0, help="sueldo: hijos menores a cargo"),
         arg("--conyuge", action="store_true", help="sueldo: cónyuge a cargo en FONASA"),
         arg("--tasa", choices=["basica", "minima", "debito", "exento"], default="basica", help="compra/importar: tasa de IVA"),
         arg("--neto", action="store_true", help="compra: el monto no incluye IVA"),
         arg("--ncm", help="importar: código arancelario (10 u 8 dígitos con puntos)"),
         arg("--arancel", type=float, help="importar: arancel en %% en lugar de --ncm"),
         arg("--mercosur", action="store_true", help="importar: origen Mercosur"),
         arg("--contribuyente", action="store_true", help="importar: el importador es contribuyente de IRAE (anticipo 4%%)"),
         arg("--envio", action="store_true", help="importar: compra por courier o correo (franquicia o 60%%)"),
         arg("--eeuu", action="store_true", help="importar --envio: vendedor de EE.UU. registrado"),
         arg("--cupo", type=float, default=800, help="importar --envio: cupo de franquicia que queda en el año (USD)"),
         arg("--csv", action="store_true", help="print CSV instead of a table"))
def tax(args):
    rows, totals, unit = TAX_ACTIONS[args.accion](args.monto, args)
    print(f"# {args.accion} {args.monto:,.2f} — {unit}", file=sys.stderr)
    fmt = (lambda x: "" if x is None else f"{x:.2f}") if args.csv else (lambda x: "" if x is None else f"{x:,.2f}")
    table = [[who, concept, fmt(base), "" if t is None else f"{t:g}%", fmt(amount)] for who, concept, base, t, amount in rows]
    table += [["", name, "", "", fmt(value)] for name, value in totals]
    emit(["paga", "concepto", "base", "tasa", "monto"], table, args.csv)


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
