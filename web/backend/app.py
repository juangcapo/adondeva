"""adondeva web: HTTP API over adondeva.py, plus the built React frontend.

Run from the repo root:
  .venv/bin/uvicorn web.backend.app:app --reload
"""
import csv
import json
import os
import secrets
import sys
import threading
import time
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
import adondeva as ad  # noqa: E402

from . import noticias, uso  # noqa: E402

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


@lru_cache
def revenue():
    return ad.load_revenue()


@lru_cache(maxsize=2)
def spending_series(include_fondos_terceros):
    with DATA_LOCK:
        return ad.spending_series(include_fondos_terceros)


# One year only: each takes ~70 MB as Python objects, and keeping 4 got the 512 MB machine OOM-killed.
# Changing year re-reads its file (~0.4 s); drilling down within a year stays cached.
@lru_cache(maxsize=1)
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


# ---------------------------------------------------------------- usage log, limits and headers

# API paths that are not queries about the data: the log's own endpoints, health checks and docs.
NOT_LOGGED = ("/api/hit", "/api/health", "/api/admin", "/api/docs", "/api/openapi.json")

# Per client IP and minute. /api/breakdown re-reads a large file for years out of the cache (~0.5 s of CPU),
# so it gets a tighter limit than the rest; /api/hit is written to disk.
LIMITS = {"api": uso.Limiter(300, 60), "/api/breakdown": uso.Limiter(60, 60), "/api/hit": uso.Limiter(120, 60)}
# Wrong admin passwords: 10 per IP every 15 minutes, then 429 until the window passes.
ADMIN_FAILURES = uso.Limiter(10, 15 * 60)

# The frontend loads nothing from other sites. Styles stay 'unsafe-inline' for the chart library's inline styles.
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
    "Strict-Transport-Security": "max-age=31536000",
}


def secure(response, path):
    response.headers.update(HEADERS)
    if not path.startswith("/api/docs"):  # Swagger UI loads its scripts from a CDN
        response.headers["Content-Security-Policy"] = CSP
    if path.startswith(("/admin", "/api/admin")):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Robots-Tag"] = "noindex"
    elif path.startswith("/assets/") and response.status_code == 200:
        # File names carry a content hash, so browsers and Cloudflare can keep them for good.
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


@app.middleware("http")
async def guard(request: Request, call_next):
    """Origin lock and www redirect, rate limits, then the request, then the usage log and security headers."""
    path = request.url.path
    # With Cloudflare in front (CF_ORIGIN_SECRET set), only requests through it are served: direct visits to
    # adondeva.fly.dev would skip its bot protection and could forge the visitor's IP. Fly's health check
    # reaches the machine directly, so it stays open.
    if os.environ.get("CF_ORIGIN_SECRET") and path != "/api/health" and not uso.from_cloudflare(request):
        return secure(PlainTextResponse("Acceso directo no permitido.", 403), path)
    canonical = os.environ.get("CANONICAL_HOST")
    if canonical and request.headers.get("host", "").split(":")[0] == f"www.{canonical}":
        query = f"?{request.url.query}" if request.url.query else ""
        return secure(RedirectResponse(f"https://{canonical}{path}{query}", 301), path)
    if path.startswith("/api/") and path != "/api/health":
        ip = uso.client_ip(request)
        if not all(lim.allow(ip) for key, lim in LIMITS.items() if key == "api" or key == path):
            return secure(JSONResponse({"detail": "Demasiadas consultas; probá de nuevo en un minuto."}, 429,
                                       headers={"Retry-After": "60"}), path)
    start = time.perf_counter()
    response = await call_next(request)
    if path.startswith("/api/") and not path.startswith(NOT_LOGGED):
        try:
            uso.record(tipo="api", ruta=path[:200], params=uso.params_json(request.query_params),
                       estado=response.status_code, ms=round((time.perf_counter() - start) * 1000, 1),
                       **uso.details(request))
        except Exception as e:  # the log must never break a request
            print(f"uso: {e}", flush=True)
    return secure(response, path)


class Hit(BaseModel):
    """A page view or an interaction the API doesn't see (sent by the frontend)."""
    tipo: Literal["pagina", "evento"]
    ruta: str = Field(max_length=300)
    referrer: str | None = Field(None, max_length=1000)
    datos: dict | None = None


YEAR = range(1900, 2101)
# The interactions the frontend sends, with the values each field may take; anything else is rejected,
# so the reports only ever show values the site itself produces.
EVENTS = {
    "recaudacion-impuesto": {"sigla": "tax", "accion": {"agregar", "quitar"}},
    "recaudacion-vista": {"vista": {"grupo", "impuesto"}, "modo": {"real", "nominal", "pct"}, "desde": YEAR},
    "gasto-vista": {"modo": {"real", "nominal"}, "desde": YEAR},
    "donar": {},
    "noticia-abrir": {"id": "noticia"},
}


def valid_event(name, datos):
    spec = EVENTS.get(name)
    if spec is None or not isinstance(datos, dict) or set(datos) != set(spec):
        return False
    for k, allowed in spec.items():
        v = datos[k]
        if allowed == "tax":
            ok = isinstance(v, str) and v in revenue()[0]
        elif allowed == "noticia":
            ok = isinstance(v, int) and not isinstance(v, bool) and any(n["id"] == v for n in noticias.listar())
        elif allowed is YEAR:
            ok = isinstance(v, int) and not isinstance(v, bool) and v in YEAR
        else:
            ok = v in allowed
        if not ok:
            return False
    return True


@app.post("/api/hit", status_code=204)
def hit(h: Hit, request: Request):
    if h.tipo == "pagina":
        if not h.ruta.startswith("/") or h.ruta.startswith("//") or any(ord(c) < 32 for c in h.ruta) or h.datos:
            raise HTTPException(422, "Página inválida.")
        datos = None
    else:
        if not valid_event(h.ruta, h.datos):
            raise HTTPException(422, "Evento desconocido.")
        datos = json.dumps(h.datos, ensure_ascii=False)
    uso.record(tipo=h.tipo, ruta=h.ruta, params=datos, referrer=uso.referrer(h.referrer), **uso.details(request))


@app.get("/api/health", include_in_schema=False)
def health():
    return {"ok": True}


# The admin page and its data need ADMIN_PASSWORD (a Fly secret); without it they stay off.
basic = HTTPBasic(realm="adondeva admin", auto_error=False)


def admin(request: Request, creds: HTTPBasicCredentials | None = Depends(basic)):
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not password:
        raise HTTPException(404)
    ip = uso.client_ip(request)
    if ADMIN_FAILURES.blocked(ip):
        raise HTTPException(429, "Demasiados intentos fallidos; probá de nuevo en 15 minutos.")
    ok = creds and secrets.compare_digest(creds.username.encode(), b"admin") \
        and secrets.compare_digest(creds.password.encode(), password.encode())
    if not ok:
        if creds:  # the browser's first, empty request is not an attempt
            ADMIN_FAILURES.add(ip)
        raise HTTPException(401, "Usuario o contraseña incorrectos.", headers={"WWW-Authenticate": 'Basic realm="adondeva admin"'})


def same_origin(request: Request):
    """Admin writes only from the site's own pages: the browser sends the saved password with any request,
    so a page on another site could otherwise make it post or delete (CSRF)."""
    origin = request.headers.get("origin")
    site = request.headers.get("sec-fetch-site")
    if (origin and origin.split("://", 1)[-1] != request.headers.get("host")) or site not in (None, "same-origin", "none"):
        raise HTTPException(403, "Origen no permitido.")


ADMIN_WRITE = [Depends(admin), Depends(same_origin)]


@app.get("/api/noticias")
def noticias_lista():
    return noticias.listar()


@app.get("/api/noticias/{slug}")
def noticia(slug: str):
    n = noticias.por_slug(slug)
    if not n:
        raise HTTPException(404, "Esta nota no existe.")
    return n


@app.get("/api/admin/noticias", dependencies=[Depends(admin)], include_in_schema=False)
def admin_noticias():
    return noticias.listar(todas=True)


@app.post("/api/admin/noticias", status_code=201, dependencies=ADMIN_WRITE, include_in_schema=False)
def admin_noticia_nueva(n: noticias.Noticia):
    return noticias.guardar(n)


@app.put("/api/admin/noticias/{id}", dependencies=ADMIN_WRITE, include_in_schema=False)
def admin_noticia_editar(id: int, n: noticias.Noticia):
    saved = noticias.guardar(n, id)
    if not saved:
        raise HTTPException(404, "Esa noticia no existe.")
    return saved


@app.delete("/api/admin/noticias/{id}", status_code=204, dependencies=ADMIN_WRITE, include_in_schema=False)
def admin_noticia_borrar(id: int):
    if not noticias.borrar(id):
        raise HTTPException(404, "Esa noticia no existe.")


@app.get("/api/admin/stats", dependencies=[Depends(admin)], include_in_schema=False)
def admin_stats(dias: int = Query(30, ge=1, le=3650)):
    out = uso.stats(dias)
    taxes = revenue()[0]
    for t in out["impuestos"]:
        t["nombre"] = taxes[t["sigla"]]["nombre"] if t["sigla"] in taxes else t["sigla"]
    return out


@app.get("/api/admin/export.csv", dependencies=[Depends(admin)], include_in_schema=False)
def admin_export(dias: int | None = Query(None, ge=1, le=3650)):
    return PlainTextResponse(uso.export_csv(dias), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": 'attachment; filename="adondeva-usos.csv"'})


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
    {"id": "dgi", "nombre": "Recaudación por impuesto", "organismo": "DGI",
     "url": "https://www.gub.uy/direccion-general-impositiva/datos-y-estadisticas/estadisticas/recaudacion-anual-mensual-impuesto",
     "detalle": "Lo que recaudó la DGI cada año, impuesto por impuesto, en pesos corrientes (criterio de caja).",
     "advertencias": ["Hasta 1989 la DGI detalla solo 5 o 6 impuestos: entre 9% y 16% del total queda en «Otros y ajustes».",
                      "No incluye aportes a la seguridad social (BPS), aranceles de Aduanas ni tributos departamentales."]},
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
    years = revenue()[1]
    coverage["dgi"] = {"desde": min(years), "hasta": max(years), "anios": len(years)}
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


@app.get("/api/revenue")
def revenue_series(base: int | None = None):
    """DGI collections per year and tax; `factor` turns a year's pesos into pesos of `base`."""
    (taxes, amounts), prices = revenue(), ipc()
    usable = sorted(y for y in amounts if y in prices)
    base = base or usable[-1]
    if base not in prices:
        raise HTTPException(400, f"No hay IPC anual para {base}.")
    return {"base": base, "grupos": ad.REVENUE_GROUPS,
            "impuestos": [{k: t[k] for k in ("sigla", "nombre", "grupo", "desde", "hasta")} for t in taxes.values()],
            "anios": [{"anio": y, "total": amounts[y]["TOTAL"],
                       "factor": prices[base]["ipc_promedio"] / prices[y]["ipc_promedio"],
                       "montos": {s: x for s, x in amounts[y].items() if s != "TOTAL"}}
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
def tax(accion: Literal["sueldo", "compra", "importar", "alquiler"], monto: float = Query(gt=0, allow_inf_nan=False),
        hijos: int = Query(0, ge=0), conyuge: bool = False,
        tasa: Literal["basica", "minima", "debito", "exento"] = "basica", neto: bool = False,
        ncm: str | None = None, arancel: float | None = Query(None, ge=0, allow_inf_nan=False), mercosur: bool = False,
        contribuyente: bool = False, envio: bool = False, eeuu: bool = False, cupo: float = Query(800, ge=0, allow_inf_nan=False)):
    args = SimpleNamespace(hijos=hijos, conyuge=conyuge, tasa=tasa, neto=neto, ncm=ncm, arancel=arancel,
                           mercosur=mercosur, contribuyente=contribuyente, envio=envio, eeuu=eeuu, cupo=cupo)
    rows, totals, unit = bad_request(ad.TAX_ACTIONS[accion], monto, args)
    return {"unidad": unit,
            "filas": [{"paga": who, "concepto": c, "base": b, "tasa": t, "monto": m} for who, c, b, t, m in rows],
            "totales": [{"nombre": n, "valor": v} for n, v in totals]}


@app.get("/api/ncm")
def ncm(q: str = Query(min_length=2), limit: int = Query(20, ge=1, le=100)):
    """Tariff lines whose code starts with `q` or whose description contains it."""
    want, digits = ad.fold(q), q.strip().replace(".", "")
    if len(want) < 2:
        raise HTTPException(400, "Escribí al menos 2 caracteres.")
    hits = [r for r in arancel()
            if (digits.isdigit() and r["ncm"].replace(".", "").startswith(digits)) or want in ad.fold(r["descripcion"])]
    return hits[:limit]


# ---------------------------------------------------------------- frontend

if FRONTEND.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")

    @app.get("/{page:path}", include_in_schema=False)
    def spa(page: str, request: Request, creds: HTTPBasicCredentials | None = Depends(basic)):
        """Client-side routes all load index.html; React picks the page."""
        if page.startswith("api/"):
            raise HTTPException(404)
        if page.strip("/").split("/")[0] == "admin":
            admin(request, creds)  # ask for the password up front, so the page's API calls carry it
        file = (FRONTEND / page).resolve()
        ok = page and file.is_relative_to(FRONTEND) and file.is_file()
        return FileResponse(file if ok else FRONTEND / "index.html")
