"""adondeva web: HTTP API over adondeva.py, plus the built React frontend.

Run from the repo root:
  .venv/bin/uvicorn web.backend.app:app --reload
"""
import csv
import sys
import threading
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
import adondeva as ad  # noqa: E402

FRONTEND = (REPO / "web" / "frontend" / "dist").resolve()

# adondeva's file cache is a plain JSON file: serialize anything that may write it.
DATA_LOCK = threading.Lock()


def bad_request(fn, *args):
    """Run an adondeva helper, turning its sys.exit(message) into a 400."""
    try:
        return fn(*args)
    except SystemExit as e:
        raise HTTPException(400, str(e.code)) from None


# ---------------------------------------------------------------- cached loaders

@lru_cache
def ipc():
    return ad.load_ipc()


@lru_cache(maxsize=2)
def spending_series(include_fondos_terceros):
    with DATA_LOCK:
        return ad.spending_series(include_fondos_terceros)


@lru_cache(maxsize=4)
def detail_rows(year):
    source, path = ad.detail_sources()[year]
    with DATA_LOCK:
        return source, ad.detail_opp_year(path) if source == "opp" else ad.detail_mef_year(path)


@lru_cache
def arancel():
    with open(ad.ARANCEL, encoding="utf-8") as f:
        return [{k: r[k] for k in ("ncm", "descripcion", "tga_extrazona_pct", "tga_intrazona_pct")}
                for r in csv.DictReader(f)]


@asynccontextmanager
async def warm_up(_):
    """Read the large files in the background so the first visitor does not wait 15 seconds."""
    def work():
        spending_series(False)
        detail_rows(max(ad.detail_sources()))
    threading.Thread(target=work, daemon=True).start()
    yield


app = FastAPI(title="adondeva", docs_url="/api/docs", openapi_url="/api/openapi.json", lifespan=warm_up)


# ---------------------------------------------------------------- endpoints

DATASETS = [
    {"id": "opp-historico", "nombre": "Ejecución presupuestal 1961–2010", "organismo": "OPP",
     "url": "https://transparenciapresupuestaria.opp.gub.uy/inicio/datos-abiertos",
     "detalle": "Gasto ejecutado por inciso y año, en miles de pesos corrientes. Sin desglose por programa ni objeto del gasto.",
     "advertencias": ["Hasta 1984 la amortización de deuda se contaba en el inciso 20, así que 1980–1984 dan algo alto.",
                      "Los valores anteriores a los cambios de moneda de 1975 y 1993 ya vienen convertidos a pesos actuales."]},
    {"id": "opp", "nombre": "Crédito presupuestal detallado 2011–2024", "organismo": "OPP",
     "url": "https://transparenciapresupuestaria.opp.gub.uy/inicio/datos-abiertos",
     "detalle": "Un CSV por año: apertura, crédito y ejecutado por inciso, unidad ejecutora, programa, proyecto, objeto del gasto y financiación.",
     "advertencias": ["El archivo de 2025 de OPP llega solo a mitad de año; para 2025 se usa MEF.",
                      "OPP reemplaza archivos sin aviso (el de 2021 cambió más de un año después)."]},
    {"id": "mef", "nombre": "Rendición de Cuentas 2025", "organismo": "MEF",
     "url": "https://www.gub.uy/ministerio-economia-finanzas/comunicacion/publicaciones/rendicion-cuentas-balance-ejecucion-presupuestal-ejercicio-2025-datos",
     "detalle": "Crédito y obligado de 2025 con el mismo nivel de detalle que OPP. Publicado el 30 de junio de 2026.",
     "advertencias": ["MEF incluye «Fondos de Terceros Declarados por Ley» (cerca del 1% del gasto), que OPP no cuenta; se excluye para comparar años.",
                      "MEF publica datos abiertos solo para 2025; los años anteriores están únicamente en PDF."]},
    {"id": "ine-ipc", "nombre": "Índice de Precios del Consumo (base oct. 2022 = 100)", "organismo": "INE",
     "url": "https://www.gub.uy/instituto-nacional-estadistica/datos-y-estadisticas/estadisticas/series-historicas-ipc-base-octubre-2022100",
     "detalle": "Índice mensual desde julio de 1937 y anual con promedio, diciembre e inflación medida de las dos formas.",
     "advertencias": ["El sitio www5.ine.gub.uy no envía su certificado intermedio."]},
    {"id": "impuestos", "nombre": "Impuestos, tasas y contribuciones", "organismo": "Compilado por adondeva",
     "url": "https://github.com/juangcapo/adondeva/tree/main/data/uy/taxes",
     "detalle": "Cada impuesto, tasa y contribución de Uruguay con sus tasas, por nivel: nacional, organismos, aduana, seguridad social y departamental.",
     "advertencias": ["Valores de BPC, UR y UI de valores_referencia.csv; hay que actualizarlos cuando BPS publica nuevos."]},
    {"id": "aranceles", "nombre": "Aranceles de importación", "organismo": "Compilado por adondeva",
     "url": "https://github.com/juangcapo/adondeva/tree/main/data/uy/aranceles",
     "detalle": "Arancel de cada código NCM, cambios pendientes y comparación del régimen de envíos 2024 vs 2026.",
     "advertencias": ["La tasa consular proviene de una fuente secundaria."]},
]


@app.get("/api/sources")
def sources():
    by_source = {}
    for y, (_, src) in spending_series(False).items():
        by_source.setdefault(src, []).append(y)
    coverage = {src: {"desde": min(ys), "hasta": max(ys), "anios": len(ys)} for src, ys in by_source.items()}
    coverage["ine-ipc"] = {"desde": min(ipc()), "hasta": max(ipc()), "anios": len(ipc())}
    with open(ad.TAXES / "catalog.csv", encoding="utf-8") as f:
        catalog = list(csv.DictReader(f))
    return {"datasets": [d | {"cobertura": coverage.get(d["id"])} for d in DATASETS], "impuestos": catalog}


@app.get("/api/spending")
def spending(base: int | None = None, fondos_terceros: bool = False):
    series, prices = spending_series(fondos_terceros), ipc()
    usable = sorted(y for y in series if y in prices)
    base = base or usable[-1]
    if base not in prices:
        raise HTTPException(400, f"No hay IPC anual para {base}.")
    return {"base": base, "anios": [
        {"anio": y, "fuente": series[y][1], "nominal": series[y][0],
         "real": series[y][0] * prices[base]["ipc_promedio"] / prices[y]["ipc_promedio"]}
        for y in usable]}


@app.get("/api/breakdown")
def breakdown(year: int | None = None, path: list[str] = Query([]), fondos_terceros: bool = False):
    years = sorted(ad.detail_sources())
    year = year or years[-1]
    if year not in years:
        raise HTTPException(404, f"No hay presupuesto detallado para {year}. Disponible: {years[0]}–{years[-1]}.")
    if len(path) >= len(ad.BREAKDOWN_LEVELS):
        raise HTTPException(400, f"Como máximo {len(ad.BREAKDOWN_LEVELS) - 1} selecciones.")
    source, rows = detail_rows(year)
    if not fondos_terceros:
        rows = [r for r in rows if r[8] != ad.FONDOS_TERCEROS]
    chosen = []
    for depth, selector in enumerate(path):
        value, _ = ad.pick(selector, [k for k, _, _ in ad.ranking(rows, depth)])
        if value is None:
            raise HTTPException(404, f"«{selector}» no corresponde a un único valor de {ad.BREAKDOWN_LEVELS[depth]}.")
        chosen.append(value)
        rows = [r for r in rows if r[depth] == value]
    ranked = ad.ranking(rows, len(chosen))
    return {"anio": year, "fuente": source, "anios": years, "niveles": ad.BREAKDOWN_LEVELS,
            "camino": chosen, "nivel": len(chosen),
            "items": [{"nombre": k, "credito": b, "gasto": s} for k, b, s in ranked],
            "total": {"credito": sum(b for _, b, _ in ranked), "gasto": sum(s for _, _, s in ranked)}}


@app.get("/api/tax/{accion}")
def tax(accion: Literal["sueldo", "compra", "importar", "alquiler"], monto: float = Query(gt=0),
        hijos: int = Query(0, ge=0), conyuge: bool = False,
        tasa: Literal["basica", "minima", "debito", "exento"] = "basica", neto: bool = False,
        ncm: str | None = None, arancel: float | None = Query(None, ge=0), mercosur: bool = False,
        contribuyente: bool = False, envio: bool = False, eeuu: bool = False, cupo: float = Query(800, ge=0)):
    args = SimpleNamespace(hijos=hijos, conyuge=conyuge, tasa=tasa, neto=neto, ncm=ncm, arancel=arancel,
                           mercosur=mercosur, contribuyente=contribuyente, envio=envio, eeuu=eeuu, cupo=cupo)
    rows, totals, unit = bad_request(ad.TAX_ACTIONS[accion], monto, args)
    return {"unidad": unit,
            "filas": [{"paga": who, "concepto": c, "base": b, "tasa": t, "monto": m} for who, c, b, t, m in rows],
            "totales": [{"nombre": n, "valor": v} for n, v in totals]}


@app.get("/api/ncm")
def ncm(q: str = Query(min_length=2), limit: int = Query(20, le=100)):
    """Tariff lines whose code starts with `q` or whose description contains it."""
    want, digits = ad.fold(q), q.replace(".", "")
    hits = [r for r in arancel()
            if (digits.isdigit() and r["ncm"].replace(".", "").startswith(digits)) or want in ad.fold(r["descripcion"])]
    return hits[:limit]


# ---------------------------------------------------------------- frontend

if FRONTEND.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")

    @app.get("/{page:path}", include_in_schema=False)
    def spa(page: str):
        """Client-side routes all load index.html; React picks the page."""
        if page.startswith("api/"):
            raise HTTPException(404)
        file = (FRONTEND / page).resolve()
        ok = page and file.is_relative_to(FRONTEND) and file.is_file()
        return FileResponse(file if ok else FRONTEND / "index.html")
