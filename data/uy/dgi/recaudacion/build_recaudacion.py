"""Build clean tax-collection tables from DGI's annual series by tax.

Reads raw/Recaudación por impuesto - Series anuales.csv (pesos corrientes, 1982 on)
and writes:
  impuestos.csv           one row per tax: sigla, nombre, grupo, desde, hasta, nota
                          (desde: DGI's series start; hasta: last year with collections)
  recaudacion_anual.csv   one row per year and tax: anio, sigla, monto (pesos corrientes)

Each tax's grupo follows the sections of MEF's revenue classification (bal_recursos):
renta, consumo (bienes y servicios), propiedad, otros. "AJUSTES" is DGI's total minus
the sum of the taxes it lists (9–16% before 1990, when DGI details few taxes; under 1.5%
from 1994); "TOTAL" is DGI's own total.

Standard library only. Run: python3 build_recaudacion.py
"""
import csv
import io
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "raw" / "Recaudación por impuesto - Series anuales.csv"

# DGI column -> (sigla, short name, grupo), in DGI's column order.
TAXES = {
    "IMPUESTO A LAS RENTAS DE LAS ACTIVIDADES ECONÓMICAS - IRAE": ("IRAE", "IRAE (rentas de las empresas)", "renta"),
    "IMPUESTO A LA ENAJENACIÓN DE LOS BIENES AGROPECUARIOS - IMEBA": ("IMEBA", "IMEBA (venta de bienes agropecuarios)", "consumo"),
    "IMPUESTO A LA RENTA DE LAS PERSONAS FÍSICAS  CATEGORÍA I - IRPF Cat I": ("IRPF-I", "IRPF categoría I (capital)", "renta"),
    "IMPUESTO A LA RENTA DE LAS PERSONAS FÍSICAS  CATEGORÍA II - IRPF Cat II": ("IRPF-II", "IRPF categoría II (trabajo)", "renta"),
    "IMPUESTO A LAS RENTAS DE LOS NO RESIDENTES - IRNR": ("IRNR", "IRNR (no residentes)", "renta"),
    "IMPUESTO DE ASISTENCIA A LA SEGURIDAD SOCIAL - IASS": ("IASS", "IASS (jubilaciones y pensiones)", "renta"),
    "IMPUESTO A LAS SOCIEDAES FINANCIERAS DE INVERSIÓN - ISAFI": ("ISAFI", "ISAFI (sociedades financieras de inversión)", "propiedad"),
    "IMPUESTO AL PATRIMONIO PERSONAS JURÍDICAS": ("IP-PJ", "Patrimonio, personas jurídicas", "propiedad"),
    "IMPUESTO AL PATRIMONIO DE LAS EXPLOTACIONES AGROPECUARIAS": ("IP-AGRO", "Patrimonio, explotaciones agropecuarias", "propiedad"),
    "SOBRETASA DEL IMPUESTO AL PATRIMONIO": ("IP-SOBRETASA", "Sobretasa del Impuesto al Patrimonio", "propiedad"),
    "IMPUESTO DE CONTROL DE SOCIEDADES ANÓNIMAS - ICOSA": ("ICOSA", "ICOSA (control de sociedades anónimas)", "propiedad"),
    "IMPUESTO AL PATRIMONIO PERSONAS FÍSICAS": ("IP-PF", "Patrimonio, personas físicas", "propiedad"),
    "IMPUESTO A LAS TRASMISIONES PATRIMONIALES - ITP": ("ITP", "ITP (transmisiones patrimoniales)", "propiedad"),
    "IMPUESTO A LAS TRASMISIONES PATRIMONIALES - Adicional": ("ITP-AD", "ITP adicional", "propiedad"),
    "IMPUESTO AL VALOR AGREGADO - IVA": ("IVA", "IVA (valor agregado)", "consumo"),
    "IMPUESTO A LA PEQUEÑA EMPRESA (IVA Mínimo)": ("IVA-MIN", "IVA mínimo (pequeña empresa)", "consumo"),
    "IMPUESTO ESPECÍFICO INTERNO - IMESI": ("IMESI", "IMESI (específico interno)", "consumo"),
    "IMPUESTO A LA ENAJENACIÓN DE LOS BIENES AGROPECUARIOS - Adicional MEVIR": ("IMEBA-MEVIR", "IMEBA adicional MEVIR", "consumo"),
    "IMPUESTO A LA ENAJENACIÓN DE LOS BIENES AGROPECUARIOS - Adicional INIA": ("IMEBA-INIA", "IMEBA adicional INIA", "consumo"),
    "IMPUESTO A LOS INGRESOS DE LAS COMPAÑÍAS DE SEGUROS": ("SEGUROS", "Ingresos de las compañías de seguros", "renta"),
    "IMPUESTO PARA EL FONDO DE INSPECCIÓN SANITARIA - FIS": ("FIS", "FIS (Fondo de Inspección Sanitaria)", "consumo"),
    "IMPUESTO A LAS RENTAS DE INDUSTRIA Y COMERCIO - IRIC": ("IRIC", "IRIC (rentas de industria y comercio)", "renta"),
    "IMPUESTO DE CONTRIBUCION AL FINANCIAMIENTO DE LA SEGURIDAD SOCIAL - COFIS": ("COFIS", "COFIS (financiamiento de la seguridad social)", "consumo"),
    "IMPUESTO ESPECÍFICO A LOS SERVICIOS DE SALUD - IMESSA": ("IMESSA", "IMESSA (servicios de salud)", "consumo"),
    "IMPUESTO A LAS COMISIONES": ("COMISIONES", "Comisiones", "consumo"),
    "IMPUESTO A LAS VENTAS FORZADAS": ("VENTAS-FORZADAS", "Ventas forzadas", "consumo"),
    "IMPUESTO A LAS TARJETAS DE CREDITO": ("TARJETAS", "Tarjetas de crédito", "consumo"),
    "IMPUESTO A LAS TELECOMUNICACIONES - ITEL": ("ITEL", "ITEL (telecomunicaciones)", "consumo"),
    "IMPUESTO A LOS INGRESOS DE LOS ORGANIZADORES DE SORTEOS": ("SORTEOS", "Ingresos de organizadores de sorteos", "renta"),
    "IMPUESTO A LA COMPRA DE MONEDA EXTRANJERA - ICOME": ("ICOME", "ICOME (compra de moneda extranjera)", "consumo"),
    "IMPUESTO A LA COMPRA-VENTA DE BIENES EN REMATE PÚBLICO": ("REMATES", "Compraventa en remate público", "consumo"),
    "IMPUESTO A LAS CESIONES DE DERECHOS SOBRE DEPORTISTAS": ("DEPORTISTAS", "Cesiones de derechos sobre deportistas", "consumo"),
    "IMPUESTO A LOS ACTIVOS DE LAS EMPRESAS BANCARIAS - IMABA": ("IMABA", "IMABA (activos bancarios)", "propiedad"),
    "IMPUESTO DE CONTROL DEL SISTEMA FINANCIERO - ICOSIFI": ("ICOSIFI", "ICOSIFI (control del sistema financiero)", "otros"),
    "IMPUESTO A LAS RENTAS AGROPECUARIAS - IRA": ("IRA", "IRA (rentas agropecuarias)", "renta"),
    "IMPUESTO A LAS ACTIVIDADES AGROPECUARIAS - IMAGRO": ("IMAGRO", "IMAGRO (actividades agropecuarias)", "renta"),
    "IMPUESTO DE EDUCACIÓN PRIMARIA": ("PRIMARIA", "Impuesto de Primaria (inmuebles)", "propiedad"),
}
TOTAL = "RECAUDACIÓN TOTAL DE LA DGI"


def number(s):
    """DGI writes whole pesos with dot thousands: '1.427.065.702'."""
    s = s.strip()
    return int(s.replace(".", "")) if s else None


def main():
    rows = list(csv.reader(io.StringIO(RAW.read_text(encoding="latin-1")), delimiter=";"))
    header, starts, notes = rows[0], rows[1], rows[2]
    cols = {name: i for i, name in enumerate(header)}
    missing = [n for n in [*TAXES, TOTAL] if n not in cols]
    if missing:
        raise SystemExit(f"Columns not in the DGI file (layout changed?): {missing}")
    extra = [n for n in header[2:] if n not in TAXES and n != TOTAL]
    if extra:
        raise SystemExit(f"New DGI columns, add them to TAXES: {extra}")

    years = [r for r in rows[3:] if r and r[0].strip().isdigit()]
    out = []
    for r in years:
        y = int(r[0])
        amounts = {s: number(r[cols[name]]) for name, (s, _, _) in TAXES.items()}
        total = number(r[cols[TOTAL]])
        out += [(y, s, v) for s, v in amounts.items() if v]
        out.append((y, "AJUSTES", total - sum(v or 0 for v in amounts.values())))
        out.append((y, "TOTAL", total))

    with open(HERE / "recaudacion_anual.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "sigla", "monto"])
        w.writerows(out)

    last_paid = {}
    for y, s, v in out:
        last_paid[s] = y
    with open(HERE / "impuestos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sigla", "nombre", "grupo", "desde", "hasta", "nota"])
        for name, (s, short, group) in TAXES.items():
            i = cols[name]
            w.writerow([s, short, group, starts[i].split()[0], last_paid.get(s, ""), " ".join(notes[i].split())])
        w.writerow(["AJUSTES", "Otros y ajustes", "otros", years[0][0], last_paid["AJUSTES"],
                    "Total de la DGI menos la suma de los impuestos que lista."])

    print(f"{len(TAXES)} taxes, {len(years)} years {years[0][0]}..{years[-1][0]}, {len(out)} rows")


if __name__ == "__main__":
    main()
