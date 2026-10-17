"""Compare the postal/courier import regime in force in 2024 with the one in force since May 2026.

2024: Decreto 356/014 as amended by Decretos 336/015 and 453/016 (raw/decreto_356-014_texto_actualizado_aduanas.txt,
      raw/aduanas_2015-12-29_regimen_simplificado.txt).
2026: Ley 20.446 arts. 627-635 and Decreto 50/026 (raw/decreto_050-026_envios_postales.pdf); the simplified 60% regime
      changed on 23/03/2026 and the franchise on 01/05/2026.

Writes:
  comparacion.csv  rule by rule, 2024 vs 2026
  escenarios.csv   tax paid on one purchase by value and origin, best option in each regime
  perfiles.csv     tax paid over a year for a few typical buyers

Standard library only. Run: python3 build_comparacion.py
"""
import csv
from pathlib import Path

HERE = Path(__file__).parent
D356 = "Decreto 356/014 (texto actualizado)"
D50 = "Decreto 50/026"
UXXI = "Guía Uruguay XXI 2026"

COMPARACION = [
    ("vigencia", "1/1/2015 a 30/4/2026 (franquicia); simplificado hasta 22/3/2026", "simplificado desde 23/3/2026; franquicia desde 1/5/2026", D356, f"{D50} art. 18"),
    ("peso máximo por envío", "20 kg", "20 kg", f"{D356} art. 1", f"{D50} art. 1"),
    ("franquicia: cantidad de envíos", "3 por año civil", "3 por año civil", f"{D356} art. 5 c)", f"{D50} art. 4 c)"),
    ("franquicia: tope de valor", "USD 200 por envío expreso (courier); USD 50 por envío no expreso (correo común)", "USD 800 acumulados por año entre los 3 envíos", f"{D356} arts. 3 y 4", f"{D50} art. 3"),
    ("franquicia: aranceles", "exento", "exento", f"{D356} arts. 3 y 4", f"{D50} art. 3"),
    ("franquicia: IVA", "exento (exento de todo tributo)", "22% sobre el valor; mínimo USD 20 por envío según la guía oficial", f"{D356} arts. 3 y 4", f"{D50} art. 3; {UXXI}"),
    ("franquicia: excepción IVA Estados Unidos", "no aplica (todo exento)", "exento de IVA si el vendedor es residente en EE.UU., está registrado en la DNA (desde 3/11/2026) y el envío no supera USD 200", "", f"{D50} art. 3; Aduanas"),
    ("franquicia: obsequios familiares", "exentos; correo común hasta USD 50", "exentos de todo tributo; consumen cupo", f"{D356} art. 3", f"{D50} art. 3"),
    ("franquicia: libros y medicamentos de uso personal", "fuera del límite de 3 envíos", "fuera del tope de USD 800 (medicamentos con autorización del MSP)", f"{D356} art. 5", f"{D50} art. 4"),
    ("franquicia: medio de pago", "tarjeta de crédito o débito internacional o dinero electrónico", "ídem, a nombre del comprador y destinatario, con autorización a informar a la DNA", f"{D356} art. 5 d)", f"{D50} art. 4 d) a f)"),
    ("franquicia: identidad", "persona física mayor de edad", "persona física mayor de edad con documento uruguayo, registro único y control de identidad digital ante la DNA", f"{D356} art. 5 a)", f"{D50} art. 4 a) y g)"),
    ("régimen simplificado (prestación única): tasa", "60% del valor, sustituye todos los tributos", "60% del valor, sustituye todos los tributos", "Aduanas 29/12/2015", f"{D50} art. 2"),
    ("régimen simplificado: tope por envío", "USD 200", "USD 800", "Aduanas 29/12/2015", f"{D50} art. 2"),
    ("régimen simplificado: pago mínimo", "USD 10 por envío", "USD 20 por envío", "Aduanas 29/12/2015", f"{D50} art. 2"),
    ("régimen simplificado: cantidad de envíos", "sin límite", "sin límite", "", ""),
    ("régimen simplificado: quién puede usarlo", "personas físicas", "personas físicas o jurídicas", "Aduanas 29/12/2015", f"{D50} art. 2"),
    ("bienes con IMESI (alcohol, tabaco, perfumes, etc.)", "excluidos del régimen", "excluidos del régimen", f"{D356} art. 8", f"{D50} art. 7"),
    ("quién paga los tributos", "el usuario ante la DNA", "el operador postal, como responsable por obligaciones de terceros", "", f"{D50} art. 8"),
    ("incumplimiento", "pagar tributos en 30 días o abandono", "pierde la franquicia, paga 60% más multa del doble de tributos por declaración inexacta", f"{D356} art. 13", f"{D50} art. 15; {UXXI}"),
    ("valores mayores al tope", "régimen general de importación (aranceles, IVA, IMESI, tasas; despachante)", "ídem", "", ""),
]

VALORES = [20, 50, 100, 150, 200, 250, 300, 400, 500, 800, 1000]
ORIGENES = [("EE.UU. (vendedor registrado)", True), ("otros países (China, Europa, etc.)", False)]
GENERAL = "régimen general"


def r2(x):
    return round(x, 2)


def tax_2024(value, courier, franquicia_disponible):
    """Cheapest legal option in 2024 for one shipment. Returns (tax, option)."""
    limit = 200 if courier else 50
    if franquicia_disponible and value <= limit:
        return 0.0, "franquicia (exento)"
    if value <= 200:
        return max(0.6 * value, 10), "simplificado 60%"
    return None, GENERAL


def options_2026(value, from_us, cupo_restante, envios_franquicia_restantes):
    """All 2026 options for one shipment, as {option: tax}."""
    opts = {}
    if envios_franquicia_restantes > 0 and value <= cupo_restante:
        if from_us and value <= 200:
            opts["franquicia (IVA exento por TIFA)"] = 0.0
        else:
            opts["franquicia (IVA 22%)"] = max(0.22 * value, 20)
    if value <= 800:
        opts["simplificado 60%"] = max(0.6 * value, 20)
    return opts


def best(opts):
    if not opts:
        return None, GENERAL
    name = min(opts, key=opts.get)
    return opts[name], name


def escenarios():
    rows = []
    for courier in (True, False):
        canal = "courier (entrega expresa)" if courier else "correo común (no expreso)"
        for origen, from_us in ORIGENES:
            for v in VALORES:
                t24, o24 = tax_2024(v, courier, True)
                t26, o26 = best(options_2026(v, from_us, 800, 3))
                rows.append({
                    "canal": canal, "origen": origen, "valor_usd": v,
                    "impuesto_2024_usd": "" if t24 is None else r2(t24), "opcion_2024": o24,
                    "impuesto_2026_usd": "" if t26 is None else r2(t26), "opcion_2026": o26,
                    "diferencia_usd": "" if t24 is None or t26 is None else r2(t26 - t24),
                    "costo_total_2024_usd": "" if t24 is None else r2(v + t24),
                    "costo_total_2026_usd": "" if t26 is None else r2(v + t26),
                })
    return rows


PERFILES = [
    ("3 compras de USD 50 en China por courier", [(50, False)] * 3),
    ("3 compras de USD 150 en EE.UU. por courier", [(150, True)] * 3),
    ("3 compras de USD 150 en China por courier", [(150, False)] * 3),
    ("6 compras de USD 100 en China por courier", [(100, False)] * 6),
    ("12 compras de USD 30 en China por courier", [(30, False)] * 12),
    ("2 compras de USD 400 en EE.UU. por courier", [(400, True)] * 2),
    ("1 compra de USD 800 en China por courier", [(800, False)]),
]


def perfiles():
    rows = []
    for nombre, compras in PERFILES:
        total24 = total26 = 0.0
        general24 = general26 = 0
        franq24, cupo, franq26 = 3, 800.0, 3
        for value, from_us in compras:
            t, opt = tax_2024(value, True, franq24 > 0)
            if opt.startswith("franquicia"):
                franq24 -= 1
            if t is None:
                general24 += 1
            else:
                total24 += t
            opts = options_2026(value, from_us, cupo, franq26)
            # use the franchise only while it beats the 60% option
            t, opt = best(opts)
            if opt.startswith("franquicia"):
                franq26 -= 1
                cupo -= value
            if t is None:
                general26 += 1
            else:
                total26 += t
        # shipments that fall into the general regime have no comparable amount, so the totals are left blank
        t24 = "" if general24 else r2(total24)
        t26 = "" if general26 else r2(total26)
        rows.append({
            "perfil": nombre, "gasto_usd": sum(v for v, _ in compras),
            "impuesto_2024_usd": t24, "impuesto_2026_usd": t26,
            "diferencia_usd": r2(total26 - total24) if t24 != "" and t26 != "" else "",
            "envios_a_regimen_general_2024": general24, "envios_a_regimen_general_2026": general26,
        })
    return rows


def write(name, rows):
    with open(HERE / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    write("comparacion.csv", [dict(zip(("concepto", "regimen_2024", "regimen_2026", "norma_2024", "norma_2026"), c)) for c in COMPARACION])
    write("escenarios.csv", escenarios())
    write("perfiles.csv", perfiles())
    print("comparacion.csv, escenarios.csv, perfiles.csv written")


if __name__ == "__main__":
    main()
