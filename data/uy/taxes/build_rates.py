"""Rebuild rates/*.csv from the RATES table below, one file per catalog.csv entry, and fill catalog.csv's `archivo` column.

To change a rate, edit RATES and run: python3 build_rates.py (standard library only).
Catalog entries missing from RATES get a single `sin_datos` row.
"""
import csv
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
COLS = ["condicion", "base", "desde", "hasta", "unidad_tramo", "tasa_pct", "monto", "unidad_monto",
        "vigencia", "confianza", "fuente", "notas"]

S = {
    "UXXI": "https://www.uruguayxxi.gub.uy/es/quiero-invertir/guias-inversor/sistema-tributario-2026/descarga/",
    "BPS_TASAS": "https://www.bps.gub.uy/835/tasas.html",
    "BPS_BONIF": "https://www.bps.gub.uy/10309/aporte-servicios-bonificados.html",
    "BPS_FONASA": "https://www.bps.gub.uy/10314/tasas-fonasa.html",
    "BPS_FRL": "https://www.bps.gub.uy/10322/fondo-reconversion-laboral-frl.html",
    "BPS_FGCL": "https://www.bps.gub.uy/15668/fondo-de-garantia-de-creditos-laborales.html",
    "BPS_VALORES": "https://www.bps.gub.uy/16815/valores.html",
    "BPS_CONST": "https://www.bps.gub.uy/837/aportacion-construccion.html",
    "BPS_FOCER": "https://www.bps.gub.uy/10316/fondo-de-cesantia-y-retiro-de-la-construccion-focer.html",
    "BPS_FSC": "https://www.bps.gub.uy/10317/fondo-social-de-la-construccion.html",
    "BPS_FOSVOC": "https://www.bps.gub.uy/10318/fondo-social-de-vivienda-construccion-fosvoc.html",
    "BPS_GRAF": "https://www.bps.gub.uy/10319/fondo-de-la-industria-grafica.html",
    "BPS_FOSMETAL": "https://www.bps.gub.uy/12129/fondo-social-metalurgico-fosmetal.html",
    "BPS_DOMFONDO": "https://www.bps.gub.uy/10960/fondo-social-trabajo-domestico.html",
    "BPS_MONO18083": "https://www.bps.gub.uy/6668/monotributo-ley-18083.html",
    "BPS_MONO19942": "https://www.bps.gub.uy/18051/monotributo-ley-19942.html",
    "BPS_MIDES": "https://www.bps.gub.uy/6667/monotributo-social-mides-ley-18874.html",
    "BPS_RURAL": "https://www.bps.gub.uy/15581/contribucion-patronal-rural.html",
    "BPS_RURALMIN": "https://www.bps.gub.uy/848/sector-rural.html",
    "BPS_MEVIR": "https://www.bps.gub.uy/15584/impuesto-afectado-a-mevir.html",
    "DGI_IVAMIN": "https://www.gub.uy/direccion-general-impositiva/comunicacion/publicaciones/monto-pagar-del-iva-minimo",
    "RSM_IVAMIN": "https://www.rsm.global/uruguay/en/node/747",
    "ELOBS_IRPF": "https://www.elobservador.com.uy/cuales-son-las-nuevas-franjas-aportes-irpf-2026-y-el-nuevo-valor-la-bpc-n6030375",
    "CAMBIO": "https://cambio-uruguay.com/en/impuestos-inversiones-uruguay",
    "MEMORY_IEP": "https://memory.com.uy/blog/obligaciones-fiscales/que-es-el-impuesto-de-primaria/",
    "DGI_IEP_RURAL": "https://www.gub.uy/direccion-general-impositiva/impuesto-primaria/padrones-rurales/informacion-para-calculo-ejercicio-2026",
    "DEC334": "https://www.impo.com.uy/bases/decretos/334-2025/2",
    "TODGI_T14": "https://impo.com.uy/bases/todgi2023/101-2024/53_T14",
    "TODGI_T11": "https://impo.com.uy/bases/todgi2023/101-2024/1_T11",
    "DEC21_2026": "https://www.impo.com.uy/bases/decretos/21-2026",
    "DGI_IMEBA": "https://www.gub.uy/direccion-general-impositiva/sites/direccion-general-impositiva/files/documentos/publicaciones/IMEBA%20122023.pdf",
    "DEC255": "https://impo.com.uy/bases/decretos/255-2025",
    "DEC359": "https://impo.com.uy/bases/decretos/359-2017/1",
    "DEC152": "https://impo.com.uy/bases/decretos/152-2025",
    "LEY13892": "https://impo.com.uy/bases/leyes-originales/13892-1970/421",
    "DETRAC": "https://medios.presidencia.gub.uy/legal/2025/decretos/06/miem_25_225.pdf",
    "DNA_PREF": "https://www.aduanas.gub.uy/innovaportal/v/2773/8/innova.front/tasa-por-servicios-preferenciales.html",
    "DEC235": "https://www.impo.com.uy/bases/decretos/235-2024",
    "DEC426": "https://www.aduanas.gub.uy/innovaportal/v/8915/3/innova.front/decreto-n%C2%B0-426_011.html",
    "AUTOBLOG_TC": "https://www.autoblog.com.uy/2017/10/que-es-la-tasa-consular-y-por-que-los.html",
    "YOFACT_IMPORT": "https://yo-facturo.com/blog/como-importar-a-uruguay/",
    "COMEX": "https://comexuruguay.com/blog/tributos-importacion-uruguay-2026/",
    "FEDEX_POSTAL": "https://www.fedex.com/content/dam/fedex/lac-latin-america/downloads/2026/UY_ES_2026_5_pdf_NA_Reg-Alert-28-April_cus.pdf",
    "DEC50": "https://medios.presidencia.gub.uy/legal/2026/decretos/03/mef_297.pdf",
    "ADU2015": "https://www.aduanas.gub.uy/innovaportal/v/14924/3/innova.front/a-partir-del-1%C2%B0-de-enero-se-modifica-el-regimen-para-compras-en-el-exterior.html",
    "LEY20446": "https://www.impo.com.uy/bases/leyes-originales/20446-2025",
    "LEY17820": "https://impo.com.uy/bases/leyes/17820-2004/3",
    "URSEA_MEM": "https://www.gub.uy/unidad-reguladora-servicios-energia-agua/sites/unidad-reguladora-servicios-energia-agua/files/2021-11/MEMORIA%20ANUAL%202015.pdf",
    "LEY16524": "https://impo.com.uy/bases/leyes/16524-1994/3",
    "MVD_FS": "https://www.montevideo.com.uy/Noticias/Ejecutivo-propone-eliminar-la-contribucion-adicional-del-Fondo-de-Solidaridad-en-Rendicion-uc826311",
    "CALCULAME_CJ": "https://calculame.uy/aporte-jubilatorio-cjppu-notarial",
    "CNOT": "https://www.cajanotarial.org.uy/innovaportal/v/1064/1/innova.front/actualizacion_semestral_del_arancel.html",
    "LEY19695": "https://impo.com.uy/bases/leyes-originales/19695-2018",
    "DEC161": "https://impo.com.uy/bases/decretos/161-2019",
    "SUCIVE": "https://www.gub.uy/congreso-intendentes/comunicacion/publicaciones/texto-ordenado-del-sucive-2026",
    "DATOSUY_CI": "https://datosuruguay.com/contribucion-inmobiliaria/montevideo",
    "MVD_CI_PROP": "https://www.montevideo.com.uy/Noticias/Intendencia-de-Montevideo-propone-pagar-la-Contribucion-Inmobiliaria-en-hasta-12-cuotas-uc967809",
    "DEC109": "https://www.impo.com.uy/bases/decretos/109-1994",
    "AUTOBLOG_EV": "https://www.autoblog.com.uy/2026/07/gobierno-aplicara-imesi-electricos-con.html",
    "CLASIAUTOS": "https://clasiautos.uy/descubri-que-impuestos-pagan-los-autos-en-uruguay-y-su-impacto-en-los-precios/",
    "FOCUS_APUESTAS": "https://focusgn.com/latinoamerica/uruguay-impuestos-entran-vigencia",
    "IEP_ANDERSEN": "https://uy.andersen.com/documents/IMPUESTO_DE_PRIMARIA_INMUEBLES_RURALES_EXONERACIO_N_pdf_1788273377.pdf",
    "ELOBS_IEP": "https://www.elobservador.com.uy/nacional/impuesto-primaria-2026-dgi-habilito-el-pago-la-tercera-cuota-n6057568",
    "DO_20260114": "https://www.impo.com.uy/diariooficial/2026/01/14/documentos.pdf",
    "DGI_IMESI_2009": "https://medios.presidencia.gub.uy/jm_portal/2011/noticias/NO_B582/IMESI.pdf",
    "BPS_R5_2026": "https://www.bps.gub.uy/23860/2026---comunicado-r-5---valores-escalas-irpf-2026.html",
    "LEY18396": "https://uruguay.justia.com/nacionales/leyes/ley-18396-oct-24-2008/gdoc/",
    "LEY18405": "https://uruguay.justia.com/nacionales/leyes/ley-18405-oct-24-2008/gdoc/",
    "MVD_CI": "https://tramites.montevideo.gub.uy/sites/tramites.montevideo.gub.uy/files/tributos/documentos/2026_Calculo_Contribucio%CC%81n_Inmobiliaria.pdf",
    "CARRASCO": "https://www.aeropuertodecarrasco.com.uy/tasa-de-embarque/",
    "PDE_EMB": "https://aeropuertodepuntadeleste.com.uy/tasa-de-embarque/",
    "BCU_TASA": "https://www.bcu.gub.uy/Leyes%20y%20Decretos/ernp18083.pdf",
    "BCU_ANTEPROY": "https://www.guyer.com.uy/informes-&-noticias/anteproyecto-de-ley-que-propone-modificacion-de-la-tasa-de-control-regulatorio-del-sistema-financiero",
    "DL15605": "https://www.impo.com.uy/bases/decretos-ley/15605-1984",
    "INAC_FAENA": "https://www.inac.uy/innovaportal/v/5431/17/innova.front/precios-fictos-07--y-tasa-control-de-faena",
    "MEF_ARANCEL": "https://www.gub.uy/ministerio-economia-finanzas/nomenclatura-aranceles-uruguay-0",
    "MEF_IRAE_ANT": "https://www.gub.uy/ministerio-economia-finanzas/sites/ministerio-economia-finanzas/files/2026-01/Decreto%2030_12_25%20mef_230.pdf",
}


def r(condicion, *, base="", desde="", hasta="", unidad_tramo="", tasa="", monto="", unidad_monto="",
      vigencia="", confianza="oficial", src="", notas=""):
    return {"condicion": condicion, "base": base, "desde": desde, "hasta": hasta, "unidad_tramo": unidad_tramo,
            "tasa_pct": tasa, "monto": monto, "unidad_monto": unidad_monto, "vigencia": vigencia,
            "confianza": confianza, "fuente": S[src] if src else "", "notas": notas}


def nodata(notas="sin datos de tasa todavía"):
    return [r("sin datos", confianza="sin_datos", notas=notas)]


def brackets(cond, base, unit, cuts, rates, src, vig, conf="oficial"):
    """cuts are the upper limits of each bracket except the last (open-ended)."""
    rows, lo = [], 0
    for i, rate in enumerate(rates):
        hi = cuts[i] if i < len(cuts) else ""
        rows.append(r(cond, base=base, desde=lo, hasta=hi, unidad_tramo=unit, tasa=rate,
                      vigencia=vig, confianza=conf, src=src))
        lo = hi
    return rows


G = "guia_oficial"   # Uruguay XXI investor guide (June 2026), written by PwC for the government agency
SEC = "secundaria"
V26 = "2026"

RATES = {}

RATES["Impuesto al Valor Agregado"] = [
    r("tasa básica", base="precio de bienes y servicios gravados", tasa=22, vigencia=V26, confianza=G, src="UXXI"),
    r("tasa mínima: alimentos de primera necesidad, medicamentos, hospedaje hotelero", base="precio", tasa=10, vigencia=V26, confianza=G, src="UXXI"),
    r("tasa cero: exportaciones", base="precio", tasa=0, vigencia=V26, confianza=G, src="UXXI", notas="se devuelve el IVA compras"),
    r("tasa cero: productos agropecuarios en estado natural vendidos por contribuyentes de IRAE (salvo frutas, flores y hortalizas)", base="precio", tasa=0, vigencia=V26, confianza=G, src="UXXI"),
    r("exento: frutas y verduras naturales, moneda extranjera, inmuebles, maquinaria agrícola, combustibles salvo fuel oil y gasoil, leche, insumos agropecuarios, libros y prensa, agua de consumo básico, intereses y arrendamientos de inmuebles", base="precio", tasa=0, vigencia=V26, confianza=G, src="UXXI", notas="exento: no genera crédito de IVA compras"),
    r("venta a consumidor final pagada con débito o dinero electrónico", base="precio", tasa=20, vigencia=V26, confianza=G, src="UXXI", notas="2 puntos menos que la tasa básica (Ley 19.210)"),
    r("compras por envío postal dentro de la franquicia anual de USD 800 por persona (hasta 20 kg por envío)", base="valor declarado", tasa=22, monto=20, unidad_monto="USD mínimo por envío", vigencia=V26, confianza=G, src="UXXI", notas="Ley 20.446; la franquicia exonera aranceles pero no IVA"),
    r("servicios digitales de intermediación: oferente y demandante en Uruguay", base="100% del precio", tasa=22, vigencia=V26, confianza=G, src="UXXI"),
    r("servicios digitales de intermediación: oferente o demandante en el exterior", base="50% del precio", tasa=22, vigencia=V26, confianza=G, src="UXXI"),
]

_BEB = "base específica por litro (Dec. 342/025); el impuesto es esta base por la tasa del numeral"
_BEBIDAS_2026 = [
    ("numeral 1: champagne", 346.39), ("numeral 1: vermouth", 173.28), ("numeral 1: otros vinos finos y licorosos", 259.84),
    ("numeral 4: whisky", 253.68), ("numeral 4: grapas, cañas y amargas", 166.45), ("numeral 4: otros hasta 5% vol.", 192.92),
    ("numeral 4: demás bebidas alcohólicas", 258.67), ("numeral 5: cervezas sin alcohol", 99.69),
    ("numeral 5: cervezas envase retornable", 96.27), ("numeral 5: demás cervezas", 103.71),
    ("numeral 6: aguas minerales y sodas", 24.53), ("numeral 6: jugos y néctares con 50% o más de jugo", 40.62),
    ("numeral 6: base jugo de frutas con baja gasificación", 40.62), ("numeral 6: demás base jugo de fruta", 44.61),
    ("numeral 6: alimentos líquidos", 40.62), ("numeral 7: maltas", 71.24),
    ("numeral 7: jugos y néctares con 50% o más de jugo", 40.62), ("numeral 7: base jugo de frutas con baja gasificación", 40.62),
    ("numeral 7: demás base jugo de fruta", 44.61), ("numeral 7: alimentos líquidos", 40.62),
    ("numeral 7: bebidas con cafeína o taurina", 44.62), ("numeral 7: concentrados sólidos (por litro de bebida elaborada)", 2.61),
    ("numeral 7: demás bebidas sin alcohol", 44.61), ("numeral 16: amargos", 123.34),
]
_COMB_2026 = [
    ("nafta Súper 95 30-S", 22.92), ("nafta Premium 97 30-S", 25.05), ("queroseno", 10.34), ("nafta de aviación", 42.51),
    ("Jet A1", 0), ("nafta de aviación para la aviación nacional o de tránsito", 3.94), ("alcohol carburante", 37.32),
]
RATES["Impuesto Específico Interno"] = [
    r(f"bebidas, {c}", base=_BEB, monto=m, unidad_monto="UYU por litro", vigencia="desde ene-2026", src="DO_20260114") for c, m in _BEBIDAS_2026
] + [
    r(f"bebidas, tasa del numeral {n}", base="base específica", tasa=t, vigencia="dic-2009", confianza=SEC, src="DGI_IMESI_2009",
      notas="tasa de la recopilación DGI de 2009 (Dec. 96/990); puede haber cambiado")
    for n, t in [("1", 20.2), ("4", 80), ("5", 23.5), ("6 base jugo de fruta", 11), ("6 aguas minerales y sodas", 10.5),
                 ("6 y 7 alimentos líquidos y maltas", 13), ("7 los demás", 21.5), ("16", 21.5)]
] + [
    r(f"combustibles: {c}", base="litro enajenado", monto=m, unidad_monto="UYU por litro", vigencia="desde ene-2026", src="DO_20260114", notas="Dec. 343/025")
    for c, m in _COMB_2026
] + [
    r("combustibles: componente por emisiones de CO2, nafta Súper 95", base="tonelada de CO2 emitida", monto=7006, unidad_monto="UYU por tonelada (14,36 por litro)", vigencia="desde ene-2026", src="DO_20260114"),
    r("combustibles: componente por emisiones de CO2, nafta Premium 97", base="tonelada de CO2 emitida", monto=7006, unidad_monto="UYU por tonelada (14,43 por litro)", vigencia="desde ene-2026", src="DO_20260114"),
    r("alcohol carburante vendido a industrias para elaborar naftas", base="litro", monto=0, unidad_monto="UYU por litro", vigencia="desde ene-2026", src="DO_20260114"),
    r("tabacos (paquete de 45 g)", base="base específica $71,24", tasa=70, monto=49.87, unidad_monto="UYU por paquete", vigencia="desde ene-2026", src="DO_20260114", notas="Dec. 345/025"),
    r("cigarrillos (cajilla de 20)", base="base específica $159,94", tasa=70, monto=111.96, unidad_monto="UYU por cajilla", vigencia="desde ene-2026", src="DO_20260114", notas="incluye free shop"),
    r("lubricantes, numeral 12", base="base específica $159,13 por litro", tasa=39, monto=62.06, unidad_monto="UYU por litro", vigencia="desde ene-2026", src="DO_20260114"),
    r("grasas, numeral 12", base="base específica $207,90 por kilo", tasa=39, monto=81.08, unidad_monto="UYU por kilo", vigencia="desde ene-2026", src="DO_20260114"),
    r("lubricantes, numeral 13", base="base específica $159,13 por litro", tasa=2.5, monto=3.98, unidad_monto="UYU por litro", vigencia="desde ene-2026", src="DO_20260114"),
    r("grasas, numeral 13", base="base específica $207,90 por kilo", tasa=2.5, monto=5.20, unidad_monto="UYU por kilo", vigencia="desde ene-2026", src="DO_20260114"),
    r("bebidas alcohólicas: tope legal", base="precio de primera enajenación (o ficto)", tasa=85, vigencia=V26, confianza=G, src="UXXI"),
    r("nafta refinada: tope legal", base="precio de venta", tasa=133, vigencia=V26, confianza=G, src="UXXI"),
    r("otras bebidas sin alcohol: tope legal", base="precio de primera enajenación", tasa=30, vigencia="2024", confianza=SEC, src="TODGI_T11"),
    r("cosméticos y perfumería", base="precio de primera enajenación", tasa=20, vigencia="2024", confianza=SEC, src="TODGI_T11", notas="texto del Título 11 citado por terceros"),
    r("vehículos nafta hasta 1.000 cc", base="valor en aduana / precio", tasa=23, vigencia="2025", confianza=SEC, src="CLASIAUTOS"),
    r("vehículos nafta 1.001 a 1.500 cc", base="valor en aduana / precio", tasa=28.75, vigencia="2025", confianza=SEC, src="CLASIAUTOS"),
    r("vehículos nafta 1.501 a 2.000 cc", base="valor en aduana / precio", tasa=34.5, vigencia="2025", confianza=SEC, src="CLASIAUTOS"),
    r("vehículos nafta más de 2.000 cc", base="valor en aduana / precio", tasa=46, vigencia="2025", confianza=SEC, src="CLASIAUTOS"),
    r("vehículos diésel", base="valor en aduana / precio", tasa=115, vigencia="2025", confianza=SEC, src="CLASIAUTOS"),
    r("vehículos eléctricos", base="valor en aduana", tasa=0, vigencia="hasta 2026", confianza=SEC, src="AUTOBLOG_EV"),
    r("vehículos eléctricos con valor en aduana hasta USD 19.000", base="valor en aduana", tasa=0, vigencia="desde 2027", confianza=SEC, src="AUTOBLOG_EV"),
    r("vehículos eléctricos con valor en aduana de USD 19.001 a 27.000", base="valor en aduana", tasa=5, vigencia="desde 2027", confianza=SEC, src="AUTOBLOG_EV"),
    r("vehículos eléctricos con valor en aduana mayor a USD 27.000", base="valor en aduana", tasa=9, vigencia="desde 2027", confianza=SEC, src="AUTOBLOG_EV"),
]

RATES["Impuesto a las Rentas de las Actividades Económicas"] = [
    r("tasa general", base="renta neta de fuente uruguaya", tasa=25, vigencia=V26, confianza=G, src="UXXI"),
    r("trading de mercaderías sin pasaje por Uruguay o intermediación de servicios en el exterior (opcional)", base="3% del margen bruto", tasa=25, vigencia=V26, confianza=G, src="UXXI", notas="tasa efectiva 0,75% del margen"),
    r("transporte internacional", base="10% de pasajes y fletes del país al exterior", tasa=25, vigencia=V26, confianza=G, src="UXXI"),
    r("agencias de noticias internacionales", base="10% de la retribución bruta", tasa=25, vigencia=V26, confianza=G, src="UXXI"),
    r("cesión de contenedores para comercio internacional", base="15% del precio", tasa=25, vigencia=V26, confianza=G, src="UXXI"),
    r("enajenación de participaciones de no residentes con activos en Uruguay (personas físicas y no residentes)", base="ficto 2,4% del precio de venta", vigencia=V26, confianza=G, src="UXXI"),
    r("pequeñas empresas (literal E)", base="ingresos anuales", desde=0, hasta=305000, unidad_tramo="UI", tasa=0, vigencia=V26, confianza=SEC, src="RSM_IVAMIN", notas="exoneradas de IRAE; pagan IVA mínimo"),
    r("anticipo en la importación de bienes de consumo del anexo (lista por código en ../aranceles/arancel.csv)", base="valor en aduana más arancel", tasa=4, vigencia="desde 2026", src="MEF_IRAE_ANT", notas="pago a cuenta del IRAE, no impuesto adicional"),
    r("productores agropecuarios: IRAE obligatorio en vez de IMEBA", base="ingresos del ejercicio anterior", desde=2500000, unidad_tramo="UI", tasa=25, vigencia=V26, confianza=G, src="UXXI", notas="también si explotan más de 1.250 ha CONEAT o son SA, SCA, establecimientos permanentes o fideicomisos"),
]

_IRPF_ANUAL = brackets("Categoría II, rentas del trabajo (escala anual)", "renta anual del trabajo", "BPC",
                       [84, 120, 180, 360, 600, 900, 1380], [0, 10, 15, 24, 25, 27, 31, 36], "UXXI", V26, G)
_IRPF_MES = brackets("Categoría II, anticipo mensual por retención", "renta mensual computable", "BPC",
                     [7, 10, 15, 30, 50, 75, 115], [0, 10, 15, 24, 25, 27, 31, 36], "UXXI", V26, G)
RATES["Impuesto a la Renta de las Personas Físicas"] = _IRPF_ANUAL + _IRPF_MES + [
    r("Categoría II, tasa de deducciones con ingreso nominal anual hasta 180 BPC", base="total de deducciones", desde=0, hasta=180, unidad_tramo="BPC", tasa=14, vigencia=V26, confianza=G, src="UXXI", notas="se resta del impuesto; mensual: hasta 15 BPC"),
    r("Categoría II, tasa de deducciones con ingreso nominal anual mayor a 180 BPC", base="total de deducciones", desde=180, unidad_tramo="BPC", tasa=8, vigencia=V26, confianza=G, src="UXXI"),
    r("deducción por hijo menor a cargo", monto=20, unidad_monto="BPC anuales por hijo", vigencia=V26, confianza=G, src="UXXI", notas="se duplica para hijos con discapacidad"),
    r("deducción por cuota de préstamo hipotecario de vivienda única (costo hasta 794.000 UI)", monto=36, unidad_monto="BPC anuales (tope)", vigencia=V26, confianza=G, src="UXXI"),
    r("crédito por arrendamiento de vivienda permanente", base="precio del arrendamiento", tasa=6, vigencia=V26, confianza=G, src="UXXI"),
    r("trabajo fuera de relación de dependencia: ficto de gastos", base="ingresos", tasa=30, vigencia=V26, confianza=G, src="UXXI", notas="porcentaje deducible, no tasa del impuesto"),
    r("retención a no dependientes cuando la facturación mensual al responsable supera 10.000 UI", base="monto pagado más retención", desde=10000, unidad_tramo="UI por mes", tasa=7, vigencia=V26, confianza=G, src="UXXI"),
    r("Categoría I: depósitos en pesos a tasa fija, hasta 1 año", base="intereses", tasa=5.5, vigencia=V26, confianza=SEC, src="CAMBIO"),
    r("Categoría I: depósitos en pesos a tasa fija, 1 a 3 años", base="intereses", tasa=2.5, vigencia=V26, confianza=SEC, src="CAMBIO"),
    r("Categoría I: depósitos en pesos a tasa fija, más de 3 años", base="intereses", tasa=0.5, vigencia=V26, confianza=SEC, src="CAMBIO"),
    r("Categoría I: depósitos en pesos reajustables (UI), hasta 1 año", base="intereses", tasa=10, vigencia=V26, confianza=SEC, src="CAMBIO"),
    r("Categoría I: depósitos en pesos reajustables (UI), 1 a 3 años", base="intereses", tasa=7, vigencia=V26, confianza=SEC, src="CAMBIO"),
    r("Categoría I: depósitos en pesos reajustables (UI), más de 3 años", base="intereses", tasa=5, vigencia=V26, confianza=SEC, src="CAMBIO"),
    r("Categoría I: depósitos en moneda extranjera, hasta 3 años", base="intereses", tasa=12, vigencia=V26, confianza=SEC, src="CAMBIO"),
    r("Categoría I: depósitos en moneda extranjera, más de 3 años", base="intereses", tasa=7, vigencia=V26, confianza=SEC, src="CAMBIO"),
    r("Categoría I: dividendos de contribuyentes de IRAE (incluye fictos)", base="dividendo", tasa=7, vigencia=V26, confianza=G, src="UXXI"),
    r("Categoría I: alquileres", base="renta neta", tasa=12, vigencia=V26, confianza=SEC, src="CAMBIO", notas="la retención sobre el bruto es 10,5%; exonerados si las rentas no superan 40 BPC anuales"),
    r("Categoría I: incrementos patrimoniales (régimen real)", base="precio menos costo fiscal actualizado", tasa=12, vigencia=V26, confianza=SEC, src="CAMBIO"),
    r("Categoría I: incrementos patrimoniales, inmuebles no rurales comprados antes de 1/7/2007 (opcional)", base="15% del precio", tasa=12, vigencia=V26, confianza=SEC, src="CAMBIO", notas="tasa efectiva 1,8%"),
    r("Categoría I: incrementos patrimoniales sin costo probado o bienes en el exterior (ficto)", base="20% del precio", tasa=12, vigencia=V26, confianza=SEC, src="CAMBIO", notas="tasa efectiva 2,4%"),
    r("Categoría I: exoneración de operaciones chicas", base="precio de cada operación", hasta=30000, unidad_tramo="UI", tasa=0, vigencia=V26, confianza=SEC, src="CAMBIO", notas="y la suma anual menor a 90.000 UI"),
    r("Categoría I: rentas de capital del exterior (desde 2026)", base="renta", tasa=12, vigencia=V26, confianza=G, src="UXXI", notas="retención de 8% si opera un bróker local con custodia"),
    r("Categoría I: premios de juegos de azar y carreras", base="premio menos apuesta", tasa=12, vigencia="desde 2018", confianza=SEC, src="FOCUS_APUESTAS", notas="Ley 19.535; exoneraciones por monto a verificar"),
    r("nuevos residentes desde 2026, tras los 11 años de régimen IRNR: opción A por 5 años", base="rentas de capital del exterior", tasa=6, vigencia=V26, confianza=G, src="UXXI"),
    r("nuevos residentes desde 2026, tras los 11 años: opción B por 20 años", monto=1875000, unidad_monto="UI anuales", vigencia=V26, confianza=G, src="UXXI", notas="1.250.000 UI si permanece más de 183 días en el país"),
]

RATES["Impuesto a las Rentas de los No Residentes"] = [
    r("dividendos de contribuyentes de IRAE (incluye fictos)", base="dividendo", tasa=7, vigencia=V26, confianza=G, src="UXXI"),
    r("intereses de depósitos y títulos: misma tabla por moneda y plazo que IRPF Categoría I", base="intereses", desde=0.5, hasta=12, unidad_tramo="% (rango)", vigencia=V26, confianza=G, src="UXXI"),
    r("entidades de países de baja o nula tributación: rentas de inmuebles en Uruguay", base="renta", tasa=30.25, vigencia=V26, confianza=G, src="UXXI"),
    r("entidades de países de baja o nula tributación: restantes rentas (salvo dividendos)", base="renta", tasa=25, vigencia=V26, confianza=G, src="UXXI"),
    r("restantes rentas", base="renta", tasa=12, vigencia=V26, confianza=G, src="UXXI"),
    r("trabajadores extranjeros de zona franca o régimen de talento calificado (opción)", base="rentas del trabajo dependiente", tasa=12, vigencia=V26, confianza=G, src="UXXI", notas="sustituye IRPF y aportes a la seguridad social"),
    r("exoneración de transmisiones chicas", base="precio de cada operación", hasta=30000, unidad_tramo="UI", tasa=0, vigencia=V26, confianza=G, src="UXXI", notas="y la suma anual hasta 90.000 UI"),
]

RATES["Impuesto de Asistencia a la Seguridad Social"] = (
    brackets("escala anual", "jubilaciones y pensiones anuales", "BPC", [108, 180, 600], [0, 6, 24, 30], "CAMBIO", V26, SEC)
    + brackets("escala mensual (retención)", "jubilaciones y pensiones mensuales", "BPC", [9, 15, 50], [0, 6, 24, 30], "ELOBS_IRPF", V26, SEC))

RATES["Impuesto a la Enajenación de Bienes Agropecuarios"] = [
    r("lana y cueros ovinos y bovinos", base="precio de primera enajenación", tasa=2.5, vigencia=V26, src="DEC21_2026"),
    r("ganado bovino y ovino", base="precio de primera enajenación", tasa=2, vigencia=V26, src="DEC21_2026"),
    r("ganado suino, avicultura, cunicultura, flores y semillas", base="precio de primera enajenación", tasa=1.5, vigencia=V26, confianza=SEC, src="DEC21_2026", notas="resumen de terceros del art. 6"),
    r("leche", base="precio de primera enajenación", tasa=1.1, vigencia=V26, src="DEC21_2026"),
    r("cereales y oleaginosos", base="precio de primera enajenación", tasa=0.1, vigencia=V26, src="DEC21_2026"),
    r("leche artesanal de pequeños productores fuera de IRAE con remisión menor a 500 litros diarios", base="precio", tasa=0.1, vigencia=V26, src="DEC21_2026"),
]
RATES["Adicional IMEBA (MEVIR)"] = [
    r("lana, cueros, ganado bovino y ovino, cereales y oleaginosos", base="precio de enajenación", tasa=0.2, vigencia=V26, confianza=G, src="UXXI"),
]
RATES["Adicional IMEBA (INIA)"] = [
    r("lana, cueros, ganado en pie, cereales y oleaginosos, leche, avicultura y apicultura, productos forestales, exportación en estado natural de hortalizas, frutas, cítricos, flores y semillas", base="precio de enajenación", tasa=0.4, vigencia=V26, confianza=G, src="UXXI"),
]

_IP_NR = brackets("personas físicas no residentes (sin IRNR)", "patrimonio gravado", "veces el mínimo no imponible",
                  [1, 2, 4], [0.7, 1.1, 1.4, 1.5], "CAMBIO", "2025", SEC)
RATES["Impuesto al Patrimonio"] = [
    r("personas jurídicas", base="activos en el país menos pasivos admitidos", tasa=1.5, vigencia=V26, confianza=G, src="UXXI"),
    r("bancos y casas financieras", base="activos en el país menos pasivos admitidos", tasa=2.8, vigencia=V26, confianza=G, src="UXXI"),
    r("entidades de países de baja o nula tributación", base="bienes en el país", tasa=3, vigencia=V26, confianza=G, src="UXXI"),
    r("explotaciones agropecuarias hasta 12.000.000 UI", base="patrimonio agropecuario", hasta=12000000, unidad_tramo="UI", tasa=0, vigencia=V26, confianza=G, src="UXXI", notas="exoneración con condiciones"),
    r("explotaciones agropecuarias de 12.000.000 a 30.000.000 UI", base="patrimonio agropecuario", desde=12000000, hasta=30000000, unidad_tramo="UI", tasa=0.75, vigencia=V26, confianza=G, src="UXXI"),
    r("explotaciones agropecuarias de más de 30.000.000 UI", base="patrimonio agropecuario", desde=30000000, unidad_tramo="UI", tasa=1.5, vigencia=V26, confianza=G, src="UXXI"),
    r("personas físicas residentes", base="patrimonio que excede el mínimo no imponible", tasa=0.1, vigencia="2025", confianza=SEC, src="CAMBIO", notas="escala abatida hasta la tasa plana de 0,1%"),
    r("mínimo no imponible persona física 2025", monto=6653000, unidad_monto="UYU", vigencia="2025", src="DEC334", notas="núcleo familiar: 13.306.000"),
] + _IP_NR
RATES["Sobretasa del Impuesto al Patrimonio"] = [
    r("explotaciones agropecuarias que superan 12.000.000 UI", base="totalidad del patrimonio agropecuario", desde=0.7, hasta=1.5, unidad_tramo="% (rango según valor)", vigencia=V26, confianza=G, src="UXXI"),
]
RATES["Impuesto de Control de las Sociedades Anónimas"] = [
    r("constitución de la sociedad anónima", base="monto ficto", tasa=1.5, monto=578428, unidad_monto="UI (base)", vigencia=V26, confianza=G, src="UXXI"),
    r("cierre de cada ejercicio", base="monto ficto", tasa=0.75, monto=578428, unidad_monto="UI (base)", vigencia=V26, confianza=G, src="UXXI", notas="imputable al Impuesto al Patrimonio"),
]
RATES["Impuesto de Enseñanza Primaria"] = brackets(
    "inmuebles urbanos y suburbanos", "valor real catastral", "UYU",
    [282612, 494568, 2119563, 4945638], [0, 0.15, 0.2, 0.25, 0.3], "MEMORY_IEP", V26, SEC) + [
    r("inmuebles rurales con explotación agropecuaria", base="valor catastral e índice CONEAT por padrón", vigencia=V26, confianza="sin_datos", src="DGI_IEP_RURAL", notas="la DGI publica una planilla de cálculo; exonerados quienes exploten hasta 300 ha CONEAT 100"),
]
RATES["Impuesto a las Trasmisiones Patrimoniales"] = [
    r("enajenación de inmuebles: enajenante", base="valor real catastral", tasa=2, vigencia=V26, confianza=G, src="UXXI"),
    r("enajenación de inmuebles: adquirente", base="valor real catastral", tasa=2, vigencia=V26, confianza=G, src="UXXI"),
    r("transferencia sin contraprestación: beneficiario", base="valor real catastral", tasa=4, vigencia=V26, confianza=G, src="UXXI"),
    r("herencia en línea recta ascendente o descendente", base="valor real catastral", tasa=3, vigencia=V26, confianza=G, src="UXXI"),
]
RATES["Adicional del Impuesto a las Trasmisiones Patrimoniales"] = nodata("figura en el boletín DGI 2023 con recaudación 0")
RATES["Impuesto a la Apuesta"] = [
    r("apuestas en máquinas electrónicas de casinos y salas", base="monto apostado", tasa=0.75, vigencia="2018-2025", confianza=SEC, src="DEC359", notas="Dec. 359/017 derogado por Dec. 167/025; tasa actual a verificar"),
]
RATES["Impuesto a los Ingresos de las Entidades Aseguradoras"] = [
    r("seguros generales, incendio y vehículos", base="ingresos brutos por primas", tasa=7, vigencia=V26, src="DEC255"),
    r("seguros de vida", base="ingresos brutos por primas", tasa=0, vigencia=V26, src="DEC255"),
    r("aseguradora no autorizada a operar en el país", base="tasa del ramo", tasa=40, vigencia=V26, src="DEC255", notas="incremento porcentual sobre la tasa del ramo"),
]
RATES["Impuestos para el Fondo de Inspección Sanitaria"] = [
    r("exportación de bovinos y ovinos en pie y de carne (salvo conservas)", base="valor exportado", tasa=1, vigencia=V26, src="DEC152"),
    r("carne vacuna y ovina destinada al consumo interno", base="precio", tasa=1, vigencia="1970", confianza=SEC, src="LEY13892", notas="tasa de la ley original de 1970; la vigente está en el Dec. 152/025, sin verificar"),
]
RATES["Detracciones a la exportación"] = [
    r("cueros bovinos sin terminar (subpartidas 41.04.11 y 41.04.19)", base="valor exportado", tasa=5, vigencia="base legal", confianza=SEC, src="DETRAC", notas="decretos sucesivos la bajan a 0% por 6 meses; situación en 2026 a verificar"),
]

_MONO = "aporte mensual total al BPS"
RATES["Monotributo"] = [
    r("unipersonal sin cobertura FONASA, inicio de actividad antes de 2021", monto=2637, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO18083"),
    r("unipersonal con FONASA, sin cónyuge y con hijos, inicio antes de 2021", monto=6996, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO18083"),
    r("unipersonal con FONASA, con cónyuge y con hijos, inicio antes de 2021", monto=7888, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO18083"),
    r("sociedad de hecho, por socio, inicio antes de 2021", monto=2088, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO18083"),
    r("unipersonal sin FONASA, inicio desde 2021, primeros 12 meses", monto=1071, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO19942"),
    r("unipersonal sin FONASA, inicio desde 2021, meses 13 a 24", monto=1594, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO19942"),
    r("unipersonal sin FONASA, inicio desde 2021, desde el mes 25", monto=2637, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO19942"),
    r("unipersonal con FONASA, sin cónyuge y con hijos, inicio desde 2021, primeros 12 meses", monto=5430, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO19942"),
    r("unipersonal con FONASA, sin cónyuge y con hijos, inicio desde 2021, meses 13 a 24", monto=5953, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO19942"),
    r("unipersonal con FONASA, sin cónyuge y con hijos, inicio desde 2021, desde el mes 25", monto=6996, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO19942"),
    r("sociedad de hecho, por socio, inicio desde 2021, primeros 12 meses", monto=522, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO19942"),
    r("sociedad de hecho, por socio, inicio desde 2021, meses 13 a 24", monto=1045, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO19942"),
    r("sociedad de hecho, por socio, inicio desde 2021, desde el mes 25", monto=2088, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MONO19942"),
]
RATES["Monotributo Social MIDES"] = [
    r(f"titular sin Seguro Nacional de Salud, {tramo}", base="5 BFC ($ 9.240)", monto=m, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MIDES",
      notas="incluye 8% sobre 1 BPC de seguro de enfermedad")
    for tramo, m in [("meses 1 a 12 (25%)", 659), ("meses 13 a 24 (50%)", 1320), ("meses 25 a 36 (75%)", 1979), ("desde el mes 37 (100%)", 2637)]
] + [
    r(f"titular con Seguro Nacional de Salud, sin cónyuge y con hijos, {tramo}", base="5 BFC ($ 9.240)", monto=m, unidad_monto=_MONO, vigencia="ene-2026", src="BPS_MIDES")
    for tramo, m in [("meses 1 a 12 (25%)", 5430), ("meses 13 a 24 (50%)", 5953), ("meses 25 a 36 (75%)", 6475), ("desde el mes 37 (100%)", 6996)]
]
RATES["Aporte Social Único de Personas Privadas de Libertad"] = nodata()

RATES["Tasa Global Arancelaria (Arancel Externo Común)"] = [
    r("importaciones desde el Mercosur", base="valor en aduana (CIF)", tasa=0, vigencia=V26, src="DEC426"),
    r("importaciones extrazona: según posición arancelaria", base="valor en aduana (CIF)", desde=0, hasta=35, unidad_tramo="% (rango)", vigencia="feb-2025", src="MEF_ARANCEL", notas="tasa por código de 10 dígitos en ../aranceles/arancel.csv"),
]
RATES["Recargos a la importación"] = nodata()
RATES["Tasa Consular"] = [
    r("importaciones extrazona de bienes de consumo", base="valor CIF", tasa=5, vigencia="desde 2018", confianza=SEC, src="AUTOBLOG_TC", notas="0% para bienes de capital, petróleo crudo y admisión temporaria"),
    r("importaciones desde el Mercosur", base="valor CIF", tasa=3, vigencia="desde 2018", confianza=SEC, src="AUTOBLOG_TC"),
    r("dato discrepante en guía de 2026", base="valor FOB", tasa=2, vigencia=V26, confianza=SEC, src="YOFACT_IMPORT", notas="contradice la fila anterior; verificar con la DNA"),
]
RATES["Tasa por Servicios Preferenciales"] = [
    r("permiso de importación", base="valor CIF", tasa=0.2, monto=50, unidad_monto="USD tope", vigencia=V26, src="DNA_PREF"),
]
RATES["Tasa de Inspección No Intrusiva"] = [
    r("cada DUA o mensaje simplificado", monto=85, unidad_monto="UI máximo por declaración", vigencia="desde 2/10/2024", src="DEC235", notas="exentos envíos aéreos de hasta 20 kg y USD 200"),
]
RATES["Tasa de Servicios Aduaneros / servicios extraordinarios"] = nodata()
RATES["IVA a la importación"] = [
    r("tasa básica", base="CIF más arancel (y más IMESI según el caso)", tasa=22, vigencia=V26, confianza=SEC, src="COMEX", notas="las guías no coinciden sobre si la base incluye el IMESI"),
    r("tasa mínima", base="ídem", tasa=10, vigencia=V26, confianza=SEC, src="COMEX"),
]
RATES["IMESI a la importación"] = [
    r("mismas tasas que el IMESI interno", base="valor en aduana", vigencia=V26, confianza=G, src="UXXI", notas="ver Impuesto Específico Interno"),
]
RATES["Prestación para el LATU sobre exportaciones no tradicionales"] = [
    r("exportaciones no tradicionales", base="valor en aduana", tasa=0.2, vigencia=V26, src="LEY20446", notas="2 por mil, pagado en el BROU al liquidar el cumplido de embarque"),
]
RATES["Tributo único a envíos postales y express"] = [
    r("envíos de hasta 20 kg y factura de hasta USD 800, opcional", base="valor facturado o declarado", tasa=60, monto=20, unidad_monto="USD mínimo por envío", vigencia="desde 23/3/2026", src="DEC50", notas="sustituye aranceles y tributos internos; comparación con 2024 en ../aranceles/regimen-envios/"),
    r("régimen anterior: envíos de hasta USD 200", base="valor facturado o declarado", tasa=60, monto=10, unidad_monto="USD mínimo por envío", vigencia="2016 a 22/3/2026", src="ADU2015", notas="Decreto 356/014 modificado; ver ../aranceles/regimen-envios/"),
]

RATES["Aportes jubilatorios personales"] = [
    r("Industria y Comercio, trabajo doméstico y civil", base="remuneración gravada", tasa=15, vigencia="desde 1/7/2007", src="BPS_TASAS"),
    r("tope A (art. 7 y 8 Ley 16.713)", monto=96279, unidad_monto="UYU mensuales", vigencia="oct-2026", src="BPS_VALORES"),
    r("tope B", monto=144418, unidad_monto="UYU mensuales", vigencia="oct-2026", src="BPS_VALORES"),
    r("tope C", monto=288836, unidad_monto="UYU mensuales", vigencia="oct-2026", src="BPS_VALORES"),
]
RATES["Aportes jubilatorios patronales"] = [
    r("Industria y Comercio y trabajo doméstico", base="remuneración gravada", tasa=7.5, vigencia="desde 1/7/2007", src="BPS_TASAS", notas="en la aportación civil varía por organismo"),
]
RATES["Aportes por servicios bonificados"] = [
    r("actividades con riesgo para la vida o la integridad del trabajador", base="remuneración gravada", desde=6.9, hasta=27.5, unidad_tramo="% (rango según actividad)", vigencia="2024", src="BPS_BONIF", notas="aporte patronal"),
]
RATES["Aportes al FONASA (personal y patronal)"] = [
    r("patronal", base="remuneración gravada", tasa=5, vigencia=V26, src="BPS_FONASA", notas="más complemento de cuota mutual si corresponde"),
] + [
    r(f"personal, remuneración hasta 2,5 BPC, {sit}", base="remuneración gravada", desde=0, hasta=2.5, unidad_tramo="BPC mensuales", tasa=t, vigencia=V26, src="BPS_FONASA")
    for sit, t in [("sin cónyuge, sin hijos", 3), ("sin cónyuge, con hijos", 3), ("con cónyuge, sin hijos", 5), ("con cónyuge, con hijos", 5)]
] + [
    r(f"personal, remuneración mayor a 2,5 BPC, {sit}", base="remuneración gravada", desde=2.5, unidad_tramo="BPC mensuales", tasa=t, vigencia=V26, src="BPS_FONASA")
    for sit, t in [("sin cónyuge, sin hijos", 4.5), ("sin cónyuge, con hijos", 6), ("con cónyuge, sin hijos", 6.5), ("con cónyuge, con hijos", 8)]
] + [
    r("valor de la cuota mutual", monto=1880, unidad_monto="UYU mensuales", vigencia="oct-2026", src="BPS_VALORES"),
]
RATES["Fondo de Reconversión Laboral"] = [
    r("personal, dependientes y no dependientes", base="remuneración gravada", tasa=0.1, vigencia="desde 2019", src="BPS_FRL"),
    r("patronal, dependientes", base="remuneración gravada", tasa=0.1, vigencia="desde 2019", src="BPS_FRL"),
]
RATES["Fondo de Garantía de Créditos Laborales"] = [
    r("patronal, trabajadores dependientes de la actividad privada", base="remuneración gravada", tasa=0.025, vigencia="desde 2019", src="BPS_FGCL"),
]
RATES["Aporte Unificado de la Construcción"] = [
    r(f"construcción: {c}", base="remuneración gravada del personal de obra", tasa=t, vigencia=V26, src="BPS_CONST")
    for c, t in [("contribuciones patronales a la seguridad social", 9), ("contribuciones personales a la seguridad social", 17.9),
                 ("cargas salariales", 29.9), ("Seguro Nacional de Salud", 9), ("seguro de accidentes BSE", 6), ("total aporte unificado", 71.8)]
] + [
    r("partidas del art. 167 Ley 16.713 (alimentación, salud, seguros, transporte)", base="partidas", tasa=7.5, vigencia=V26, src="BPS_CONST", notas="fuera del aporte unificado"),
]
RATES["Aporte a la Caja de Profesionales sobre obras de construcción"] = [
    r("obras de arquitectura", base="monto imponible de la obra", tasa=4, vigencia=V26, src="BPS_CONST", notas="Ley 17.738; se paga con el aporte unificado"),
    r("obras de ingeniería", base="monto imponible de la obra", tasa=2, vigencia=V26, src="BPS_CONST"),
]
RATES["Fondo de Cesantía y Retiro de la Construcción"] = [
    r("patronal", base="remuneración", tasa=5, vigencia=V26, src="BPS_FOCER", notas="5% o 0,5% según la situación del trabajador"),
    r("patronal, caso reducido", base="remuneración", tasa=0.5, vigencia=V26, src="BPS_FOCER"),
    r("personal", base="remuneración", tasa=0.5, vigencia=V26, src="BPS_FOCER", notas="según modalidad de trabajo"),
]
RATES["Fondo Social de la Construcción"] = [
    r("patronal", base="remuneración", tasa=1.2691, vigencia="desde 2014", src="BPS_FSC"),
    r("personal", base="remuneración", tasa=0.5809, vigencia="desde 2014", src="BPS_FSC"),
]
RATES["Fondo Social de Vivienda de la Construcción"] = [
    r("patronal", base="remuneración", tasa=0.025, vigencia="desde 2009", src="BPS_FOSVOC"),
    r("personal", base="remuneración", tasa=0.025, vigencia="desde 2009", src="BPS_FOSVOC"),
]
RATES["Fondo de la Industria Gráfica"] = [
    r("personal, dependientes y no dependientes del grupo 36", base="remuneración", tasa=1.15, vigencia="desde 2000", src="BPS_GRAF"),
]
RATES["Fondo Social Metalúrgico"] = [
    r("patronal, subgrupos del grupo 8", base="remuneración gravada", tasa=0.86, vigencia="desde 2017", src="BPS_FOSMETAL"),
    r("personal", base="remuneración gravada", tasa=0.39, vigencia="desde 2017", src="BPS_FOSMETAL"),
]
RATES["Fondo Social del Trabajo Doméstico"] = [
    r("patronal (voluntario)", base="remuneración gravada", tasa=0.03, vigencia="desde 2016", src="BPS_DOMFONDO"),
    r("personal (voluntario)", base="remuneración gravada", tasa=0.03, vigencia="desde 2016", src="BPS_DOMFONDO"),
]
RATES["Aporte rural (contribución patronal rural)"] = [
    r("empresas rurales con explotación: unidad básica de contribución", base="BPC por hectárea CONEAT", tasa=0.1004, monto=6.89, unidad_monto="UYU por ha CONEAT al mes", vigencia="2.º cuatrimestre 2026", src="BPS_RURALMIN"),
    r("predios sin explotación", base="BPC por hectárea CONEAT", tasa=0.1506, monto=10.34, unidad_monto="UYU por ha CONEAT al mes", vigencia="2.º cuatrimestre 2026", src="BPS_RURALMIN"),
    r("aporte mínimo (15% de 22 BFC por 0,67)", monto=4086, unidad_monto="UYU mensuales", vigencia="2.º cuatrimestre 2026", src="BPS_RURALMIN"),
    r("contratistas rurales", base="suma de montepíos (15%) de sus dependientes", tasa=-12.99, vigencia="desde 2020", src="BPS_RURAL", notas="la suma se reduce 12,99%"),
    r("acrecimiento en empresas pluripersonales", base="contribución patronal rural", tasa=10, vigencia=V26, src="BPS_RURAL", notas="10% por los primeros tres integrantes y 10% más por cada uno adicional"),
]
RATES["Impuesto MEVIR rural (BPS)"] = [
    r("empresas rurales con más de 500 ha CONEAT", base="hectáreas CONEAT", desde=500, unidad_tramo="ha CONEAT", monto="UR/1000", unidad_monto="por ha CONEAT al trimestre", vigencia=V26, src="BPS_MEVIR"),
]
RATES["Aportes del servicio doméstico"] = [
    r("jubilatorio personal", base="remuneración gravada", tasa=15, vigencia=V26, src="BPS_TASAS"),
    r("jubilatorio patronal", base="remuneración gravada", tasa=7.5, vigencia=V26, src="BPS_TASAS"),
    r("FONASA, FRL y fondo social", base="remuneración gravada", vigencia=V26, src="BPS_TASAS", notas="mismas tasas del régimen general; ver sus archivos"),
]
_CJPPU_17738 = [("1 especial (bonificada)", 3802), ("1", 7566), ("2", 14312), ("3", 20283), ("4", 25444), ("5", 29791),
                ("6", 33372), ("7", 36174), ("8", 38150), ("9", 39349), ("10", 39734)]
_CJPPU_20410 = [("1 especial (bonificada)", 3430), ("1", 6828), ("2", 12917), ("3", 18305), ("4", 22960), ("5", 26885),
                ("6", 30116), ("7", 32644), ("8", 34428), ("9", 35510), ("10", 35858)]
_CJPPU_15 = [("1 especial (bonificada)", 3802), ("1", 7566), ("2", 8701), ("3", 10876), ("4", 13051), ("5", 15662), ("6", 18011),
             ("7", 19812), ("8", 22785), ("9", 25063), ("10", 26816), ("11", 28426), ("12", 29847), ("13", 31041), ("14", 32283), ("15", 33574)]
RATES["Aportes a la Caja de Profesionales Universitarios"] = [
    r(f"escala de 10 categorías (Ley 17.738), categoría {c}", monto=m, unidad_monto="UYU mensuales", vigencia="2026", src="BPS_R5_2026") for c, m in _CJPPU_17738
] + [
    r(f"ficto reducido o ajustado (Ley 20.410), categoría {c}", monto=m, unidad_monto="UYU mensuales", vigencia="2026", src="BPS_R5_2026") for c, m in _CJPPU_20410
] + [
    r(f"escala de 15 categorías (Ley 17.738), categoría {c}", monto=m, unidad_monto="UYU mensuales", vigencia="2026", src="BPS_R5_2026") for c, m in _CJPPU_15
] + [
    r("aporte sobre sueldo ficto de la categoría", base="sueldo ficto", tasa=20.5, vigencia=V26, confianza=SEC, src="CALCULAME_CJ", notas="Ley 20.410"),
    r("ídem", base="sueldo ficto", tasa=21.5, vigencia="2027", confianza=SEC, src="CALCULAME_CJ"),
    r("ídem", base="sueldo ficto", tasa=22.5, vigencia="2028", confianza=SEC, src="CALCULAME_CJ"),
]
RATES["Timbre Profesional"] = [
    r("trámites ATyR", monto=270, unidad_monto="UYU por timbre", vigencia="oct-2026", src="BPS_VALORES"),
    r("lentes", monto=44, unidad_monto="UYU por timbre", vigencia="oct-2026", src="BPS_VALORES"),
    r("prótesis", monto=170, unidad_monto="UYU por timbre", vigencia="oct-2026", src="BPS_VALORES"),
]
RATES["Aportes a la Caja Notarial"] = [
    r("actuaciones notariales", base="honorario de arancel", tasa=19, vigencia=V26, confianza=SEC, src="CNOT"),
]
RATES["Aportes a la Caja Bancaria"] = [
    r("personal, afiliados de instituciones de los literales A) a E) y J) del art. 3 y la propia Caja", base="asignaciones computables", tasa=17.5, vigencia="desde 2009", src="LEY18396"),
    r("personal, afiliados de instituciones de los literales F) a I) del art. 3", base="asignaciones computables", tasa=15, vigencia="desde 2009", src="LEY18396"),
    r("patronal básico, instituciones de los literales A) a D) y la propia Caja", base="asignaciones computables", tasa=25.25, vigencia="desde 2009", src="LEY18396", notas="baja 0,45 puntos por año, hasta 4,5, cuando las reservas lleguen al 50% del presupuesto"),
    r("patronal básico, instituciones de los literales E) a J)", base="asignaciones computables", tasa=7.5, vigencia="desde 2009", src="LEY18396"),
    r("prestación complementaria, bancos y financieras (literales A y B)", base="activos propios en el país más activos netos en el exterior, saldo mensual", tasa=0.04, vigencia="desde 2009", src="LEY18396", notas="4 por diez mil; tasa máxima"),
    r("prestación complementaria, aseguradoras (literales C y D)", base="primas emitidas en el mes", tasa=1.4, vigencia="desde 2009", src="LEY18396", notas="14 por mil; tasa máxima"),
    r("prestación complementaria, literales F) a H)", base="activos propios en el país, saldo mensual", tasa=0.04, vigencia="desde 2009", src="LEY18396"),
    r("prestación complementaria, BCU, administradoras de ahorro previo e instituciones financieras externas", base="asignaciones computables", tasa=10, vigencia="desde 2009", src="LEY18396"),
    r("prestación complementaria, literal I)", base="ingresos mensuales sin IVA", tasa=0.2, vigencia="desde 2009", src="LEY18396", notas="20 por diez mil"),
    r("prestación complementaria, la propia Caja", base="asignaciones computables", tasa=5.5, vigencia="desde 2009", src="LEY18396"),
] + brackets("contribución de jubilados y pensionistas (régimen anterior)", "pasividad nominal mensual", "BPC",
             [6, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60], [0, 2, 7.5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20], "LEY18396", "desde 2009") + [
    r("recargo para pasividades mayores a 10 BPC", base="tasa de la escala", tasa=2, vigencia="desde 2010", src="LEY18396", notas="puntos porcentuales adicionales; bajan 0,4 por año según reservas"),
]
RATES["Aportes militares"] = [
    r("patronal", base="remuneración gravada", tasa=19.5, vigencia="desde 2019", src="LEY19695"),
    r("personal, en actividad", base="remuneración gravada", tasa=15, vigencia="desde 2019", src="LEY19695"),
    r("personal, retirados y reformados hasta 36 años de montepío", base="haber de retiro", tasa=13, vigencia="desde 2019", src="DEC161"),
]
RATES["Aportes policiales"] = [
    r("patronal de retiro", base="partidas gravadas", tasa=19.5, vigencia="desde 2009", src="LEY18405"),
    r("personal de retiro", base="partidas gravadas", tasa=15, vigencia="desde 2009", src="LEY18405"),
    r("contribución especial por servicios bonificados (Ministerio del Interior)", base="partidas gravadas", vigencia="desde 2009", confianza="sin_datos", src="LEY18405", notas="tasa fijada por el Poder Ejecutivo"),
]
RATES["Aporte al Fondo de Solidaridad"] = [
    r(f"categoría {c} (cuota mensual)", monto=m, unidad_monto="UYU mensuales", vigencia="2026", src="BPS_R5_2026", notas=n)
    for c, m, n in [("1: 0,5 BPC anuales", 286, ""), ("2: 1 BPC anual", 572, ""), ("3: 2 BPC anuales", 1144, ""),
                    ("4: 1 BPC más adicional de 5/6 BPC anuales", 1049, "incluye el adicional"), ("5: 2 BPC más adicional de 5/6 BPC anuales", 1621, "incluye el adicional")]
] + [
    r("carreras de menos de 4 años, 5 a 9 años desde el egreso", monto=0.5, unidad_monto="BPC anuales", src="LEY16524"),
    r("carreras de menos de 4 años, 10 o más años desde el egreso", monto=1, unidad_monto="BPC anuales", src="LEY16524"),
    r("carreras de 4 años o más, 5 a 9 años desde el egreso", monto=1, unidad_monto="BPC anuales", src="LEY16524"),
    r("carreras de 4 años o más, 10 o más años desde el egreso", monto=2, unidad_monto="BPC anuales", src="LEY16524"),
]
RATES["Adicional del Fondo de Solidaridad"] = [
    r("egresados de carreras de 5 o más años", monto="5/6", unidad_monto="BPC anuales", vigencia="2026", src="BPS_R5_2026", notas="sigue vigente en 2026 (BPS lo usa en las categorías 4 y 5)"),
    r("redacción original: egresados con ingresos mayores a 6 salarios mínimos", monto="5/3", unidad_monto="salarios mínimos anuales", vigencia="2001", confianza=SEC, src="MVD_FS", notas="Ley 17.296; reemplazado por el valor en BPC"),
]
RATES["Tasa de Control del Marco Regulatorio de Comunicaciones"] = [
    r("prestadores de servicios de comunicaciones (salvo radio y TV abierta)", base="ingresos brutos", tasa=0.3, src="LEY17820"),
]
RATES["Tasa de Control del Marco Regulatorio de Energía y Agua"] = [
    r("actividades reguladas de energía y agua", base="facturación", tasa=0.2, vigencia="2015", confianza=SEC, src="URSEA_MEM", notas="dato de la memoria anual 2015 de URSEA"),
]
RATES["Tasa de embarque aeroportuaria"] = [
    r("Carrasco: vuelos internacionales", monto=61, unidad_monto="USD por pasajero", vigencia=V26, src="CARRASCO", notas="incluida en el pasaje; exentos menores de 2 años, diplomáticos e invitados oficiales"),
    r("Carrasco: vuelos a Buenos Aires (Aeroparque)", monto=27, unidad_monto="USD por pasajero", vigencia=V26, src="CARRASCO"),
    r("Carrasco: vuelos nacionales", monto=5, unidad_monto="USD por pasajero", vigencia=V26, src="CARRASCO"),
    r("Carrasco: precio de seguridad", monto=9.57, unidad_monto="USD por pasajero", vigencia=V26, src="CARRASCO"),
    r("Punta del Este: vuelos internacionales", monto=42, unidad_monto="USD por pasajero", confianza=SEC, src="PDE_EMB"),
    r("Punta del Este: vuelos nacionales", monto=4, unidad_monto="USD por pasajero", confianza=SEC, src="PDE_EMB"),
]
RATES["Tasa de control del sistema financiero"] = [
    r("entidades supervisadas por el BCU: tope legal", base="promedio anual de activos o comisiones, según el sujeto", tasa=0.2, src="BCU_TASA", notas="2 por mil como máximo (Ley 18.083); alícuotas por tipo de entidad en el Dec. 795/008, no disponible; en 2025 el BCU propuso modificarla"),
]
RATES["Prestación INAC del 0,7% sobre carnes"] = [
    r("carnes vendidas en el mercado interno", base="precio de venta (precios fictos publicados por INAC)", tasa=0.7, src="DL15605", notas="Decreto-ley 15.605"),
]
RATES["Tasa de Control de Faena (INAC)"] = [
    r("faena de reses bovinas", base="cabezas faenadas", confianza="sin_datos", src="INAC_FAENA", notas="creada por el Dec. 364/003; monto no disponible"),
]
RATES["Impuesto Mínimo Complementario Doméstico"] = [
    r("grupos multinacionales con ingresos consolidados de 750 millones de euros o más", base="resultado neto admisible GloBE", tasa=15, vigencia="desde 2026", confianza=G, src="UXXI", notas="paga la diferencia entre 15% y la tasa efectiva local"),
]

RATES["Patente de Rodados"] = [
    r("autos 0 km", base="valor de mercado sin IVA", tasa=5, vigencia=V26, confianza=SEC, src="SUCIVE", notas="SUCIVE, igual en todo el país"),
    r("autos usados", base="valor de mercado al 30/09/2025", tasa=4.5, vigencia=V26, confianza=SEC, src="SUCIVE"),
    r("eléctricos 0 km", base="valor sin IVA", tasa=3, vigencia=V26, confianza=SEC, src="SUCIVE"),
    r("eléctricos usados", base="valor de mercado", tasa=2.25, vigencia=V26, confianza=SEC, src="SUCIVE", notas="El Observador cita 2,5%"),
    r("ómnibus, micros y furgones desafectados del servicio público", monto=22208.27, unidad_monto="UYU anuales", vigencia=V26, confianza=SEC, src="SUCIVE"),
]
RATES["Contribución Inmobiliaria Urbana y Suburbana"] = brackets(
    "Montevideo: escala progresiva", "valor imponible 2026", "UYU",
    [992630, 2481576, 4963144, 8551753, 17103509], [0.25, 0.75, 1, 1.2, 1.65, 1.8], "MVD_CI", V26) + [
    r("Montevideo: primer tramo para inmuebles con valor imponible menor a $2.481.577", base="valor imponible 2026", desde=0, hasta=992630, unidad_tramo="UYU", tasa=0.18, vigencia=V26, src="MVD_CI", notas="en lugar de 0,25%"),
    r("demás departamentos", confianza="sin_datos", notas="cada intendencia fija sus alícuotas"),
]
RATES["Adicionales municipales a la Contribución Inmobiliaria"] = [
    r("Montevideo: vivienda deshabitada al menos un año", base="Contribución Inmobiliaria", tasa=100, confianza=SEC, src="MVD_CI_PROP", notas="la IM propuso derogarlo desde 2027"),
]

RATES["Impuesto a la Compra de Moneda Extranjera"] = [
    r("compras de BCU, BROU y BHU para su actividad de cambio", base="monto comprado", tasa=0, vigencia="1994", src="DEC109"),
    r("compras de personas públicas estatales fuera de la actividad de cambio", base="erogaciones mensuales en moneda extranjera", tasa=2, vigencia="1994", src="DEC109"),
]

DEPARTAMENTAL_SIN_DATOS ="cada intendencia fija sus alícuotas; sin datos todavía"


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:70]


def main():
    path = HERE / "catalog.csv"
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    out = HERE / "rates"
    out.mkdir(exist_ok=True)
    unused = set(RATES)
    for row in rows:
        name = row["nombre"]
        if name in RATES:
            data = RATES[name]
            unused.discard(name)
        elif row["nivel"] == "departamental":
            data = nodata(DEPARTAMENTAL_SIN_DATOS)
        elif row["estado"] == "derogado":
            data = nodata("derogado; tasa histórica sin datos todavía")
        else:
            data = nodata()
        fname = f"{slug(name)}.csv"
        row["archivo"] = f"rates/{fname}"
        with open(out / fname, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            w.writerows(data)
    if unused:
        sys.exit(f"rates without catalog entry: {sorted(unused)}")
    written = {Path(row["archivo"]).name for row in rows}
    for stale in out.glob("*.csv"):
        if stale.name not in written:
            stale.unlink()
    fields = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "files written")


if __name__ == "__main__":
    main()
