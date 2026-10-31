"""Rebuild the rate files from the RATES table below, one per catalog.csv entry in its level folder, and fill catalog.csv's `archivo` column.

To change a rate, edit RATES and run: python3 build_rates.py (standard library only).
Catalog entries missing from RATES get a single `sin_datos` row.
"""
import csv

import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
COLS = ["departamento", "condicion", "base", "desde", "hasta", "unidad_tramo", "tasa_pct", "monto", "unidad_monto",
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
    "DO_20090128": "https://www.impo.com.uy/diariooficial/2009/01/28/documentos.pdf",
    "DO_20250820": "https://www.impo.com.uy/diariooficial/2025/08/20/documentos.pdf",
    "INAC_DEC364": "https://inac.uy/innovaportal/file/5562/1/decreto-364-003-del-4.3.2021.pdf",
    "INAC_DEC11": "https://inac.uy/innovaportal/file/5563/1/decreto-11-009.pdf",
    "VINALES": "https://www.cienciassociales.edu.uy/wp-content/uploads/2019/09/Evoluci%C3%B3n-sistema-tributario-1990-2018-Gustavo-Vi%C3%B1ales-v.-presen.pdf",
    "LEY17166": "https://uruguay.justia.com/nacionales/leyes/ley-17166-sep-10-1999/gdoc/",
    "DEC658": "https://www.impo.com.uy/bases/decretos/658-1992",
    "LEY18876": "https://impo.com.uy/bases/leyes/18876-2011",
    "BPS_PPL": "https://www.bps.gub.uy/19831/nuevo-regimen-de-aportes-para-emprendimientos-productivos-de-personas-privadas-de-libertad.html",
    "DEC122_2025": "https://www.impo.com.uy/bases/decretos/122-2025/1",
    "LEY18064": "https://uruguay.justia.com/nacionales/leyes/ley-18064-nov-27-2006/gdoc/",
    "LEY16624": "https://uruguay.justia.com/nacionales/leyes/ley-16624-nov-10-1994/gdoc/",
    "LEY17741": "https://uruguay.justia.com/nacionales/leyes/ley-17741-jan-10-2004/gdoc/",
    "LEY16757": "https://uruguay.justia.com/nacionales/leyes/ley-16757-jun-26-1996/gdoc/",
    "LEY18057": "https://uruguay.justia.com/nacionales/leyes/ley-18057-nov-20-2006/gdoc/",
    "LEY17663": "https://uruguay.justia.com/nacionales/leyes/ley-17663-jul-11-2003/gdoc/",
    "MVD_BAILES": "https://tramites.montevideo.gub.uy/tramites-y-tributos/solicitud/declaracion-de-espectaculos-publicos",
    "DGR_INSC": "https://www.gub.uy/tramites/inscripcion-actos-negocios-juridicos-decisiones-autoridades-competentes-sujetas-ley-publicidad-registral",
    "DGR_CERT": "https://www.gub.uy/tramites/certificados-informacion-inmuebles",
    "DNA_EXTRA": "https://www.aduanas.gub.uy/innovaportal/v/2772/8/innova.front/tasa-por-servicios-extraordinarios.html",
    "DEC305_986": "https://www.impo.com.uy/bases/decretos/305-1986",
    "MEF_IRAE_ANT": "https://www.gub.uy/ministerio-economia-finanzas/sites/ministerio-economia-finanzas/files/2026-01/Decreto%2030_12_25%20mef_230.pdf",
}


def r(condicion, *, base="", desde="", hasta="", unidad_tramo="", tasa="", monto="", unidad_monto="",
      vigencia="", confianza="oficial", src="", notas=""):
    return {"departamento": "", "condicion": condicion, "base": base, "desde": desde, "hasta": hasta, "unidad_tramo": unidad_tramo,
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
    r("anticipo en la importación de bienes de consumo del anexo (lista por código en data/uy/aranceles/arancel.csv)", base="valor en aduana más arancel", tasa=4, vigencia="desde 2026", src="MEF_IRAE_ANT", notas="pago a cuenta del IRAE, no impuesto adicional"),
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
RATES["Adicional del Impuesto a las Trasmisiones Patrimoniales"] = [
    r("adquisición de inmuebles rurales por sociedades y demás contribuyentes de los literales A a D", base="valor real catastral", tasa=5, vigencia="desde 2007", src="LEY18064", notas="destino Instituto Nacional de Colonización; el boletín DGI 2023 muestra recaudación 0"),
    r("herederos y legatarios en línea recta", base="valor real catastral", tasa=4, vigencia="desde 2007", src="LEY18064"),
    r("personas físicas en las condiciones del art. 5", tasa=0, src="LEY18064", notas="no gravadas"),
]
RATES["Fondo Nacional de Música"] = [
    r("espectáculos de conjuntos musicales extranjeros", base="total recaudado", tasa=5, vigencia="desde 1994", src="LEY16624"),
    r("ídem, complementados por un espectáculo nacional", base="total recaudado", tasa=3, vigencia="desde 1994", src="LEY16624"),
]
RATES["Fondo Nacional de Teatro"] = [
    r("espectáculos de elencos nacionales", base="total recaudado", tasa=1, vigencia="desde 2004", src="LEY17741"),
    r("espectáculos de elencos extranjeros", base="total recaudado", tasa=5, vigencia="desde 2004", src="LEY17741"),
    r("espectáculos de elencos mixtos", base="total recaudado", tasa=3, vigencia="desde 2004", src="LEY17741"),
]
RATES["Tasa de promoción y control vitivinícola"] = [
    r("boletas de circulación de vinos nacionales e importados", base="litro de vino", monto=0.31, unidad_monto="UYU por litro (valor 1996, ajuste semestral por IPC)", vigencia="desde 1996", src="LEY16757"),
    r("subproductos de la uva", base="litro o kilo", monto=0.31, unidad_monto="UYU (valor 1996, ajuste por IPC)", vigencia="desde 1996", src="LEY16757"),
]
RATES["Tasa al transporte marítimo y fluvial de pasajeros"] = [
    r("pasajeros entre puertos uruguayos y argentinos (tope legal)", base="precio del pasaje", tasa=2, vigencia="desde 2006", src="LEY18057", notas="destino autoridad portuaria; exentos menores de 10 años"),
]
RATES["Fondo de Financiamiento y Recomposición de la Actividad Arrocera"] = [
    r("exportaciones de arroz y derivados", base="valor FOB", tasa=5, vigencia="desde 2003", src="LEY17663", notas="retención; vigencia actual no verificada"),
]
RATES["Tasas registrales"] = [
    r("inscripción de cada acto o contrato (trámite común)", monto=3, unidad_monto="UR", vigencia="2026", confianza=G, src="DGR_INSC", notas="se paga con e-timbre"),
    r("inscripción urgente (solo Registro Mobiliario)", monto=3812, unidad_monto="UYU", vigencia="2026", confianza=G, src="DGR_INSC"),
    r("certificado de información de inmuebles (común)", monto=1.5, unidad_monto="UR", vigencia="2026", confianza=G, src="DGR_CERT", notas="la página muestra $1.265, valor desactualizado de la UR"),
    r("certificado urgente / segunda ampliación / consulta directa", monto="3.812 / 0,5 UR / 3.041", unidad_monto="UYU salvo indicación", vigencia="2026", confianza=G, src="DGR_CERT"),
]
RATES["Tasa de Servicios Aduaneros / servicios extraordinarios"] = [
    r("permiso de importación (servicio permanente y extraordinario)", monto="escala", unidad_monto="por permiso", vigencia="2026", confianza=G, src="DNA_EXTRA",
      notas="la escala no se publica; la Ley 15.809 deja la tarifa al Poder Ejecutivo"),
    r("servicios fuera del horario habitual, por hora de funcionario", monto=260, unidad_monto="N$ por hora (1986)", vigencia="1986", src="DEC305_986", notas="valor histórico en nuevos pesos"),
]
RATES["Retenciones sobre entradas a bailes"] = [
    r("INAU", base="valor de la entrada", tasa=1, vigencia="2025", confianza=G, src="MVD_BAILES"),
    r("Comisión Honoraria de Lucha Antituberculosa", base="valor de la entrada", tasa=5, vigencia="2025", confianza=G, src="MVD_BAILES"),
    r("Ministerio de Salud Pública", base="valor de la entrada", tasa=3, vigencia="2025", confianza=G, src="MVD_BAILES"),
]
RATES["Impuesto a la Apuesta"] = [
    r("apuestas en máquinas electrónicas de casinos y salas", base="monto apostado", tasa=0.75, vigencia="desde ago-2025", src="DO_20250820", notas="Dec. 167/025; contribuyente el apostador, retiene la sala"),
    r("régimen anterior", base="monto apostado", tasa=0.75, vigencia="2018-2025", confianza=SEC, src="DEC359", notas="Dec. 359/017"),
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
    r("cueros bovinos sin terminar (subpartidas 41.04.11 y 41.04.19): tasa base", base="valor exportado", tasa=5, vigencia="Dec. 639/006", confianza=SEC, src="DETRAC"),
    r("ídem, rebaja transitoria", base="valor exportado", tasa=0, vigencia="desde 2020, prorrogada por Dec. 122/025 (jun-2025)", src="DEC122_2025", notas="sin prórroga posterior encontrada; si venció, rige otra vez el 5%"),
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
RATES["Aporte Social Único de Personas Privadas de Libertad"] = [
    r(f"emprendimientos productivos aprobados por el INR, {tramo}", base="monto ficto (aporte jubilatorio y FRL)", tasa=pct, vigencia="desde 2022", src="BPS_PPL",
      notas="sustituye aportes y demás impuestos nacionales salvo los de importación; monto ficto no publicado")
    for tramo, pct in [("meses 1 a 12", 25), ("meses 13 a 24", 50), ("meses 25 a 36", 75), ("desde el mes 37", 100)]
]

RATES["Tasa Global Arancelaria (Arancel Externo Común)"] = [
    r("importaciones desde el Mercosur", base="valor en aduana (CIF)", tasa=0, vigencia=V26, src="DEC426"),
    r("importaciones extrazona: según posición arancelaria", base="valor en aduana (CIF)", desde=0, hasta=35, unidad_tramo="% (rango)", vigencia="feb-2025", src="MEF_ARANCEL", notas="tasa por código de 10 dígitos en data/uy/aranceles/arancel.csv"),
]
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
    r("envíos de hasta 20 kg y factura de hasta USD 800, opcional", base="valor facturado o declarado", tasa=60, monto=20, unidad_monto="USD mínimo por envío", vigencia="desde 23/3/2026", src="DEC50", notas="sustituye aranceles y tributos internos; comparación con 2024 en data/uy/aranceles/regimen-envios/"),
    r("régimen anterior: envíos de hasta USD 200", base="valor facturado o declarado", tasa=60, monto=10, unidad_monto="USD mínimo por envío", vigencia="2016 a 22/3/2026", src="ADU2015", notas="Decreto 356/014 modificado; ver data/uy/aranceles/regimen-envios/"),
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
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=0, hasta=5000, unidad_tramo="millones de UI", tasa=0.1, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=5000, hasta=10000, unidad_tramo="millones de UI", tasa=0.0975, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=10000, hasta=15000, unidad_tramo="millones de UI", tasa=0.095, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=15000, hasta=20000, unidad_tramo="millones de UI", tasa=0.0925, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=20000, hasta=25000, unidad_tramo="millones de UI", tasa=0.09, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=25000, hasta=30000, unidad_tramo="millones de UI", tasa=0.0875, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=30000, hasta=35000, unidad_tramo="millones de UI", tasa=0.085, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=35000, hasta=40000, unidad_tramo="millones de UI", tasa=0.0825, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=40000, hasta=45000, unidad_tramo="millones de UI", tasa=0.08, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=45000, hasta=50000, unidad_tramo="millones de UI", tasa=0.0775, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=50000, hasta=55000, unidad_tramo="millones de UI", tasa=0.075, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=55000, hasta=60000, unidad_tramo="millones de UI", tasa=0.0725, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=60000, hasta=65000, unidad_tramo="millones de UI", tasa=0.07, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=65000, hasta=70000, unidad_tramo="millones de UI", tasa=0.0675, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=70000, hasta=75000, unidad_tramo="millones de UI", tasa=0.065, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=75000, hasta=80000, unidad_tramo="millones de UI", tasa=0.0625, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=80000, hasta=85000, unidad_tramo="millones de UI", tasa=0.06, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=85000, hasta=90000, unidad_tramo="millones de UI", tasa=0.0575, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=90000, hasta=95000, unidad_tramo="millones de UI", tasa=0.055, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=95000, hasta=100000, unidad_tramo="millones de UI", tasa=0.0525, vigencia="desde 2009", src="DO_20090128"),
    r("bancos (tasa marginal descendente)", base="activos radicados en el país", desde=100000, hasta='', unidad_tramo="millones de UI", tasa=0.05, vigencia="desde 2009", src="DO_20090128"),
    r("casas financieras", base="activos propios en el país", tasa=0.1, vigencia="desde 2009", src="DO_20090128"),
    r("instituciones financieras externas", base="activos propios en el país", tasa=0.1, monto=500000, unidad_monto="UI tope anual", vigencia="desde 2009", src="DO_20090128"),
    r("cooperativas de intermediación financiera", base="activos propios en el país", tasa=0.05, vigencia="desde 2009", src="DO_20090128"),
    r("administradoras de grupos de ahorro previo", base="activos propios en el país", tasa=0.04, vigencia="desde 2009", src="DO_20090128"),
    r("casas de cambio", base="activos propios en el país", tasa=0.02, vigencia="desde 2009", src="DO_20090128"),
    r("instituciones con activos menores a 5 millones de UI (literales A, B y H)", base="activos propios en el país", hasta=5, unidad_tramo="millones de UI", tasa=0, vigencia="desde 2009", src="DO_20090128"),
    r("AFAP", base="comisiones cobradas", tasa=0.2, vigencia="desde 2009", src="DO_20090128"),
    r("aseguradoras, reaseguradoras y mutuas", base="ingresos brutos de fuente uruguaya", tasa=0.2, vigencia="desde 2009", src="DO_20090128", notas="pago a cuenta del IIEA"),
    r("bolsas, corredores y agentes de valores", base="comisiones cobradas", tasa=0.2, vigencia="desde 2009", src="DO_20090128"),
    r("administradoras de fondos de inversión y fiduciarios profesionales", base="comisiones cobradas", tasa=0.2, vigencia="desde 2009", src="DO_20090128"),
    r("emisores de valores de oferta pública", tasa=0, vigencia="desde 2009", src="DO_20090128"),
    r("representaciones de entidades del exterior y administradoras de crédito", base="activos propios en el país", tasa=0.2, vigencia="desde 2009", src="DO_20090128"),
    r("tope legal", base="promedio anual de activos o comisiones", tasa=0.2, src="BCU_TASA", notas="Ley 18.083 art. 95; el Dec. 203/012 agregó sujetos; en 2025 el BCU propuso modificarla"),
]
RATES["Prestación INAC del 0,7% sobre carnes"] = [
    r("carnes vendidas en el mercado interno", base="precio de venta (precios fictos publicados por INAC)", tasa=0.7, src="DL15605", notas="Decreto-ley 15.605"),
]
RATES["Tasa de Control de Faena (INAC)"] = [
    r("faena de reses bovinas: tasa de control original", base="res bovina faenada", monto=1, unidad_monto="USD por res", vigencia="desde 2003", src="INAC_DEC364", notas="Dec. 364/003; la paga el remitente, la deposita la planta en la cuenta INAC/TCF"),
    r("incremento para vacuna antiaftosa (Dec. 432/003)", base="res bovina faenada", monto=1.5, unidad_monto="USD por res", vigencia="desde 2003", src="INAC_DEC11"),
    r("incremento para vacuna antiaftosa (Dec. 34/006)", base="res bovina faenada", monto=1, unidad_monto="USD por res", vigencia="desde 2006", src="INAC_DEC11"),
    r("incremento para vacuna antiaftosa (Dec. 11/009)", base="res bovina faenada", monto=1.3, unidad_monto="USD por res", vigencia="desde 2009", src="INAC_DEC11", notas="total acumulado USD 4,80 por res según los decretos citados; cambios posteriores no verificados"),
    r("habilitación de establecimientos lecheros (Dec. 432/003)", base="leche recibida en planta", monto=0.12, unidad_monto="USD cada 1.000 litros", vigencia="desde 2003", src="INAC_DEC11"),
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
# Departmental rows (including Montevideo) live in departamental_data.py.

RATES["Impuesto a la Compra de Moneda Extranjera"] = [
    r("compras de BCU, BROU y BHU para su actividad de cambio", base="monto comprado", tasa=0, vigencia="1994", src="DEC109"),
    r("compras de personas públicas estatales fuera de la actividad de cambio", base="erogaciones mensuales en moneda extranjera", tasa=2, vigencia="1994", src="DEC109"),
]
_H = dict(confianza=SEC, src="VINALES")  # Viñales (2019), history of the tax system 1990-2018, quoting each law
RATES["Impuesto a las Rentas de la Industria y Comercio"] = [
    r("tasa general", base="renta neta", tasa=30, vigencia="hasta 1990", **_H),
    r("aumento transitorio por un año", base="renta neta", tasa=40, vigencia="1990-1991 (Ley 16.107)", **_H),
    r("tasa general", base="renta neta", tasa=30, vigencia="1991-2002", **_H),
    r("aumento", base="renta neta", tasa=35, vigencia="2002-2004 (Ley 17.453)", **_H),
    r("tasa al momento de la derogación", base="renta neta", tasa=30, vigencia="ejercicios desde ago-2004 hasta 2007 (Dec. 270/004)", **_H),
]
RATES["Impuesto a las Rentas Agropecuarias"] = [
    r("tasa general", base="renta neta agropecuaria", tasa=30, vigencia="hasta 1990", **_H),
    r("aumento transitorio", base="renta neta agropecuaria", tasa=40, vigencia="ejercicio 1989-1990", **_H),
    r("aumento", base="renta neta agropecuaria", tasa=35, vigencia="2002-2004", **_H),
    r("tasa al momento de la derogación", base="renta neta agropecuaria", tasa=30, vigencia="2004-2007", **_H),
]
RATES["Impuesto a las Retribuciones Personales"] = [
    r("retribuciones, hasta 3 SMN", base="retribución nominal", hasta=3, unidad_tramo="salarios mínimos mensuales", tasa=1, vigencia="1982-1990", **_H),
    r("retribuciones, más de 3 SMN", base="retribución nominal", desde=3, unidad_tramo="salarios mínimos mensuales", tasa=2, vigencia="1982-1990", **_H),
    r("empleadores privados y entes", base="retribuciones pagadas", tasa=1, vigencia="1982-1990", **_H),
    r("retribuciones, hasta 3 SMN", base="retribución nominal", hasta=3, unidad_tramo="salarios mínimos mensuales", tasa=1, vigencia="1995-2001 (Ley 16.697)", **_H),
    r("retribuciones, 3 a 6 SMN", base="retribución nominal", desde=3, hasta=6, unidad_tramo="salarios mínimos mensuales", tasa=3, vigencia="1995-2001", **_H),
    r("retribuciones, más de 6 SMN", base="retribución nominal", desde=6, unidad_tramo="salarios mínimos mensuales", tasa=6, vigencia="1995-2001", **_H),
    r("retribuciones, hasta 3 SMN", base="retribución nominal", hasta=3, unidad_tramo="salarios mínimos mensuales", tasa=0, vigencia="ago-2004 a 2007 (Dec. 270/004)", **_H),
    r("retribuciones, 3 a 6 SMN", base="retribución nominal", desde=3, hasta=6, unidad_tramo="salarios mínimos mensuales", tasa=2, vigencia="ago-2004 a 2007", **_H),
    r("retribuciones, más de 6 SMN", base="retribución nominal", desde=6, unidad_tramo="salarios mínimos mensuales", tasa=6, vigencia="ago-2004 a 2007", **_H),
    r("jubilaciones y pensiones, hasta 6 SMN", base="pasividad nominal", hasta=6, unidad_tramo="salarios mínimos mensuales", tasa=0, vigencia="ago-2004 a 2007", **_H),
    r("jubilaciones y pensiones, más de 6 SMN", base="pasividad nominal", desde=6, unidad_tramo="salarios mínimos mensuales", tasa=2, vigencia="ago-2004 a 2007", **_H),
] + brackets("escala de 2002, servicios personales privados", "retribución nominal", "salarios mínimos mensuales",
             [3, 6, 10, 15, 25, 30, 35, 40, 50], [0, 3, 7.5, 9, 10, 13, 14, 15, 17, 18], "VINALES", "2002-2004 (Ley 17.453)", SEC) \
  + brackets("escala de 2002, sector público", "retribución nominal", "salarios mínimos mensuales",
             [3, 6, 10, 15, 20, 25, 30, 35], [0, 3, 7.5, 10, 12, 14, 16, 18, 20], "VINALES", "2002-2004 (Ley 17.453)", SEC) \
  + brackets("escala de 2002, jubilaciones y pensiones", "pasividad nominal", "salarios mínimos mensuales",
             [3, 6, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60], [1, 2, 4, 7.5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20], "VINALES", "2002-2004 (Ley 17.453)", SEC)
RATES["Impuesto de Contribución al Financiamiento de la Seguridad Social"] = [
    r("bienes industrializados vendidos a organismos estatales, empresas y contribuyentes de IVA o IMESI, e importaciones", base="precio sin IVA; en importación, valor en aduana más arancel incrementado hasta 21,75%", tasa=3, vigencia="2001-2007 (Ley 17.345)", notas="luego se agregaron servicios públicos de empresas estatales; el Dec. 270/004 redujo la tasa sobre esos servicios", **_H),
]
RATES["Impuesto a los Activos de las Empresas Bancarias"] = [
    r("activos gravados (tope legal)", base="activos de bancos y casas financieras", tasa=1.5, vigencia="1986-1995", **_H),
    r("créditos de comercio exterior, préstamos a 3 años o más y otros", base="activos", tasa=0.75, vigencia="1986-1995", **_H),
    r("prefinanciación de exportaciones", base="créditos", tasa=0.01, vigencia="desde 1995", **_H),
    r("resto de los activos gravados (tope legal)", base="activos", tasa=2, vigencia="1995-2007 (Ley 16.697)", **_H),
]
RATES["Impuesto de Control del Sistema Financiero"] = [
    r("tope legal al crearse", base="créditos computables para el IMABA", tasa=0.18, vigencia="2001-2002 (Ley 17.296)", **_H),
    r("tope legal", base="créditos computables para el IMABA", tasa=0.36, vigencia="2002-2007 (Ley 17.453)", **_H),
]
RATES["Impuesto Específico a los Servicios de Salud"] = [
    r("servicios de salud prestados en el país", base="precio del servicio", tasa=3, vigencia="2001-2007 (Ley 17.309)", notas="exonerados los servicios gravados por IVA desde 2002", **_H),
]
RATES["Impuesto a las Pequeñas Empresas"] = [
    r("empresas del literal E del IRIC", monto=20000, unidad_monto="nuevos pesos mensuales (1990)", vigencia="1990, actualizado por IPC", notas="desde 2001 se usó, aumentado 30%, como mínimo del IRIC; monto al derogarse no encontrado", **_H),
]
RATES["Impuesto a las Comisiones"] = [
    r("tope al crearse", base="comisiones", tasa=5, vigencia="1991", **_H),
    r("tope", base="comisiones", tasa=7, vigencia="1992", **_H),
    r("tope", base="comisiones", tasa=9, vigencia="1993-2002", **_H),
    r("aumento", base="comisiones", tasa=10.5, vigencia="2002-jul-2004 (Ley 17.453)", **_H),
    r("tasa al momento de la derogación", base="comisiones", tasa=9, vigencia="ago-2004 a 2007 (Dec. 270/004)", **_H),
]
RATES["Impuesto a las Telecomunicaciones"] = [
    r("llamadas salientes desde líneas celulares", monto=0.4, unidad_monto="pesos por minuto", vigencia="2002-2007 (Ley 17.453)", **_H),
    r("llamadas salientes de larga distancia internacional", monto=2, unidad_monto="pesos por minuto", vigencia="2002-2007", **_H),
    r("llamadas de telefonía fija a celulares", monto=0.4, unidad_monto="pesos por minuto", vigencia="2002-2007", **_H),
]
RATES["Impuesto a las Tarjetas de Crédito"] = [
    r("emisores de tarjetas de crédito (tope legal)", monto=0.1, unidad_monto="UR mensuales por tarjeta vigente", vigencia="2002-2007 (Ley 17.453)", **_H),
]
RATES["Impuesto a las Ventas Forzadas"] = [
    r("ventas en remate judicial de muebles e inmuebles", base="precio obtenido en el remate", tasa=2, vigencia="1993-2007 (Ley 16.320 art. 391)", confianza=SEC, src="DEC658", notas="paga el comprador; retiene el rematador"),
]
RATES["Impuesto a las Cesiones de Derechos sobre Deportistas"] = [
    r("cesiones o permutas de derechos de deportistas a entidades del exterior (tope legal)", base="precio de la cesión", tasa=10, vigencia="2001-2007 (Ley 17.296)", notas="50% al Ministerio de Deporte y 50% al Fondo Nacional de lucha contra el SIDA", **_H),
]
RATES["Impuesto a la Compraventa de Bienes Muebles en Remate Público"] = [
    r("compraventa de muebles en remate público", base="precio de venta", tasa=0.2, vigencia="desde 1967 (Ley 13.640, destino MEVIR)", notas="2 por mil, por mitades entre las partes; la Ley 16.694 (1995) modificó la alícuota, valor no encontrado", **_H),
]
RATES["Impuesto a los Concursos, Sorteos y Competencias"] = [
    r("concursos, sorteos y competencias por teléfono, correo o similares (tope legal)", base="ingresos del organizador sin IVA", tasa=20, vigencia="1999-2007 (Ley 17.166)", src="LEY17166"),
]
RATES["Impuesto a la Concentración de Inmuebles Rurales"] = [
    r("titulares con inmuebles rurales que superan 2.000 ha CONEAT 100", base="hectáreas CONEAT 100", desde=d, hasta=h, unidad_tramo="ha", monto=m, unidad_monto="UI por hectárea", vigencia="2012-2013", confianza=SEC, src="LEY18876",
      notas="Ley 18.876; declarado inconstitucional y derogado por la Ley 19.093 (2013)")
    for d, h, m in [(0, 2000, 0), (2000, 5000, 67), (5000, 10000, 100), (10000, "", 135)]
]
RATES["Impuesto a la Venta de Moneda Extranjera"] = [
    r("ventas de bancos, financieras y casas de cambio (tope legal)", base="precio de la operación", tasa=1.5, vigencia="desde 1984 (Decreto-ley 15.584)", **_H),
]
RATES["Impuesto a las Actividades Agropecuarias"] = [
    r("tope legal", base="ingreso neto ficto según capacidad productiva CONEAT", tasa=30, vigencia="1984-1995", notas="exentos hasta 200 ha de producción media; 40% en el ejercicio 1989-1990; derogado desde jul-1995", **_H),
]
RATES["Impuesto a la Constitución y Aumentos de Capital de Sociedades Anónimas"] = [
    r("constitución", base="capital", tasa=1, vigencia="1985-2001", **_H),
    r("aumentos de capital", base="aumento", desde=0.5, hasta=1, unidad_tramo="% (rango)", vigencia="1991-2001", notas="reemplazado por el ICOSA", **_H),
]
RATES["Impuesto Adicional a las Retribuciones Personales"] = [
    r("sector público, más de 20 SMN", base="retribución", tasa=4, vigencia="2002-2004", notas="sube hasta 7%", **_H),
    r("resto, más de 25 SMN", base="retribución", tasa=3, vigencia="2002-2004", notas="sube 1% cada 5 SMN hasta 6%", **_H),
]
RATES["Impuesto a los Ingresos de las Compañías de Seguros"] = [
    r("compañías con dirección y capital en el exterior: ramos generales", base="ingresos brutos por primas", tasa=7, vigencia="hasta 2001 (T.O. 1987 Título 6)", **_H),
    r("ídem: seguros marítimos / vida", base="ingresos brutos por primas", monto="4% / 2%", vigencia="hasta 2001", **_H),
    r("compañías con dirección y capital en el país: ramos generales", base="ingresos brutos por primas", tasa=5, vigencia="hasta 2001", **_H),
    r("ídem: seguros marítimos / vida", base="ingresos brutos por primas", monto="2% / 0,5%", vigencia="hasta 2001", notas="reemplazado por el IIEA (Ley 17.296)", **_H),
]
RATES["Recargos a la importación"] = nodata("Impuesto Aduanero Único y recargos, unificados en la Tasa Global Arancelaria (Decreto 85/991); tasas históricas no encontradas")

DEPARTAMENTAL_SIN_DATOS = "cada intendencia fija sus alícuotas; sin datos todavía"


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:70]


# catalog.csv `nivel` -> folder holding that level's rate files
FOLDERS = {
    "nacional": "nacional",
    "organismos": "organismos",
    "aduana": "aduana",
    "seguridad_social": "seguridad_social",
    "departamental": "departamental",
    "derogado": "derogados",
}


def departmental_rows():
    """Rows from departamental_data.py grouped by tributo, with department and source filled in."""
    import departamental_data as dd
    by_tributo = {}
    for dept, tributo, row in dd.rows(r):
        row["departamento"] = dept
        row["condicion"] = f"{dept}: {row['condicion']}"
        if not row["fuente"]:
            row["fuente"] = dd.DEPT_SOURCES[dept][0]
        by_tributo.setdefault(tributo, []).append(row)
    return by_tributo


def main():
    path = HERE / "catalog.csv"
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    unused = set(RATES)
    dept = departmental_rows()
    unknown = set(dept) - {row["nombre"] for row in rows}
    if unknown:
        sys.exit(f"departmental rows for tributos missing from catalog.csv: {sorted(unknown)}")
    written = set()
    for row in rows:
        name = row["nombre"]
        if name in RATES or name in dept:
            data = RATES.get(name, []) + dept.get(name, [])
            unused.discard(name)
        elif row["nivel"] == "departamental":
            data = nodata(DEPARTAMENTAL_SIN_DATOS)
        elif row["estado"] == "derogado":
            data = nodata("derogado; tasa histórica sin datos todavía")
        else:
            data = nodata()
        rel = Path(FOLDERS[row["nivel"]]) / f"{slug(name)}.csv"
        row["archivo"] = rel.as_posix()
        written.add(rel)
        (HERE / rel.parent).mkdir(exist_ok=True)
        with open(HERE / rel, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            w.writerows(data)
    if unused:
        sys.exit(f"rates without catalog entry: {sorted(unused)}")
    for folder in set(FOLDERS.values()):
        for stale in (HERE / folder).glob("*.csv"):
            if stale.relative_to(HERE) not in written:
                stale.unlink()
    fields = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "files written")

if __name__ == "__main__":
    main()
