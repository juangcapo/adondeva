// ARCE's own lists (comprasestatales.gub.uy/consultas), so the cases are filed and filtered the way ARCE does it.

/** "Organismo contratante": ARCE's incisos, by number. */
export const INCISOS: [number, string][] = [
  [1, 'Poder Legislativo'], [2, 'Presidencia de la República'], [3, 'Ministerio de Defensa Nacional'],
  [4, 'Ministerio del Interior'], [5, 'Ministerio de Economía y Finanzas'], [6, 'Ministerio de Relaciones Exteriores'],
  [7, 'Ministerio de Ganadería, Agricultura y Pesca'], [8, 'Ministerio de Industria, Energía y Minería'],
  [9, 'Ministerio de Turismo'], [10, 'Ministerio de Transporte y Obras Públicas'], [11, 'Ministerio de Educación y Cultura'],
  [12, 'Ministerio de Salud Pública'], [13, 'Ministerio de Trabajo y Seguridad Social'],
  [14, 'Ministerio de Vivienda y Ordenamiento Territorial'], [15, 'Ministerio de Desarrollo Social'], [16, 'Poder Judicial'],
  [17, 'Tribunal de Cuentas'], [18, 'Corte Electoral'], [19, 'Tribunal de lo Contencioso Administrativo'],
  [24, 'Diversos Créditos'], [25, 'Administración Nacional de Educación Pública'], [26, 'Universidad de la República'],
  [27, 'Instituto del Niño y Adolescente del Uruguay'], [28, 'Banco de Previsión Social'],
  [29, 'Administración de Servicios de Salud del Estado'], [30, 'Deuda Pública'], [31, 'Universidad Tecnológica del Uruguay'],
  [32, 'Instituto Uruguayo de Meteorología'], [33, 'Fiscalía General de la Nación'],
  [34, 'Junta de Transparencia y Ética Pública'], [35, 'Instituto Nacional de Inclusión Social Adolescente'],
  [36, 'Ministerio de Ambiente'], [40, 'Instituciones sin fines de lucro públicas'], [47, 'Cajas paraestatales'],
  [50, 'Banco Central del Uruguay'], [51, 'Banco de la República Oriental del Uruguay'], [52, 'Banco Hipotecario del Uruguay'],
  [53, 'Banco de Seguros del Estado'], [59, 'Organismos Financieros Internacionales'],
  [60, 'Administración Nacional de Combustible, Alcohol y Portland'],
  [61, 'Administración Nacional de Usinas y Trasmisiones Eléctricas'], [62, 'Administración de los Ferrocarriles del Estado'],
  [63, 'Primera Líneas Uruguayas de Navegación Aérea'], [64, 'Administración Nacional de Puertos'],
  [65, 'Administración Nacional de Telecomunicaciones'], [66, 'Administración de las Obras Sanitarias del Estado'],
  [67, 'Administración Nacional de Correos'], [68, 'Agencia Nacional de Vivienda'],
  [69, 'Unidad Reguladora de Servicios de Energía y Agua'], [70, 'Instituto Nacional de Colonización'],
  [71, 'Unidad Reguladora de Servicios de Comunicaciones'], [72, 'Instituto Nacional de Carnes'],
  [79, 'Intendencias Municipales (sin discriminar)'], [80, 'Intendencia de Artigas'], [81, 'Intendencia de Canelones'],
  [82, 'Intendencia de Cerro Largo'], [83, 'Intendencia de Colonia'], [84, 'Intendencia de Durazno'],
  [85, 'Intendencia de Flores'], [86, 'Intendencia de Florida'], [87, 'Intendencia de Lavalleja'],
  [88, 'Intendencia de Maldonado'], [89, 'Intendencia de Paysandú'], [90, 'Intendencia de Río Negro'],
  [91, 'Intendencia de Rivera'], [92, 'Intendencia de Rocha'], [93, 'Intendencia de Salto'], [94, 'Intendencia de San José'],
  [95, 'Intendencia de Soriano'], [96, 'Intendencia de Tacuarembó'], [97, 'Intendencia de Treinta y Tres'],
  [98, 'Intendencia de Montevideo'], [99, 'Congreso de Intendentes'],
]

/** ARCE's number for an inciso name, to sort the dropdown as ARCE does; names not on the list go last. */
export const incisoNumero = (nombre: string) => INCISOS.find(([, n]) => n === nombre)?.[0] ?? 1000

/** "Tipo de contratación", as ARCE lists them. */
export const TIPOS_CONTRATACION = [
  'Arrendamiento de Obra', 'Compra Directa', 'Compra por Excepción', 'Compra por Sistema Dinámico',
  'Compra Pública Innovadora', 'Concesión', 'Concurso de Precios', 'Convenio Marco', 'Diálogo Técnico',
  'Licitación Abreviada', 'Licitación Pública', 'Llamado a Expresiones de Interés', 'PFI - Comparación de precios',
  'PFI - Contratación directa', 'PFI - Licitación internacional limitada', 'PFI - Licitación pública internacional',
  'PFI - Licitación pública nacional', 'Pregón', 'Procedimiento Especial', 'Sistema Dinámico de Adquisición',
  'Solicitud de Información', 'Venta/Arrendamiento Concurso de Precios', 'Venta/Arrendamiento Directa',
  'Venta/Arrendamiento Licitación Abreviada', 'Venta/Arrendamiento Licitación Pública', 'Venta/Arrendamiento por Excepción',
  'Venta/Arrendamiento por Remate',
]
