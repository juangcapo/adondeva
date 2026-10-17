"""Departmental tax rates, transcribed from each intendencia's budgets (2001-2026), decrees and texts ordenados.

Each entry is (catalog tributo name, row). build_rates.py prefixes the department to `condicion`, fills the
`departamento` column and merges these rows into the tributo's file under departamental/.
The budget texts are kept in departamental/raw/presupuestos_2026/ for checking the details (per-locality tables).
"""

DEPT_SOURCES = {
    "Montevideo": ("https://tramites.montevideo.gub.uy/sites/tramites.montevideo.gub.uy/files/tributos/documentos/2026_Calculo_Contribucio%CC%81n_Inmobiliaria.pdf", "Cálculo de Contribución Inmobiliaria 2026 (IM)"),
    "Canelones": ("https://www.impo.com.uy/diariooficial/2026/06/23/documentos.pdf", "Presupuesto Quinquenal 2026-2030"),
    "Colonia": ("https://www.impo.com.uy/diariooficial/2011/08/29/documentos.pdf", "Decreto 013/2011, Presupuesto 2011-2015, vigente con cambios de los Decretos 017/2021 y 005/2026"),
    "Maldonado": ("https://www.revistacero.com.uy/ajustan-la-contribucion-inmobiliaria-y-tributos-asociados-en-maldonado-regiran-desde-enero-de-2026/", "prensa sobre la Resolución 11905/2025 (las filas oficiales citan el TOTIDEM)"),
    "Rocha": ("https://www.impo.com.uy/diariooficial/2026/04/10/documentos.pdf", "Decreto 1/2026, Presupuesto Quinquenal 2026-2030"),
    "Durazno": ("https://www.impo.com.uy/diariooficial/2026/07/01/documentos.pdf", "Presupuesto Quinquenal 2026-2030 (modifica el Dec. 1664/2001)"),
    "Río Negro": ("https://www.impo.com.uy/diariooficial/2026/07/03/documentos.pdf", "Decreto 38/2026, Presupuesto Quinquenal 2026-2030"),
    "Artigas": ("https://www.impo.com.uy/diariooficial/2026/07/27/documentos.pdf", "Presupuesto Quinquenal 2026-2030"),
    "Cerro Largo": ("https://www.impo.com.uy/diariooficial/2026/07/06/documentos.pdf", "Decreto 2/2026, Presupuesto Quinquenal 2026-2030"),
    "Paysandú": ("https://www.impo.com.uy/diariooficial/2026/08/07/documentos.pdf", "Presupuesto Quinquenal 2026-2030"),
    "Rivera": ("https://www.impo.com.uy/diariooficial/2016/05/27/documentos.pdf", "Ordenanza 2/016, Presupuesto 2016-2020, sobre la Ordenanza 10/11 y el Decreto 3724/2000"),
    "Soriano": ("https://www.impo.com.uy/diariooficial/2011/07/21/documentos.pdf", "Presupuesto 2011-2015, modificaciones a la Recopilación Impositiva Municipal (RIM)"),
    "Tacuarembó": ("https://www.impo.com.uy/diariooficial/2026/06/12/documentos.pdf", "Decreto 06/2026, Presupuesto Quinquenal 2026-2030"),
    "Treinta y Tres": ("https://www.impo.com.uy/diariooficial/2026/09/10/documentos.pdf", "Decreto 08/2001 (alumbrado) republicado en 2026"),
    "Salto": ("https://www.impo.com.uy/diariooficial/2011/05/24/documentos.pdf", "Presupuesto Quinquenal 2011-2015"),
    "Flores": ("https://www.impo.com.uy/diariooficial/2026/07/23/documentos.pdf", "Decreto 1.167/2026, Presupuesto Quinquenal 2026-2030"),
    "Florida": ("https://www.impo.com.uy/diariooficial/2026/09/03/documentos.pdf", "Presupuesto Quinquenal 2026-2030"),
}

CIU = "Contribución Inmobiliaria Urbana y Suburbana"
CIR = "Contribución Inmobiliaria Rural"
ADIC = "Adicionales municipales a la Contribución Inmobiliaria"
IGM = "Impuesto General Municipal"
ALUM = "Impuesto de alumbrado público"
EDIF = "Impuesto a la Edificación Inapropiada"
BALD = "Impuesto a los Terrenos Baldíos"
PAT = "Patente de Rodados"
VEXT = "Impuesto a la circulación de vehículos extranjeros"
ESPEC = "Impuesto a los espectáculos públicos"
PROP = "Impuesto a los avisos y propaganda"
REM = "Impuesto a los Remates (Ley 12.700)"
BROM = "Tasa Bromatológica"
HIG = "Tasas de higiene"
NEC = "Tasas de necrópolis"
ADM = "Tasas administrativas"
TRAN = "Tasas de tránsito"
ARQ = "Tasas de arquitectura"
MEJ = "Contribución por mejoras"
AMB = "Tasa de preservación ambiental"
TERM = "Tasa de uso de terminales de pasajeros"
HAB = "Tasa de habilitación comercial"


def do(date):
    """Diario Oficial issue URL for an ISO date."""
    return f"https://www.impo.com.uy/diariooficial/{date[:4]}/{date[5:7]}/{date[8:]}/documentos.pdf"


def rows(r):
    """Return [(department, tributo, row)]. `r` is build_rates.r, passed in to avoid an import cycle."""
    out = []

    def add(dept, tributo, condicion, fuente="", **kw):
        kw.setdefault("vigencia", "2026-2030")
        kw.setdefault("confianza", "oficial")
        row = r(condicion, **kw)
        row["fuente"] = fuente
        out.append((dept, tributo, row))

    # --- Montevideo -------------------------------------------------------------------------------------
    M = "Montevideo"
    for d, h, tt in [(0, 992630, 0.25), (992630, 2481576, 0.75), (2481576, 4963144, 1), (4963144, 8551753, 1.2), (8551753, 17103509, 1.65), (17103509, "", 1.8)]:
        add(M, CIU, "escala progresiva por tramos", base="valor imponible 2026", desde=d, hasta=h, unidad_tramo="UYU", tasa=tt, vigencia="2026")
    add(M, CIU, "primer tramo para inmuebles con valor imponible menor a $2.481.577", base="valor imponible 2026", desde=0, hasta=992630, unidad_tramo="UYU", tasa=0.18, vigencia="2026", notas="en lugar de 0,25% (Decreto 38.156)")
    M26, MD = do("2026-07-06"), "https://montevideo.gub.uy/sites/default/files/biblioteca/decretono38.262.pdf"
    MT = "https://tramites.montevideo.gub.uy/tramites-y-tributos/"
    add(M, ADIC, "fincas urbanas o suburbanas deshabitadas al menos un año civil", base="Contribución Inmobiliaria", tasa=100, fuente=M26,
        notas="se presume por consumo de luz y agua 98% menor al promedio de 5 años")
    add(M, CIU, "padrones pasados de rural a suburbano que mantienen uso productivo (facultad)", desde=0, hasta=100, unidad_tramo="% de exoneración", fuente=M26)
    add(M, CIR, "subsidio a jubilados y pensionistas, vivienda única, ingresos hasta 5 BPC y valor hasta 500.000 UI", tasa=-100, fuente=M26, notas="50% si el valor supera el tope hasta en 50%")
    for c, rate in [("general y deporte profesional", 10), ("deporte no profesional", 5), ("competiciones hípicas", 5), ("aparatos mecánicos o eléctricos", 3),
                    ("artistas internacionales fuera del MERCOSUR", 8), ("festivales sin 70% de artistas nacionales", 6)]:
        add(M, ESPEC, c, base="precio de la entrada sin impuestos nacionales", tasa=rate, fuente=M26)
    for grupo, cuts in [("artistas nacionales o residentes (70% o más)", [150000, 500000, 1500000]), ("artistas residentes en el MERCOSUR", [100000, 450000, 1000000])]:
        for i, rate in enumerate([0, 2, 4, 6]):
            add(M, ESPEC, f"{grupo}, tramo {i + 1}", base="recaudación", desde=([0] + cuts)[i], hasta=(cuts + [""])[i], unidad_tramo="UI", tasa=rate, fuente=M26)
    for i, (cap, ui) in enumerate([("hasta 50", 0), ("51 a 150", 268), ("151 a 300", 589), ("301 a 450", 1321), ("451 a 600", 1463), ("601 a 1.000", 1963),
                                   ("1.001 a 1.500", 3034), ("1.501 a 2.000", 3926), ("2.001 a 2.500", 4640), ("más de 2.500", 5354)]):
        add(M, ESPEC, f"bailes públicos más de dos veces al mes, capacidad {cap} personas", monto=ui, unidad_monto="UI mensuales", vigencia="desde 2023", fuente=MD)
    add(M, "Tasas de seguridad y protección", "rifas y similares", base="boletos vendidos", tasa=5, fuente=M26, notas="sin exoneraciones")
    add(M, "Tasas de seguridad y protección", "sorteos y promociones con premios de más de 100 UR", base="valor de los premios con IVA", tasa=5, vigencia="2024",
        fuente=MT + "autorizacion/realizar-sorteos-y-promociones-para-premios-superiores-a-100-ur", confianza="guia_oficial", notas="más garantía de 20%")
    add(M, ADM, "sellado de inicio / de culminación de trámite", monto="1.740 / 3.797", unidad_monto="UYU (mayo-agosto 2024)", vigencia="2024", confianza="guia_oficial",
        fuente=MT + "autorizacion/realizar-sorteos-y-promociones-para-premios-superiores-a-100-ur")
    add(M, ADM, "sellado de ingresos comerciales (por formulario)", monto=329, unidad_monto="UYU (agosto 2024)", vigencia="2024", confianza="guia_oficial",
        fuente=MT + "solicitud/baja-de-avisos-y-propaganda")

    # --- Canelones, Colonia, Maldonado: no 2026 budget text with rates found; third-party or press figures ----
    Ca = "Canelones"
    add(Ca, CIU, "alícuotas según zona y categoría", base="valor catastral", desde=0.45, hasta=1.9, unidad_tramo="% (rango)", confianza="secundaria", vigencia="2026",
        fuente="https://datosuruguay.com/contribucion-inmobiliaria/canelones", notas="la escala no está en el presupuesto 2026")
    add(Ca, CIU, "bonificación por pago total antes del primer vencimiento (urbana y suburbana)", tasa=-10, notas="incluye tributos conexos salvo la tasa de servicios administrativos")
    add(Ca, CIU, "buen pagador categoría A / categoría B", monto="-15% / -10%", unidad_monto="bonificación", notas="no acumulables con la anterior")
    add(Ca, CIU, "padrones en zona inundable (facultad)", desde=0, hasta=50, unidad_tramo="% de reducción")
    add(Ca, CIU, "multa por mora urbana: 1 a 30 días / más de 30 días", monto="5% / 10%", unidad_monto="del tributo", notas="más recargo de 1% mensual")
    add(Ca, CIR, "multa por mora rural: hasta 5 días hábiles / hasta 90 días / más de 90 días", monto="5% / 10% / 20%", unidad_monto="del tributo")
    add(Ca, BALD, "baldíos en régimen de urbanización PH (UH)", base="valor catastral", tasa=1.9)
    add(Ca, "Impuesto a la venta de carne", "derogado por el presupuesto 2026 (Ordenanza 4152 de 1973)", tasa=0, notas="derogado")
    Ma, TOT = "Maldonado", "https://digesto.maldonado.gub.uy/detalle-volumen/13"
    add(Ma, CIU, "mínimo anual desde 2026 (art. D.585)", monto=4450, unidad_monto="UYU de enero 2025", vigencia="desde 2026", fuente=TOT)
    for c, rate in [("hipermercados o supermercados de más de 200 m² y shoppings", 6), ("restaurantes y hoteles o similares con más de 60 unidades y restaurante", 4), ("demás inmuebles", 3)]:
        add(Ma, ADIC, f"Adicional Impuesto General Ambiental: {c}", base="valor imponible de la contribución urbana y suburbana", tasa=rate, vigencia="desde 2026", fuente=TOT,
            notas="reemplaza al Adicional Impuesto General Municipal (derogado el 1/1/2026); mínimo $4.450 de 2025")
    add(Ma, ADIC, "adicional de videovigilancia pública", base="valor imponible", tasa=0.55, monto=162, unidad_monto="UYU mínimo", vigencia="2017-2025", fuente=TOT, notas="venció el 31/12/2025")
    add(Ma, ALUM, "impuesto de alumbrado público (adicional de la contribución)", base="valor imponible de la contribución", tasa=3.5, monto=1525, unidad_monto="UYU mínimo (valores 2021)", vigencia="desde 2022", fuente=TOT,
        notas="chacras marítimas pagan hasta 50%")
    add(Ma, CIU, "única propiedad habitada por sus dueños, ingresos hasta 9 BPC", tasa=-50, fuente=TOT, notas="60% para hogares monoparentales; alcanza adicionales y tasas")
    add(Ma, CIU, "pago anual hasta el 31 de enero", tasa=-6, fuente=TOT)
    add(Ma, CIR, "propietarios que explotan hasta 1.000 ha CONEAT 100", base="alícuota de la Ley 15.809 art. 652", tasa=-18, fuente=TOT)
    add(Ma, BALD, "escala por metro cuadrado según zona (Gorlero y Rambla de los Argentinos el máximo; localidades menores el mínimo)", monto="1.283 a 9", unidad_monto="N$ por m² al año (valores originales, actualizados)", fuente=TOT,
        notas="10 zonas y unas 45 subzonas; el aumento anual va de 2,5 a 5 veces lo liquidado el ejercicio anterior")
    add(Ma, EDIF, "construcciones sin permiso o en contravención", notas="1/5 anual y acumulativo; al regularizar las tasas se multiplican de 1 a 10 veces según avance", fuente=TOT)
    add(Ma, ADM, "timbre municipal sobre todo pago o cobro de la Tesorería", base="monto del recibo", tasa=2, fuente=TOT)
    add(Ma, ADM, "testimonio / certificado del Registro Civil", monto="30 / 25", unidad_monto="UYU", fuente=TOT)
    add(Ma, ADM, "tasa por actividad administrativa", tasa=0, vigencia="desde 2025", fuente=TOT, notas="suprimida por el Dec. 4113/2025")
    add(Ma, ADM, "registro de constructores y empresas de demolición / instaladores sanitarios", monto="544 / 218", unidad_monto="UYU anuales", fuente=TOT)
    for i, m in enumerate([2311, 6111, 17814, 27641, 110568]):
        add(Ma, HIG, f"tasa de contralor de higiene ambiental, categoría {i + 1} (por giro comercial)", monto=m, unidad_monto="UYU anuales", fuente=TOT)
    add(Ma, BROM, "contralores, exámenes o inspecciones: hasta 10 / 11 a 20 / 21 a 30 por mes", monto="2.000 / 15.000 / 30.000", unidad_monto="UYU por período", fuente=TOT)
    add(Ma, "Tasa forestal", "padrones forestados", monto=0.001, unidad_monto="UR por m²", vigencia="desde 2022", fuente=TOT)
    add(Ma, ARQ, "inspección de espacios comunes", monto=0.1, unidad_monto="UR por m² (tope 100 UR)", fuente=TOT)
    add(Ma, ARQ, "tasa de conservación de pavimento", monto=1525, unidad_monto="UYU mínimo anual (valores 2021)", vigencia="desde 2022", fuente=TOT)
    add(Ma, ARQ, "fraccionamiento con excepción a la ordenanza / urbanización con calles nuevas", monto="+10% por lote / +25%", unidad_monto="sobre la tasa base", fuente=TOT)
    add(Ma, NEC, "inhumación / reducción o traslado / conservación anual de panteones", monto="400 / 200 / 200", unidad_monto="UYU", fuente=TOT)
    add(Ma, "Ocupación de espacios públicos", "redes en subsuelo o espacio aéreo hasta 50 m", monto=10, unidad_monto="UR anuales", fuente=TOT, notas="hasta 50% menos si comparten soportes")
    add(Ma, "Ocupación de espacios públicos", "reserva de espacio en la vía pública (estacionamiento, carga y descarga)", monto=2700, unidad_monto="UYU anuales", fuente=TOT)
    add(Ma, "Impuesto a la extracción de materiales", "extracción de materiales (arena, piedra, etc.)", base="aforo del m³ en el sitio de producción", tasa=5, fuente=TOT)
    add(Ma, MEJ, "obras de mejora urbanas: frentistas", desde=0, hasta=80, unidad_tramo="% del costo", fuente=TOT, notas="hasta 100% en algunos casos; pavimento a pedido: frentistas 60% o más, no frentistas hasta 40%")
    add(Ma, ESPEC, "competencias hípicas de interés departamental todo el año", tasa=-50, fuente=TOT, notas="exoneración del impuesto a las apuestas mutuas")
    add("Maldonado", CIU, "escala progresiva; mínimo anual", monto=4616, unidad_monto="UYU mínimo anual", confianza="secundaria", vigencia="2026", notas="ajuste 2026 de 4,09% por IPC (Res. 11905/2025); muchos padrones de balnearios en las franjas de 3% a 5%")
    add("Maldonado", ADIC, "Adicional Impuesto General Ambiental (desde 2026)", monto=4616, unidad_monto="UYU mínimo anual", confianza="secundaria", vigencia="2026")
    add("Maldonado", ALUM, "adicional de alumbrado público", monto=2046, unidad_monto="UYU mínimo anual", confianza="secundaria", vigencia="2026")
    add("Maldonado", ARQ, "tasa de conservación de pavimento", monto=2046, unidad_monto="UYU mínimo anual", confianza="secundaria", vigencia="2026")

    # --- Colonia: Decreto 013/2011 (bracket limits in 2011 pesos, updated by the property value index), with 2021 and 2026 changes
    Co, V11 = "Colonia", "desde 2012 (Dec. 013/2011)"
    D21, D26 = do("2021-12-24"), do("2026-09-02")
    for zona, cuts, rates in [
            ("urbanos de Colonia del Sacramento", [87022, 145040, 362608, 725231], [0.7443, 0.9795, 1.218, 1.8157, 1.915]),
            ("urbanos del resto del departamento y balnearios", [116690, 233380, 583466, 1166932], [0.7443, 0.9795, 1.218, 1.8898, 1.9929]),
            ("suburbanos de Colonia del Sacramento", [271957, 543923], [1.2, 2.4, 2.45]),
            ("suburbanos del resto del departamento", [437600, 875199], [1.2, 2.4, 2.45])]:
        for i, rate in enumerate(rates):
            add(Co, CIU, f"padrones {zona}, franja {'abcde'[i]}", base="valor imponible", desde=([0] + cuts)[i], hasta=(cuts + [""])[i],
                unidad_tramo="UYU de 2011", tasa=rate, vigencia=V11, notas="cada padrón tributa la alícuota de su franja; entes públicos tienen otra escala (1,116% a ...)")
    add(Co, CIU, "mínimo por padrón", monto=2, unidad_monto="UR anuales", vigencia=V11)
    add(Co, CIU, "inmuebles pasados a suburbanos por el Dec. 036/2013 con instalaciones", base="valor imponible", tasa=0.5, vigencia="desde 2021", fuente=D21)
    add(Co, CIU, "bonificación por pago contado de buenos pagadores", tasa=-10, vigencia="desde 2021", fuente=D21, notas="incluye sobretasas de alumbrado y salubridad")
    add(Co, CIU, "jubilados y pensionistas con ingresos hasta 10 BPC, vivienda única de hasta $666.040 (2021)", tasa=-50, vigencia="desde 2021", fuente=D21)
    D17 = do("2017-01-09")
    for z, m in [("I", 300), ("II", 200), ("III", 100)]:
        add(Co, ALUM, f"impuesto al alumbrado público, zona {z} de cada localidad", monto=m, unidad_monto="UYU de oct. 2016 mensuales (ajuste por índice tarifario UTE)", vigencia="desde 2017", fuente=D17,
            notas="Decreto 34/2016; reemplaza la sobretasa del Dec. 013/2011, que sigue solo para casos especiales")
    add(Co, ALUM, "clientes UTE con tarifas de inclusión social", monto=40, unidad_monto="UYU de 2016 mensuales", vigencia="desde 2017", fuente=D17)
    add(Co, ALUM, "padrones que pagaban más de $20.000 de sobretasa en 2016 (facultad)", base="lo pagado en 2016", tasa=70, vigencia="desde 2017", fuente=D17)
    add(Co, ALUM, "sobretasa de alumbrado (régimen anterior, casos residuales)", base="alícuotas de la contribución inmobiliaria", tasa=50, vigencia=V11, notas="más 50% por lámparas de mercurio o sodio")
    add(Co, ADIC, "sobretasa de salubridad y limpieza", base="alícuotas de la contribución inmobiliaria", tasa=50, vigencia=V11, notas="mínimo 1 UR")
    add(Co, "Tasa General Municipal", "tasa de manejo de residuos (inmuebles sin sobretasa de salubridad con recolección)", monto=2, unidad_monto="UR anuales", vigencia="desde 2026", fuente=D26)
    add(Co, ADIC, "tasa de actualización catastral", monto=1, unidad_monto="UR anuales", vigencia="2012-2015", notas="creada por 4 años")
    add(Co, BALD, "baldíos en general", base="valor imponible", tasa=10, vigencia="desde 2026", fuente=D26)
    add(Co, BALD, "frentistas a Av. General Flores, Av. Artigas, Rambla Colón y Rambla de las Américas (Colonia del Sacramento)", base="valor imponible", tasa=30, vigencia="desde 2026", fuente=D26)
    add(Co, BALD, "zonas de interés turístico y de continuidad urbana", base="valor imponible", tasa=20, vigencia="desde 2026", fuente=D26)
    add(Co, EDIF, "edificación antihigiénica o inhabitable", monto=2, unidad_monto="UR por metro de frente al año", vigencia=V11)
    add(Co, EDIF, "frentes sin vereda en calles con cuneta", monto=0.5, unidad_monto="UR por metro de frente al año", vigencia=V11)
    for c, m in [("automotores y motos de más de 100 cc", 1), ("motos de 50 a 100 cc", 0.75), ("ciclomotores de hasta 50 cc", 0.5)]:
        add(Co, PAT, f"mínimo: {c}", monto=m, unidad_monto="UR anuales", vigencia=V11, notas="el aforo general lo fija el SUCIVE")
    add(Co, ESPEC, "espectáculos públicos", base="valor de la entrada", tasa=5, vigencia=V11, notas="sin entrada: 70% del precio de la bebida más barata")
    add(Co, HIG, "tasa de higiene ambiental de locales abiertos al público", monto=4.5, unidad_monto="UR anuales", vigencia=V11, notas="exonera empresas con hasta 1 empleado")
    add(Co, BROM, "registro, habilitación y contralor de higiene", monto=2, unidad_monto="UR base × coeficiente 1 a 30", vigencia=V11)
    add(Co, BROM, "contralor en la cadena de distribución", monto=1, unidad_monto="UR base", vigencia=V11)
    add(Co, ADM, "tasa administrativa por trámite", monto=82, unidad_monto="UYU de 2011", vigencia=V11)
    add(Co, ADM, "certificado de libre de multas / antecedentes", monto="153 / 252", unidad_monto="UYU de 2011", vigencia=V11)
    add(Co, ADM, "derecho de rifas y sorteos", monto=800, unidad_monto="UYU de 2011", vigencia=V11)
    add(Co, TRAN, "inspección de vehículos / libreta / transferencia moto / transferencia otros", monto="322 / 157 / 252 / 380", unidad_monto="UYU de 2011", vigencia=V11)
    add(Co, TRAN, "licencia de conducir (mayores de 70)", monto="405 (82)", unidad_monto="UYU de 2011", vigencia=V11)
    add(Co, TRAN, "transferencia de permisos de taxi, remise o similar", monto=15924, unidad_monto="UYU de 2011", vigencia=V11)
    add(Co, ARQ, "revisión de planos: hasta 500 m² / 501 a 1.000 m² / más de 1.000 m²", monto="1.901 / 3.802 / 15.208", unidad_monto="UYU de 2011", vigencia=V11)
    add(Co, ARQ, "derechos de edificación vivienda modesta / económica / mediana / confortable", monto="13 / 26 / 53 / 80", unidad_monto="UYU de 2011 por m²", vigencia=V11, notas="locales comerciales 26, depósitos 14")
    add(Co, ARQ, "regularización de obra sin permiso", base="tasas de planos y edificación", tasa=50, vigencia="desde 2021", fuente=D21, notas="recargo")
    add(Co, ARQ, "fraccionamientos: servicio / por solar / por hectárea", monto="153 / 123 / 187", unidad_monto="UYU de 2011", vigencia=V11)
    add(Co, "Tasa de promoción turística", "huéspedes de hoteles y similares en zonas turísticas", monto=20, unidad_monto="UYU de 2011 por persona y noche", vigencia=V11, notas="menores de 13 exentos")
    add(Co, NEC, "inhumación en tierra / nicho / panteón", monto="207 / 396 / 784", unidad_monto="UYU de 2011", vigencia=V11)
    add(Co, HAB, "surtidores: contralor anual por pico (querosén / urbano y Ruta 1 / otras zonas)", monto="496 / 712 / 599", unidad_monto="UYU de 2011", vigencia=V11)
    add(Co, HAB, "barométricas privadas: inspección anual", monto=8, unidad_monto="UR", vigencia=V11)
    add(Co, "Ocupación de espacios públicos", "quiosco permanente / instalación transitoria / unidad móvil", monto="3.474 al año / 57 por m² al mes / 1.500 al mes", unidad_monto="UYU de 2011", vigencia=V11)

    # --- Rivera: Ordenanza 2/016 (2016-2020) over Ordenanza 10/11 and Decreto 3724/2000 --------------------------
    Ri, R11 = "Rivera", do("2011-05-26")
    for z, rate in [("zona catastral urbana de la ciudad de Rivera", 1.6), ("zona suburbana de la ciudad de Rivera", 1.3), ("zonas del interior del departamento", 1)]:
        add(Ri, CIU, z, base="valor real catastral", tasa=rate, vigencia="desde 2016")
    add(Ri, CIU, "exoneración por ingresos del núcleo familiar hasta 20 UR", tasa=-100, vigencia="desde 2011", fuente=R11, notas="tope del Decreto 3724/2000 art. 10")
    for f, m in [("franja 1 (damero céntrico y asistencia médica)", 6), ("franja 2", 5), ("franja 3", 3), ("franja 4", 2.5), ("franja 5 (municipios)", 2.5), ("franja 6 (juntas locales)", 1)]:
        add(Ri, HIG, f"tasa de higiene de locales comerciales, industriales y de servicios: {f}", monto=m, unidad_monto="UR anuales", vigencia="desde 2016")
    for c, m in [("hormigón", 130), ("carpeta asfáltica", 70), ("tratamiento bituminoso", 70), ("empedrado", 65)]:
        add(Ri, ARQ, f"tasa de conservación de pavimento: frente a {c}", monto=m, unidad_monto="UYU de 2016 por metro de frente al año", vigencia="desde 2016")
    for z, m in [(1, 485), (2, 388), (3, 259), (4, 153), (5, 81), (6, 78), (7, 57)]:
        add(Ri, ALUM, f"zona {z} (potencia instalada por cuadra)", monto=m, unidad_monto="UYU de 2016", vigencia="desde 2016", notas="zona 1 más de 1.250 W; zona 7 menos de 150 W")
    R00 = do("2000-12-21")
    for c, rate in [("frente a Av. Sarandí, 33 Orientales y Paul Harris", 10), ("frente a calles de hormigón", 5), ("frente a calles bituminosas", 3.5), ("frente a calles empedradas", 1.5),
                    ("frente a balasto con cordón y cuneta", 1), ("frente a otras calles", 0.5)]:
        add(Ri, BALD, f"baldíos {c}", base="valor real catastral", tasa=rate, vigencia="desde 2001", fuente=R00,
            notas="alícuota rebajada 50% por el Dec. 3724/2000; sin rebaja (el doble) si hay construcciones no regularizadas detectadas antes de fraccionar (Ordenanza 10/11)")
    add(Ri, EDIF, "edificación inapropiada", notas="mismas alícuotas que los baldíos", vigencia="desde 2001", fuente=R00)
    add(Ri, CIU, "tributación mínima por padrón (contribución + higiene + baldío)", monto=1.5, unidad_monto="UR anuales", vigencia="desde 2001", fuente=R00)
    add(Ri, CIU, "contribuyentes cumplidores", tasa=-15, vigencia="desde 2001", fuente=R00)
    add(Ri, CIU, "pasivos con único padrón e ingresos del hogar hasta 10 UR", tasa=-50, vigencia="desde 2001", fuente=R00, notas="100% del impuesto a baldíos")
    add(Ri, "Tasa General Municipal", "derogada en Rivera desde 2001 (sustituida por la tasa de higiene)", tasa=0, vigencia="desde 2001", fuente=R00)
    add(Ri, ESPEC, "espectáculos públicos", base="valor de las entradas", tasa=10, vigencia="desde 2011", fuente=R11)
    add(Ri, ESPEC, "espectáculos con más de 1.000 entradas vendidas", base="valor de las entradas", tasa=8, vigencia="desde 2011", fuente=R11)
    add(Ri, TERM, "derecho de embarque en la Terminal de Ómnibus de Rivera", monto=0.06, unidad_monto="UR por pasajero", vigencia="desde 2011", fuente=R11)
    add(Ri, TERM, "toque de andén por salida de ómnibus", monto=0.25, unidad_monto="UR", confianza="guia_oficial", fuente="https://www.rivera.gub.uy/portal/tasas/")
    add(Ri, NEC, "tasa de necrópolis", monto=3, unidad_monto="UR anuales", confianza="guia_oficial", fuente="https://www.rivera.gub.uy/portal/tasas/")
    add(Ri, "Ocupación de espacios públicos", "Paseo 33 Orientales, por puesto", monto=1, unidad_monto="UR", confianza="guia_oficial", fuente="https://www.rivera.gub.uy/portal/tasas/")
    add(Ri, "Tasa General Municipal", "residuos industriales recogidos por la intendencia", monto=0.25, unidad_monto="UR por m³", vigencia="desde 2016", notas="solo disposición final: 1 UR por tonelada")
    add(Ri, PAT, "descuento especial para camiones", tasa=-30, vigencia="desde 2011", fuente=R11)
    add(Ri, VEXT, "vehículos extranjeros usados por residentes", notas="tabla de aforo propia (2012 ajustada por IPC)", fuente="https://www.rivera.gub.uy/portal/cobro-del-impuesto-a-la-circulacion-de-vehiculos-extranjeros-para-el-ejercicio-2016/")

    # --- Soriano: Recopilación Impositiva Municipal (RIM), changes of 2011 and 2016 ------------------------------
    So, S16 = "Soriano", do("2016-06-16")
    add(So, CIU, "escala de tasas progresivas de la RIM", notas="la escala no se publicó en los presupuestos 2011/2016/2026")
    add(So, CIU, "cooperativas de vivienda y grupos habitacionales BHU/ANV sin escriturar", base="valor real catastral", tasa=0.6, vigencia="desde 2011")
    add(So, CIU, "padrones que pasan de rurales a urbanos o suburbanos por el plan de ordenamiento", base="valor real catastral", tasa=0.6, vigencia="desde 2017", fuente=S16)
    add(So, CIU, "ídem con emprendimiento de al menos 10 personas", base="valor real catastral", tasa=0.3, vigencia="desde 2017", fuente=S16)
    add(So, CIU, "contribuyente con varios bienes, todos al día", tasa=-3, vigencia="desde 2011", notas="aplica a todos los tributos salvo la contribución rural")
    add(So, ALUM, "cocheras de edificios", base="tasa de la zona", tasa=30, vigencia="desde 2011")
    add(So, "Tasa General Municipal", "disposición final de envases PET o PVC: más de 1 litro / hasta 1 litro", monto="0,35 / 0,25", unidad_monto="UYU de 2011 por envase", vigencia="desde 2011", notas="sobre 80% de lo introducido al departamento")
    add(So, PAT, "chapas de prueba", monto=2, unidad_monto="UR mensuales", vigencia="desde 2011")
    add(So, TRAN, "permiso de circulación de 0 km (48 h) / certificado libre de multas", monto="2 / 1", unidad_monto="UR", vigencia="desde 2011")
    add(So, TRAN, "depósito de vehículos: menores / mayores", monto="0,5 / 2", unidad_monto="UR mensuales", vigencia="desde 2016", fuente=S16)
    add(So, ARQ, "inspecciones de Arquitectura: suelo urbano / suburbano y rural", monto="0,5 / 1", unidad_monto="UR por inspección", vigencia="desde 2011")
    add(So, ARQ, "fraccionamientos urbanos: 2-9 / 10-19 / 20-49 / 50-99 / 100+ solares", monto="6 / 15 / 26,5 / 49,7 / 85", unidad_monto="UR", vigencia="desde 2011", notas="suburbano × 0,75; rural 1 UR por fracción; PH × 1,5")

    # --- Durazno: additional 2016 rows (Presupuesto 2016-2020) -----------------------------------------------
    Du, D16 = "Durazno", do("2016-08-04")
    add(Du, CIU, "suelo suburbano (Decretos 2181/2011 y 2315/2014)", base="valor real catastral", tasa=1.25, vigencia="desde 2016", fuente=D16)
    add(Du, CIU, "edificaciones posteriores a 2007 bajo la cota de inundación", base="valor real catastral", tasa=5, vigencia="desde 2016", fuente=D16)
    add(Du, CIU, "jubilados y pensionistas con ingresos hasta 4 BPC, única propiedad", tasa=-100, vigencia="desde 2016", fuente=D16)
    add(Du, ADIC, "impuesto solidario al Fondo de Contingencia de Cambio Climático (inmuebles no rurales)", monto=50, unidad_monto="UYU de 2016 anuales", vigencia="desde 2016", fuente=D16)
    for c, m in [("hormigón", 800), ("carpeta asfáltica", 500), ("tratamiento bituminoso", 360), ("balasto", 0)]:
        add(Du, ARQ, f"tasa de conservación de pavimento: frente a {c}", monto=m, unidad_monto="UYU de 2016 anuales", vigencia="desde 2017", fuente=D16)
    for z, m in [("1", 260), ("2", 260), ("3", 150), ("4", 95), ("5", 60)]:
        add(Du, ALUM, f"zona {z} (art. 81 del Dec. 1664/2001)", monto=m, unidad_monto="UYU de 2016 mensuales", vigencia="desde 2016", fuente=D16)
    add(Du, TERM, "toque de andén en la Terminal de Durazno", monto=120, unidad_monto="UYU de 2016 por coche", vigencia="desde 2016", fuente=D16)
    add(Du, NEC, "apertura de parcela en cementerios privados / contralor de cremación", monto="2 / 2", unidad_monto="UR", vigencia="desde 2016", fuente=D16)
    add(Du, BROM, "controles / inspecciones / exámenes", monto="250 / 400 / 800", unidad_monto="UYU de 2016", vigencia="desde 2016", fuente=D16)
    add(Du, BROM, "carné de manipulador de alimentos (3 años)", monto=320, unidad_monto="UYU de 2016", vigencia="desde 2016", fuente=D16)
    add(Du, MEJ, "obras que benefician solo a frentistas / también a no frentistas", monto="30% / 20%", unidad_monto="del costo de la obra", vigencia="desde 2016", fuente=D16)
    add(Du, "Tasa de caminería rural", "vehículos con más de 20 t de carga neta en caminería departamental", monto=1200, unidad_monto="UYU de 2016 por vehículo", vigencia="desde su reglamentación", fuente=D16)

    # --- Tacuarembó: Decreto 06/2026 over the Digesto Departamental ------------------------------------------------
    Ta, T16 = "Tacuarembó", do("2016-07-05")
    for c, m in [("examen de planos", 0.4), ("estudio urbanístico", 0.2), ("autorización para edificar o regularizar", 2)]:
        add(Ta, ARQ, c, base="valor de tasación de la obra", tasa=m / 10, notas=f"{m} por mil")
    add(Ta, ARQ, "puertas, ventanas o portones al frente / refacción de frentes / muro al frente", monto="150 por abertura / 30 por m² / 30 por m", unidad_monto="UI")
    add(Ta, ARQ, "barreras de obra", monto=60, unidad_monto="UI por metro lineal al mes")
    add(Ta, ARQ, "fraccionamiento hasta 5 fracciones", base="valor imponible", tasa=1, fuente=do("2026-09-08"), notas="más de 5: 300 UI adicionales por solar")
    for f, m in [("A", 123), ("B", 88), ("C", 69), ("D", 33)]:
        add(Ta, ALUM, f"franja {f}", monto=m, unidad_monto="UYU de 2016 mensuales", vigencia="desde 2016", fuente=T16)
    add(Ta, ALUM, "beneficiarios del bono social de UTE", tasa=-30)
    for c, b in [("ingresos menores a 3 BPC", -100), ("menores a 4 BPC", -50), ("menores a 6 BPC", -25)]:
        add(Ta, CIU, f"jubilados mayores de 60, mujeres solas jefas de hogar o personas con discapacidad, vivienda única: {c}", tasa=b)
    add(Ta, CIU, "padrones del Museo Abierto de San Gregorio de Polanco", tasa=-25, notas="hasta")
    add(Ta, CIU, "descuento por construcción de veredas nuevas", base="costo de la vereda", tasa=-30, vigencia="desde 2011", fuente=do("2011-08-22"))
    add(Ta, ADM, "valorado departamental por gestión", monto=100, unidad_monto="UYU de 2016 (ajuste anual por IPC)", vigencia="desde 2016", fuente=T16)
    add(Ta, TRAN, "afectación de vehículo a remise", base="valor del vehículo 0 km con IMESI e IVA", tasa=10, vigencia="desde 2016", fuente=T16)
    add(Ta, PAT, "bonificación adicional a ciclomotores sin multas", tasa=-10, vigencia="desde 2011", fuente=do("2011-08-22"))

    # --- Treinta y Tres --------------------------------------------------------------------------------------
    Tt = "Treinta y Tres"
    for f, m in [("A (mejor servicio)", 36), ("B", 28), ("C (más de un NIS por padrón, núcleos habitacionales, interior)", 20), ("D (sin alumbrado)", 0)]:
        add(Tt, ALUM, f"Alumbrado Público Diferencial, franja {f}", monto=m, unidad_monto="UYU de 2001 mensuales", vigencia="desde 2001", notas="se cobra en la factura de UTE")
    add(Tt, CIU, "bonificación por pago contado", tasa=-15, vigencia="desde 2021", fuente=do("2021-10-01"), notas="desde 2022 igual a la variación del IPC con tope 15%; incluye tasas de salubridad y pavimento")
    add(Tt, CIU, "bonificación de buen pagador", tasa=-10, vigencia="desde 2022", fuente=do("2021-10-01"))

    # --- Salto ------------------------------------------------------------------------------------------------
    Sa = "Salto"
    add(Sa, CIU, "escala por franjas del Decreto 6.109/01", notas="la escala no se publicó en los presupuestos 2011/2021/2026")
    add(Sa, CIU, "buen pagador / dos años o más", monto="-10% / -12%", unidad_monto="descuento", vigencia="2021-2025", fuente=do("2020-12-31"))
    for c, m in [("más de 200 m²", 860), ("30 a 200 m²", 573), ("hasta 30 m²", 287)]:
        add(Sa, HIG, f"inspección de condiciones higiénicas de locales de alimentos: {c}", monto=m, unidad_monto="UYU de 2011", vigencia="desde 2011")

    # --- Flores ---------------------------------------------------------------------------------------------
    Fl = "Flores"
    add(Fl, CIU, "jubilados y pensionistas con hasta 4 BPC, vivienda única: valor real mayor a $1.000.000", tasa=-50, vigencia="desde 2027", notas="tramos menores con bonificación mayor")
    add(Fl, CIU, "inmuebles con grado de protección patrimonial 2 / 3 / 4 en el Área Central de Trinidad", monto="-25% / -50% / -100%", unidad_monto="exoneración", vigencia="desde 2016", fuente=do("2016-06-27"))
    add(Fl, MEJ, "mayor aprovechamiento (edificar sobre el coeficiente básico)", base="mayor valor", desde=0, hasta=50, unidad_tramo="% de contrapartida", vigencia="desde 2016", fuente=do("2016-06-27"))

    # --- Rocha -------------------------------------------------------------------------------------------
    R = "Rocha"
    add(R, CIR, "alícuota fijada por ley nacional (Ley 9.189)", base="valor real catastral", notas="recauda la intendencia")
    add(R, CIU, "zona A (Rocha, La Paloma, La Aguada, Costa Azul, Balneario Atlántico, Parque La Paloma, Antoniópolis, Arachania, La Pedrera, Punta del Diablo)", base="valor real catastral", tasa=2)
    add(R, CIU, "zona B1 desarrollo urbano: zonas 2 de Lascano, Castillos, Chuy y Barra del Chuy", base="valor real catastral", tasa=1.7, monto=3, unidad_monto="UR mínimo")
    add(R, CIU, "zona B1: zonas 3", base="valor real catastral", tasa=1.5, monto=1.5, unidad_monto="UR mínimo")
    add(R, CIU, "zona B1: resto de las localidades (FZ)", base="valor real catastral", tasa=0.5, monto=1.5, unidad_monto="UR mínimo")
    add(R, CIU, "Chuy, padrones frente a Av. Internacional y Gral. Artigas", base="valor real catastral", tasa=6, monto=14, unidad_monto="UR mínimo", notas="3% si el valor está actualizado")
    add(R, CIU, "zona B2 desarrollo urbano turístico", base="valor real catastral", desde=0.5, hasta=1.7, unidad_tramo="% (rango por localidad)", monto="1,5 a 7", unidad_monto="UR mínimo")
    add(R, CIU, "zona B3 urbanización concertada", base="valor real catastral", desde=1.7, hasta=2, unidad_tramo="% (rango por localidad)", monto="4 a 8", unidad_monto="UR mínimo")
    for d, h, m in [(1, 1, 2), (2, 5, 5), (6, 10, 11), (11, 15, 14), (16, 20, 18), (21, 30, 24)]:
        add(R, CIU, "zona B4 fraccionamientos costeros de baja intensidad", base="solares del padrón", desde=d, hasta=h, unidad_tramo="solares", monto=m, unidad_monto="UR anuales")
    for d, h, m in [(0, 1.5, 6), (1.5, 3, 12), (3, 5, 20), (5, 10, 25), (10, 20, 30), (20, 50, 35), (50, "", 40)]:
        add(R, CIU, "zona B5 padrones suburbanos", base="área del padrón", desde=d, hasta=h, unidad_tramo="ha", monto=m, unidad_monto="UR anuales")
    add(R, CIU, "bonificación por pago contado y buen pagador", tasa=-10, notas="5% contado más 5% buen pagador, más 1% por año de buen pagador hasta 5%")
    add(R, ADIC, "impuesto de salud bucal y bienestar animal (todos los inmuebles urbanos y suburbanos)", monto=0.3, unidad_monto="UR anuales", notas="el cuadro de zonas muestra 0,1 + 0,1 UR")
    add(R, ADIC, "impuesto de fomento al turismo (localidades sobre el océano Atlántico)", monto=1, unidad_monto="UR anuales")
    for z, m in [("1", 6), ("2", 4), ("3", 3), ("FZ (fuera de zona)", 2)]:
        add(R, IGM, f"zona {z}", monto=m, unidad_monto="UR anuales", notas="financia limpieza y recolección")
    for z, m in [("1", 4), ("2", 3), ("3", 3), ("FZ (fuera de zona)", 1)]:
        add(R, ALUM, f"zona {z}", monto=m, unidad_monto="UR anuales")
    for lit, m, n in [("a) sin permiso de construcción o contenedores no autorizados", 20, ""),
                      ("b) permiso con observaciones sin resolver", 10, "15 UR desde el cuarto ejercicio y 20 UR desde el quinto"),
                      ("c) construcción donde no se autoriza edificar", 30, ""), ("d y e) fincas ruinosas o actividades sin viabilidad de uso", 35, ""),
                      ("f) construcciones paralizadas con deterioro", 40, ""),
                      ("construcciones en áreas protegidas o zonas fiscales", 60, "15 UR en las zonas fiscales de Aguas Dulces y Valizas")]:
        add(R, EDIF, lit, monto=m, unidad_monto="UR anuales por edificación", notas=n)
    add(R, BALD, "baldíos de Rocha, La Paloma, Castillos, Lascano y Chuy (zonas indicadas)", base="Contribución Inmobiliaria del inmueble", tasa=35, notas="acumulable a la contribución")
    add(R, PAT, "régimen SUCIVE (Ley 18.860)", notas="ver la fila nacional del SUCIVE; ciclomotores hasta 125 cc exonerados")
    add(R, VEXT, "vehículos con matrícula de Brasil u otro país usados habitualmente por residentes", base="patente de un vehículo similar en el SUCIVE", tasa=50)
    add(R, ESPEC, "espectáculos con venta de entradas", base="entradas vendidas", tasa=10)
    add(R, ESPEC, "espectáculos deportivos", base="entradas vendidas", tasa=4, notas="10% en instalaciones de la intendencia")
    add(R, ESPEC, "espectáculos sin entrada", base="concurrentes estimados", monto=0.02, unidad_monto="UR por concurrente")
    add(R, PROP, "cartelería frente a rutas", base="metro cuadrado", monto=2, unidad_monto="UR por m² al año (máximo 15 UR)")
    add(R, PROP, "avisos en la vía pública", base="metro cuadrado", desde=3, hasta=40, unidad_tramo="UR por m² al año (rango)")
    add(R, PROP, "publicidad en vehículos", monto="1 (birodados) / 1,5 (automotores)", unidad_monto="UR por mes")
    add(R, REM, "remates", base="precio de venta", tasa=1)
    for c, m in [("control", 1), ("inspección", 3), ("examen", 5)]:
        add(R, BROM, f"cada {c} de alimentos", monto=m, unidad_monto="UR")
    for c, m in [("vacuno", 1.8), ("ternero", 0.75), ("ovino", 0.125), ("cerdo", 1.2), ("lechón hasta 18 kg", 0.25)]:
        add(R, HIG, f"faena en mataderos municipales: {c}", monto=m, unidad_monto="UR por animal")
    add(R, HIG, "limpieza de baldíos por la intendencia", base="superficie", monto=1, unidad_monto="UR cada 100 m²")
    add(R, HIG, "control de barométricas particulares", monto=3, unidad_monto="UR por trimestre")
    for c, m in [("inhumación", 1.5), ("apertura de nicho o panteón", 0.75), ("exhumación", 1), ("alquiler de nicho por 3 años", 9),
                 ("transferencia de nicho", 5), ("transferencia de panteón", 8), ("servicio fúnebre (empresas)", 2.5)]:
        add(R, NEC, c, monto=m, unidad_monto="UR")
    add(R, ADM, "foja valorada por trámite", monto=0.25, unidad_monto="UR")
    add(R, ADM, "derecho de expedición por comprobante", monto=0.35, unidad_monto="UR")
    add(R, ADM, "estampilla municipal por comprobante", monto=0.25, unidad_monto="UR", notas="1 UR anual para contribución y patente")
    add(R, TRAN, "certificado para reempadronar en otro departamento", monto=5, unidad_monto="UR")
    add(R, TRAN, "reincorporación de vehículo dado de baja", monto=4, unidad_monto="UR")
    for c, m in [("hormigón armado", 15), ("adoquín", 10), ("bituminoso", 4), ("balasto", 1)]:
        add(R, ARQ, f"reparación de pavimento: {c}", monto=f"4 + {m} por m²", unidad_monto="UR")
    add(R, MEJ, "obras públicas departamentales", base="costo de la obra prorrateado", notas="no puede superar la contribución inmobiliaria del inmueble; hasta 30 años")
    add(R, AMB, "visitantes de áreas protegidas (Cabo Polonio, Isla del Padre, Bañado de los Indios)", monto=0.05, unidad_monto="UR por visitante")
    add(R, TERM, "pasajeros que embarcan en terminales de Rocha, Castillos, Chuy, Aguas Dulces y La Pedrera", monto=10, unidad_monto="UYU por pasaje", notas="ajuste anual por IPC")
    add(R, HAB, "comercios en áreas protegidas o zonas fiscales", monto=30, unidad_monto="UR anuales", notas="más 30 UR de higiene ambiental")

    # --- Durazno (the 2026 budget only changes some articles of Decreto 1664/2001) -------------------------
    D = "Durazno"
    for d, h, t in [(0, 670954, 0.32), (670954, 1341911, 0.8), (1341911, 2683817, 1.28), (2683817, "", 1.6)]:
        add(D, CIU, "Sarandí del Yí (20% menos que la escala general del Dec. 1664/2001)", base="valor real vigente", desde=d, hasta=h, unidad_tramo="UYU", tasa=t,
            notas="se aplica la alícuota del tramo al valor total; la escala general del resto del departamento no está en el presupuesto 2026")
    for z, m in [("1", 375), ("2", 150), ("3", 100), ("4", 50), ("5", 40)]:
        add(D, BALD, f"zona {z}", base="metro cuadrado", monto=m, unidad_monto="UYU por m² al año",
            notas="el texto en letras de la zona 1 dice trescientos sesenta y cinco" if z == "1" else "exonerados los baldíos 100% en zonas 4 y 5 si están limpios")
    for c, m in [("más de 400 m² y más de 20 empleados", 3), ("más de 400 m² y menos de 20 empleados", 1.5), ("200 a 399 m² y 10 a 19 empleados", 1.5),
                 ("200 a 399 m² y menos de 10 empleados", 1), ("menos de 200 m² y menos de 10 empleados", 0.5)]:
        add(D, HIG, f"control de higiene y salubridad ambiental de comercios e industrias: {c}", monto=m, unidad_monto="UR por inspección", notas="al menos dos inspecciones al año")
    for c, m in [("inhumación en tubular", 0.6), ("inhumación en nicho", 0.75), ("inhumación en panteón", 1), ("apertura de nicho", 0.75),
                 ("reducción de restos en panteón particular", 1.5), ("depósito de urna en urnario", 0.4)]:
        add(D, NEC, c, monto=m, unidad_monto="UR")
    add(D, PROP, "avisos y propaganda", notas="derogado por el presupuesto 2026 (art. 105)", tasa=0)
    D01, V01 = do("2001-12-26"), "desde 2002 (Dec. 1664/2001)"
    for i, (d, h, rate) in enumerate([(0, 100000, 0.5), (100000, 200000, 1), (200000, 400000, 1.6), (400000, "", 2)]):
        add(D, CIU, f"escala general, franja {i + 1}", base="valor real vigente", desde=d, hasta=h, unidad_tramo="UYU de 2001 (se ajusta con el valor real)", tasa=rate, vigencia=V01, fuente=D01,
            notas="en 2026 los límites equivalen a $670.954 / $1.341.911 / $2.683.817")
    add(D, CIU, "cooperativas de vivienda no fraccionadas", tasa=1, vigencia=V01, fuente=D01, notas="tope de alícuota")
    add(D, EDIF, "edificación inapropiada, ruinosa, clausurada, tapiada o inconclusa", base="Contribución Inmobiliaria urbana", tasa=150, vigencia=V01, fuente=D01)
    for z, m in [("1", 70), ("2", 70), ("3", 40), ("4", 25), ("5", 15)]:
        add(D, "Tasa General Municipal", f"tasa de salubridad, zona {z}", monto=m, unidad_monto="UYU de 2001 mensuales (ajuste por IPC)", vigencia=V01, fuente=D01)
        add(D, AMB, f"tasa de desarrollo urbanístico y medio ambiente (baldíos o sin luz), zona {z}", monto=m, unidad_monto="UYU de 2001 mensuales", vigencia=V01, fuente=D01)
    add(D, ARQ, "estudio de planos sin permiso simultáneo", base="avaluación de la obra", tasa=0.2, monto=500, unidad_monto="UYU de 2001 mínimo", vigencia=V01, fuente=D01)
    add(D, ARQ, "fraccionamiento: inicio / por fracción / amanzanamiento", monto="500 / 40 / 1.000", unidad_monto="UYU de 2001", vigencia=V01, fuente=D01)
    add(D, "Guías de propiedad y tránsito de semovientes", "tasa de trámite por guía DICOSE (opcional)", monto=5, unidad_monto="UYU de 2001 (ajuste por IPC)", vigencia=V01, fuente=D01)
    add(D, "Ocupación de espacios públicos", "quioscos permanentes zona 1 / zona 2", monto="1.200 / 720", unidad_monto="UYU de 2001 mensuales", vigencia=V01, fuente=D01)

    # --- Río Negro ---------------------------------------------------------------------------------------
    N = "Río Negro"
    for d, h, t in [(0, 763340, 0.25), (763340, 1908350, 0.7), (1908350, 5438799, 1.5), (5438799, 100617800, 1.75), (100617800, "", 3.5)]:
        add(N, CIU, "Fray Bentos y Young (escala progresiva por tramos)", base="valor real", desde=d, hasta=h, unidad_tramo="UYU", tasa=t)
    for d, h, t in [(0, 283421, 0.5), (283421, 944736, 1), (944736, 2874210, 1.3), (2874210, 53180725, 1.5), (53180725, "", 3)]:
        add(N, CIU, "resto del departamento (alícuota del tramo sobre el valor total)", base="valor real", desde=d, hasta=h, unidad_tramo="UYU", tasa=t)
    add(N, CIU, "inmuebles declarados fuera de ordenamiento territorial", base="alícuota que corresponda", tasa=200, notas="pagan el doble")
    add(N, CIR, "alícuota fijada por ley nacional", base="valor real catastral", notas="enclaves rurales categorizados como suburbanos pagan la rural más 20%")
    add(N, IGM, "Impuesto General, parte de salubridad, limpieza y conservación", base="valor imponible de la contribución urbana", tasa=0.35, monto=0.5, unidad_monto="UR mínimo")
    for c, m in [("Fray Bentos y Young zona 1, Las Cañas", 8091), ("Fray Bentos y Young zona 2, Los Arrayanes manzanas 3 a 16", 4634),
                 ("Fray Bentos zona 3", 2076), ("zonas 4 y 5 y otras localidades", 994), ("hogares con tarifa social de UTE (MIDES)", 862)]:
        add(N, ALUM, f"Impuesto General, parte de alumbrado público: {c}", monto=m, unidad_monto="UYU anuales (valores a ene-2025)", notas="se cobra mensualmente en la factura de UTE")
    for c, t in [("Fray Bentos y Young zona 1", 5), ("Fray Bentos y Young zona 2", 4), ("Fray Bentos y Young zona 3", 2), ("balnearios Las Cañas y Los Arrayanes", 12)]:
        add(N, BALD, c, base="valor imponible de la contribución urbana", tasa=t)
    for c, t in [("Fray Bentos y Young zona 1", 2), ("Fray Bentos y Young zona 2", 1.5), ("Fray Bentos y Young zona 3", 1),
                 ("zonas suburbanas de crecimiento", 0.5), ("Las Cañas y Los Arrayanes", 2), ("Nuevo Berlín y San Javier", 1)]:
        add(N, EDIF, c, base="valor imponible de la contribución urbana", tasa=t, notas="falta de veredas o de conexión a saneamiento: 50% de las alícuotas de baldío")
    add(N, PAT, "régimen SUCIVE (Ley 18.860)")
    add(N, ESPEC, "cada espectáculo con cobro de entradas", monto=1, unidad_monto="UR por solicitud", notas="salas de cine o teatro: opción de 3 UR mensuales fictas")
    add(N, PROP, "letreros de 10 a 20 m² (empresas sin domicilio en el departamento)", base="metro cuadrado", monto=0.5, unidad_monto="UR por m² al año")
    add(N, PROP, "letreros de más de 20 m²", base="metro cuadrado", monto=0.25, unidad_monto="UR por m² al año")
    add(N, PROP, "aparatos de proyección hacia la vía pública", monto="5 (sede propia) / 10 (fuera)", unidad_monto="UR anuales")
    add(N, REM, "remates", base="producido del remate", tasa=1)
    add(N, ARQ, "inspección técnica de obras", monto=1, unidad_monto="UR por inspección", notas="obras menores 0,3 UR; anticipo de estudio técnico 0,04 UR por m²")
    add(N, HAB, "estudio e inspección de locales comerciales o industriales", monto=1, unidad_monto="UR por unidad")
    add(N, HIG, "habilitación de inmuebles para arrendamiento", monto=1.5, unidad_monto="UR")

    # --- Artigas -----------------------------------------------------------------------------------------
    A = "Artigas"
    for d, h, t in [(0, 325363, 0), (325363, 650722, 0.55), (650722, 976087, 0.6), (976087, 1301454, 0.65), (1301454, 1626812, 0.7),
                    (1626812, 1952177, 0.75), (1952177, 2277538, 0.85), (2277538, 2602896, 0.9), (2602896, 2928265, 0.95), (2928265, "", 1)]:
        add(A, CIU, "escala por valor (valores al 31/12/2025)", base="valor real", desde=d, hasta=h, unidad_tramo="UYU", tasa=t,
            notas="hasta $325.363 exonerado del impuesto pero no de las tasas adicionales")
    for z, t in [("zona A de Artigas y Bella Unión", 12), ("zona B de Artigas y Bella Unión", 6), ("zonas C y D de Artigas y C de Bella Unión", 1.5)]:
        add(A, BALD, z, base="valor real", tasa=t, notas="incluye edificación menor a 32 m²")
    for z, t in [("zona A de Artigas y Bella Unión", 15), ("zona B de Artigas y Bella Unión", 9), ("zonas C y D de Artigas y C de Bella Unión", 3)]:
        add(A, EDIF, z, base="valor real", tasa=t)
    add(A, PAT, "régimen SUCIVE (Ley 18.860)", notas="cambio de categoría o motor 4 UR; permiso de chapa de alquiler 4 UR más 20 UR")
    add(A, ESPEC, "locales de bailes y similares (habilitación anual)", base="personas habilitadas a concurrir", monto=0.01, unidad_monto="UR por persona al año")
    add(A, PROP, "avisos fijos con frente a la vía pública", base="metro cuadrado", monto=1.5, unidad_monto="UR por m² al año")
    add(A, PROP, "propaganda oral o acústica con parlantes fijos", monto=1.5, unidad_monto="UR por parlante al mes")
    add(A, PROP, "propaganda en vehículos", monto="1 (birodados) / 2 (automotores)", unidad_monto="UR por mes")
    add(A, PROP, "anuncios en pantallas de salas o espacios públicos", monto=0.05, unidad_monto="UR por hora")
    add(A, HIG, "inspección de higiene de locales hasta 350 m²", base="metro cuadrado", monto=0.02, unidad_monto="UR por m² al año", notas="doble si hay materiales peligrosos")
    add(A, HIG, "inspección de higiene de locales de más de 350 m²", monto=7, unidad_monto="UR anuales")
    add(A, HIG, "vehículos de transporte de alimentos", monto="2 a 3", unidad_monto="UR según peso")
    add(A, HIG, "habilitación de locales de remates ferias / remates de mercaderías", monto="15 / 5", unidad_monto="UR anuales")
    add(A, BROM, "acto de inspección o contralor", monto="1 a 3", unidad_monto="UR según riesgo, más el costo de los análisis")
    add(A, BROM, "registro RUNAEV de empresa / producto / local / vehículo", monto="1 / 5 / 4 / 5", unidad_monto="UR")
    add(A, ARQ, "estudio y aprobación de planos de obra nueva o ampliación", base="metro cuadrado", monto=0.1, unidad_monto="UR por m²", notas="regularización 0,20; reforma 0,03 a 0,23 UR por m²")
    add(A, ARQ, "habilitación de obra / demolición / plano de ajuste", monto="1 / 1 / 2", unidad_monto="UR")
    add(A, ARQ, "perforaciones en la vía pública", monto=40, unidad_monto="UR por perforación")
    add(A, TRAN, "inspección de vehículos a pedido del interesado", monto=2, unidad_monto="UR")
    add(A, ADM, "retiro de expedientes del archivo", monto=0.5, unidad_monto="UR")
    add(A, NEC, "derecho de urna en posa urnas (5 años) / parcela en cementerio rural", monto="0,5 / 2", unidad_monto="UR")
    add(A, MEJ, "obras públicas urbanas y rurales", base="costo de la obra", notas="hasta 20% del costo en zona urbana y 50% en rural; la cuota no supera 50% de la contribución")

    # --- Cerro Largo (the 2026 budget only adds or changes some fees) ----------------------------------------
    C = "Cerro Largo"
    add(C, HAB, "contralor estructural, sanitario y ambiental de comercios con más de 200 m² de venta", base="metro cuadrado de exposición y venta", monto=0.05, unidad_monto="UR por m²")
    for c, m in [("ómnibus departamental, por entrada o salida de la terminal", 0.066), ("ómnibus urbano", 0.045), ("ómnibus interdepartamental, por salida", 0.12),
                 ("ómnibus regional, por salida", 0.07)]:
        add(C, TERM, f"tasa de contralor de ómnibus: {c}", monto=m, unidad_monto="UR por día o por unidad")
    add(C, CIU, "descuento por pago anticipado de cuotas", tasa=-5, notas="la escala de alícuotas no está en el presupuesto 2026")

    # --- Paysandú ----------------------------------------------------------------------------------------
    P = "Paysandú"
    add(P, CIU, "ciudades y centros poblados (incluye Pay Chacras)", base="valor catastral", tasa=1.1)
    add(P, CIU, "centros termales (Guaviyú y Almirón)", base="valor catastral", tasa=1.4)
    for z, t in [("zona 1 de la ciudad de Paysandú", 12), ("zona 2", 7), ("zona 3", 1), ("centros termales Guaviyú y Almirón", 25)]:
        add(P, BALD, z, base="valor catastral", tasa=t, notas="zona 1: terreno que vale 5 veces o más que lo construido; zona 2: 10 veces o más")
    add(P, EDIF, "fincas ruinosas, clausuradas o inconclusas sin permiso", base="valor catastral", tasa=3)
    add(P, EDIF, "otras edificaciones inapropiadas (literales d a g)", base="valor catastral", tasa=5)
    add(P, PAT, "régimen SUCIVE, fijado por el Congreso de Intendentes")
    add(P, PROP, "letreros y avisos", notas="cuantía por remisión al Dec. 5231/2006; sobre más de 100 avisos se paga 25%")
    add(P, ESPEC, "apuestas mutuas en competencias (salvo carreras de caballos)", base="monto bruto apostado", tasa=5, notas="lo retiene el organizador")
    add(P, ESPEC, "rifas y sorteos: derecho de permiso", base="valor nominal de la emisión", tasa=6.667, notas="más 10% de la diferencia entre premios y boletos vendidos")
    add(P, REM, "cada remate", monto=421, unidad_monto="UI por remate")
    for c, m in [("instituciones financieras, loterías y casas de cambio", 4506), ("teatros y cines", 939), ("clubes nocturnos y similares", 1875),
                 ("casas de huéspedes", 470), ("hoteles, por habitación", 106), ("demás locales hasta 25 m²", 281), ("de 25 a 50 m²", 658),
                 ("de 50 a 100 m²", 1217), ("de 100 a 1.000 m²", 2812), ("de 1.000 a 5.000 m²", 4216)]:
        add(P, HIG, f"contralor de higiene ambiental: {c}", monto=m, unidad_monto="UI anuales por local")
    add(P, HIG, "salones con máquinas electrónicas", monto="820 a 6.552", unidad_monto="UI anuales según superficie")
    for c, m in [("inhumación en nicho o panteón", 28), ("inhumación en tierra", 46), ("conservación anual de nichos", 44), ("conservación anual de panteones", 191),
                 ("conservación anual de solares", 96)]:
        add(P, NEC, c, monto=m, unidad_monto="UI")
    add(P, ADM, "tributo por tramitación", monto=8, unidad_monto="UI por tributo", notas="5 tributos por expediente")
    add(P, ADM, "partidas y certificados del Registro Civil", monto="10 a 16", unidad_monto="UI")
    add(P, TRAN, "Permiso Único Nacional de Conducir", monto=1.25, unidad_monto="UR", notas="renovaciones cortas pagan 20% a 80%")
    add(P, ARQ, "construcción / reparación de veredas por la intendencia", base="metro cuadrado", monto="2.400 / 1.200", unidad_monto="UYU por m²")
    add(P, MEJ, "mayor aprovechamiento por cambio de categoría de suelo / mayor edificabilidad", base="mayor edificabilidad", desde=10, hasta=15, unidad_tramo="% (precio compensatorio)")

    # --- Florida (the 2026 budget only changes some articles) --------------------------------------------------
    F = "Florida"
    add(F, CIU, "bonificación por pago contado anual sin deudas (desde 2027)", tasa=-10, notas="buenos pagadores 5% a 9% por cuota; la escala de alícuotas no está en el presupuesto 2026")
    add(F, ARQ, "permiso de obra en la vía pública", monto=2, unidad_monto="UR")
    add(F, ALUM, "tasa de alumbrado público por franjas según el servicio frente al inmueble", notas="se cobra en la factura de UTE; montos por franja no transcritos")
    return out
