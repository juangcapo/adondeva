"""Departmental tax rates, transcribed from each intendencia's 2026-2030 budget (Presupuesto Quinquenal).

Each entry is (catalog tributo name, row). build_rates.py prefixes the department to `condicion`, fills the
`departamento` column and merges these rows into the tributo's file under departamental/.
The budget texts are kept in departamental/raw/presupuestos_2026/ for checking the details (per-locality tables).
"""

DEPT_SOURCES = {
    "Montevideo": ("https://tramites.montevideo.gub.uy/sites/tramites.montevideo.gub.uy/files/tributos/documentos/2026_Calculo_Contribucio%CC%81n_Inmobiliaria.pdf", "Cálculo de Contribución Inmobiliaria 2026 (IM)"),
    "Canelones": ("https://datosuruguay.com/contribucion-inmobiliaria/canelones", "guía de terceros"),
    "Colonia": ("https://datosuruguay.com/contribucion-inmobiliaria/colonia", "guía de terceros"),
    "Maldonado": ("https://www.revistacero.com.uy/ajustan-la-contribucion-inmobiliaria-y-tributos-asociados-en-maldonado-regiran-desde-enero-de-2026/", "prensa sobre la Resolución 11905/2025"),
    "Rocha": ("https://www.impo.com.uy/diariooficial/2026/04/10/documentos.pdf", "Decreto 1/2026, Presupuesto Quinquenal 2026-2030"),
    "Durazno": ("https://www.impo.com.uy/diariooficial/2026/07/01/documentos.pdf", "Presupuesto Quinquenal 2026-2030 (modifica el Dec. 1664/2001)"),
    "Río Negro": ("https://www.impo.com.uy/diariooficial/2026/07/03/documentos.pdf", "Decreto 38/2026, Presupuesto Quinquenal 2026-2030"),
    "Artigas": ("https://www.impo.com.uy/diariooficial/2026/07/27/documentos.pdf", "Presupuesto Quinquenal 2026-2030"),
    "Cerro Largo": ("https://www.impo.com.uy/diariooficial/2026/07/06/documentos.pdf", "Decreto 2/2026, Presupuesto Quinquenal 2026-2030"),
    "Paysandú": ("https://www.impo.com.uy/diariooficial/2026/08/07/documentos.pdf", "Presupuesto Quinquenal 2026-2030"),
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


def rows(r):
    """Return [(department, tributo, row)]. `r` is build_rates.r, passed in to avoid an import cycle."""
    out = []

    def add(dept, tributo, condicion, **kw):
        kw.setdefault("vigencia", "2026-2030")
        kw.setdefault("confianza", "oficial")
        out.append((dept, tributo, r(condicion, **kw)))

    # --- Montevideo -------------------------------------------------------------------------------------
    M = "Montevideo"
    for d, h, tt in [(0, 992630, 0.25), (992630, 2481576, 0.75), (2481576, 4963144, 1), (4963144, 8551753, 1.2), (8551753, 17103509, 1.65), (17103509, "", 1.8)]:
        add(M, CIU, "escala progresiva por tramos", base="valor imponible 2026", desde=d, hasta=h, unidad_tramo="UYU", tasa=tt, vigencia="2026")
    add(M, CIU, "primer tramo para inmuebles con valor imponible menor a $2.481.577", base="valor imponible 2026", desde=0, hasta=992630, unidad_tramo="UYU", tasa=0.18, vigencia="2026", notas="en lugar de 0,25% (Decreto 38.156)")
    add(M, ADIC, "vivienda deshabitada al menos un año", base="Contribución Inmobiliaria", tasa=100, confianza="secundaria", vigencia="2026",
        notas="la IM propuso derogarlo desde 2027; fuente: https://www.montevideo.com.uy/Noticias/Intendencia-de-Montevideo-propone-pagar-la-Contribucion-Inmobiliaria-en-hasta-12-cuotas-uc967809")

    # --- Canelones, Colonia, Maldonado: no 2026 budget text with rates found; third-party or press figures ----
    add("Canelones", CIU, "alícuotas según zona y categoría", base="valor catastral", desde=0.45, hasta=1.9, unidad_tramo="% (rango)", confianza="secundaria", vigencia="2026")
    add("Colonia", CIU, "padrones urbanos", base="valor catastral", desde=0.74, hasta=1.99, unidad_tramo="% (rango)", confianza="secundaria", vigencia="2026", notas="Texto Ordenado de Tributos e Ingresos de la Junta Departamental")
    add("Colonia", CIU, "padrones suburbanos", base="valor catastral", desde=1.2, hasta=2.45, unidad_tramo="% (rango)", confianza="secundaria", vigencia="2026")
    add("Maldonado", CIU, "escala progresiva; mínimo anual", monto=4616, unidad_monto="UYU mínimo anual", confianza="secundaria", vigencia="2026", notas="ajuste 2026 de 4,09% por IPC (Res. 11905/2025); muchos padrones de balnearios en las franjas de 3% a 5%")
    add("Maldonado", ADIC, "Adicional Impuesto General Ambiental (desde 2026)", monto=4616, unidad_monto="UYU mínimo anual", confianza="secundaria", vigencia="2026")
    add("Maldonado", ALUM, "adicional de alumbrado público", monto=2046, unidad_monto="UYU mínimo anual", confianza="secundaria", vigencia="2026")
    add("Maldonado", ARQ, "tasa de conservación de pavimento", monto=2046, unidad_monto="UYU mínimo anual", confianza="secundaria", vigencia="2026")

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
