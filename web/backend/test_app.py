"""Run from the repo root: .venv/bin/pytest web/backend"""
import csv
import io
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# Log to a throwaway database, and turn the admin page on with a known password.
os.environ["USO_DB"] = os.path.join(tempfile.mkdtemp(), "uso.db")
os.environ["CONTENIDO_DB"] = os.path.join(tempfile.mkdtemp(), "contenido.db")
os.environ["ADMIN_PASSWORD"] = "secreta"

from web.backend import uso  # noqa: E402
from web.backend.app import app  # noqa: E402

client = TestClient(app)


def get(url, **params):
    r = client.get(url, params=params)
    assert r.status_code == 200, r.text
    return r.json()


def test_sources_cover_every_dataset():
    data = get("/api/sources")
    assert {d["id"] for d in data["datasets"] if d["cobertura"]} >= {"opp-historico", "opp", "mef", "ine-ipc", "dgi"}
    assert any(t["sigla"] == "IVA" for t in data["impuestos"])


def test_spending_real_equals_nominal_in_base_year():
    data = get("/api/spending", base=2020)
    row = next(r for r in data["anios"] if r["anio"] == 2020)
    assert row["real"] == pytest.approx(row["nominal"])


def test_revenue_taxes_add_up_to_dgi_total():
    data = get("/api/revenue")
    grupos = {t["sigla"]: t["grupo"] for t in data["impuestos"]}
    assert set(grupos.values()) <= set(data["grupos"])
    for year in data["anios"]:
        assert all(s in grupos for s in year["montos"])
        assert sum(year["montos"].values()) == pytest.approx(year["total"])
    last = data["anios"][-1]
    assert last["anio"] == data["base"] and last["factor"] == pytest.approx(1)


def test_revenue_unknown_base_is_400():
    assert client.get("/api/revenue", params={"base": 1800}).status_code == 400


def test_breakdown_drills_one_level_per_selection():
    top = get("/api/breakdown", year=2024)
    assert top["nivel"] == 0 and top["camino"] == []
    first = top["items"][0]["nombre"]
    inner = client.get("/api/breakdown", params=[("year", 2024), ("path", first)]).json()
    assert inner["nivel"] == 1 and inner["camino"] == [first]
    assert inner["total"]["gasto"] == pytest.approx(top["items"][0]["gasto"])


def test_breakdown_unknown_selection_is_404():
    assert client.get("/api/breakdown", params={"year": 2024, "path": "zzzz"}).status_code == 404


def test_tax_sueldo_matches_readme_example():
    data = get("/api/tax/sueldo", monto=80000, hijos=1)
    totals = {t["nombre"]: t["valor"] for t in data["totales"]}
    assert totals["sueldo líquido"] == pytest.approx(62601.60)


def test_tax_importar_without_code_is_400():
    assert client.get("/api/tax/importar", params={"monto": 1000}).status_code == 400


def test_ncm_search_by_code_and_text():
    assert get("/api/ncm", q="8471.30")[0]["ncm"].startswith("8471.30")
    assert get("/api/ncm", q="cafe")


def test_ncm_rejects_blank_query_and_bad_limit():
    assert client.get("/api/ncm", params={"q": "   "}).status_code == 400
    assert client.get("/api/ncm", params={"q": "8471", "limit": -3}).status_code == 422


ADMIN = ("admin", "secreta")


def test_usage_log_records_queries_pages_and_events_without_ip():
    browser = {"user-agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/130.0 Safari/537.36"}
    client.get("/api/tax/sueldo", params={"monto": 50000, "hijos": 2}, headers=browser)
    client.get("/api/breakdown", params=[("year", 2024), ("path", "1"), ("path", "2")], headers=browser)
    client.get("/api/health", headers=browser)
    client.post("/api/hit", json={"tipo": "pagina", "ruta": "/recaudacion", "referrer": "https://example.com/"}, headers=browser)
    client.post("/api/hit", json={"tipo": "evento", "ruta": "recaudacion-impuesto", "datos": {"sigla": "IVA", "accion": "agregar"}}, headers=browser)
    uso.flush()

    rows = list(csv.DictReader(io.StringIO(client.get("/api/admin/export.csv", auth=ADMIN).text)))
    assert "testclient" not in "".join(str(r) for r in rows)  # the client's address is never stored
    assert not any(r["ruta"] == "/api/health" for r in rows)
    tax = next(r for r in rows if r["params"] == '{"monto": "50000", "hijos": "2"}')
    assert tax["ruta"] == "/api/tax/sueldo" and tax["navegador"] == "Chrome" and tax["bot"] == "0"
    assert any(r["params"] == '{"year": "2024", "path": ["1", "2"]}' for r in rows)

    stats = get_admin("/api/admin/stats", dias=7)
    assert stats["totales"]["paginas"] >= 1 and stats["totales"]["visitantes"] >= 1
    assert any(r["nombre"] == "/recaudacion" for r in stats["paginas"])
    assert any(r["nombre"] == "sueldo" for r in stats["calculadora"])
    iva = next(t for t in stats["impuestos"] if t["sigla"] == "IVA")
    assert iva["nombre"] == "IVA (valor agregado)" and iva["visitantes"] == 1 and iva["agregado"] == 1


def get_admin(url, **params):
    r = client.get(url, params=params, auth=ADMIN)
    assert r.status_code == 200, r.text
    return r.json()


def test_admin_needs_the_password():
    assert client.get("/api/admin/stats").status_code == 401
    assert client.get("/api/admin/stats", auth=("admin", "otra")).status_code == 401


def test_hit_accepts_only_known_pages_and_events():
    ok = {"tipo": "evento", "ruta": "recaudacion-impuesto", "datos": {"sigla": "IVA", "accion": "agregar"}}
    assert client.post("/api/hit", json=ok).status_code == 204
    for bad in [
        {"tipo": "evento", "ruta": "x", "datos": {"a": "x" * 3000}},
        {"tipo": "evento", "ruta": "recaudacion-impuesto", "datos": {"sigla": "=cmd", "accion": "agregar"}},
        {"tipo": "evento", "ruta": "recaudacion-impuesto", "datos": {"sigla": "IVA", "accion": "agregar", "x": 1}},
        {"tipo": "evento", "ruta": "gasto-vista", "datos": {"modo": "real", "desde": True}},
        {"tipo": "pagina", "ruta": "https://evil.example/"},
        {"tipo": "pagina", "ruta": "//evil.example/"},
        {"tipo": "otro", "ruta": "/"},
    ]:
        assert client.post("/api/hit", json=bad).status_code == 422, bad


def test_referrer_keeps_only_site_and_path():
    client.post("/api/hit", json={"tipo": "pagina", "ruta": "/fuentes",
                                  "referrer": "https://mail.example.com/inbox?email=ana@example.com#x"})
    uso.flush()
    rows = client.get("/api/admin/export.csv", auth=ADMIN).text
    assert "https://mail.example.com/inbox" in rows and "ana@example.com" not in rows


def test_csv_export_neutralizes_formulas():
    assert uso.safe_cell("=HYPERLINK(1)") == "'=HYPERLINK(1)" and uso.safe_cell("/api/x") == "/api/x"


def test_security_headers_and_infinite_amounts():
    r = client.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff" and "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert client.get("/api/admin/stats", auth=ADMIN).headers["cache-control"] == "no-store"
    for v in ["inf", "1e309", "nan"]:
        assert client.get("/api/tax/compra", params={"monto": v}).status_code == 422


def test_rate_limit_and_admin_lockout():
    from web.backend import app as appmod
    limiters = [*appmod.LIMITS.values(), appmod.ADMIN_FAILURES]
    for lim in limiters:  # earlier tests share this client's IP
        lim.events.clear()
    try:
        for _ in range(60):
            client.get("/api/breakdown", params={"year": 2024})
        r = client.get("/api/breakdown", params={"year": 2024})
        assert r.status_code == 429 and r.headers["retry-after"] == "60"
        assert client.get("/api/health").status_code == 200  # health checks are never limited

        for _ in range(10):
            assert client.get("/api/admin/stats", auth=("admin", "mal")).status_code == 401
        assert client.get("/api/admin/stats", auth=ADMIN).status_code == 429  # locked out, even with the right one
    finally:
        for lim in limiters:
            lim.events.clear()


def test_cloudflare_origin_lock_ip_and_country(monkeypatch):
    monkeypatch.setenv("CF_ORIGIN_SECRET", "s3")
    via_cf = {"x-origin-secret": "s3", "cf-connecting-ip": "203.0.113.7", "cf-ipcountry": "uy",
              "user-agent": "Mozilla/5.0 Firefox/130.0"}
    # Direct requests (adondeva.fly.dev, or a forged Cloudflare header) are refused; the health check is not.
    assert client.get("/api/sources").status_code == 403
    assert client.get("/api/sources", headers={**via_cf, "x-origin-secret": "mal"}).status_code == 403
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/sources", headers=via_cf).status_code == 200

    client.post("/api/hit", json={"tipo": "pagina", "ruta": "/desde-cloudflare"}, headers=via_cf)
    uso.flush()
    rows = list(csv.DictReader(io.StringIO(client.get("/api/admin/export.csv", auth=ADMIN, headers=via_cf).text)))
    row = next(r for r in rows if r["ruta"] == "/desde-cloudflare")
    assert row["pais"] == "UY" and row["navegador"] == "Firefox"
    assert "203.0.113.7" not in str(rows)
    assert any(p["nombre"] == "UY" for p in client.get("/api/admin/stats", auth=ADMIN, headers=via_cf).json()["paises"])

    # Without the secret, Cloudflare's headers are ignored: they could be forged.
    monkeypatch.delenv("CF_ORIGIN_SECRET")
    assert uso.details(type("R", (), {"headers": via_cf, "client": None})())["pais"] == ""


def test_www_redirects_to_the_canonical_host(monkeypatch):
    monkeypatch.setenv("CANONICAL_HOST", "adondeva.org")
    r = client.get("/recaudacion?x=1", headers={"host": "www.adondeva.org"}, follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"] == "https://adondeva.org/recaudacion?x=1"


def test_admin_stats_survive_non_finite_amounts():
    client.get("/api/tax/sueldo", params={"monto": "1e309"})
    uso.flush()
    assert client.get("/api/admin/stats", auth=ADMIN).status_code == 200


LINK = {"tipo": "link", "titulo": "El gasto en seguridad creció", "medio": "La Diaria", "fecha": "2026-11-01",
        "url": "https://ladiaria.com.uy/nota", "resumen": "Resumen propio de la nota sobre seguridad.",
        "cita": "Una frase corta", "seccion": "gasto"}
PROPIA = {"tipo": "propia", "titulo": "Cuánto costó la visita", "fecha": "2026-11-05",
          "resumen": "Lo que sabemos del gasto público.", "cuerpo": "## Resumen\n\nTexto de la nota."}


def test_noticias_crud_and_drafts():
    r = client.post("/api/admin/noticias", json=LINK, auth=ADMIN)
    assert r.status_code == 201, r.text
    link = r.json()
    assert link["slug"] is None and link["cuerpo"] is None
    propia = client.post("/api/admin/noticias", json={**PROPIA, "publicada": False}, auth=ADMIN).json()
    assert propia["slug"] == "cuanto-costo-la-visita"

    publicas = get("/api/noticias")
    assert [n["id"] for n in publicas] == [link["id"]]  # drafts stay hidden
    assert "cuerpo" not in publicas[0]
    assert client.get("/api/noticias/cuanto-costo-la-visita").status_code == 404

    r = client.put(f"/api/admin/noticias/{propia['id']}", json={**PROPIA, "titulo": "Otro título"}, auth=ADMIN)
    assert r.json()["slug"] == "cuanto-costo-la-visita"  # the address survives a new title
    assert get("/api/noticias/cuanto-costo-la-visita")["cuerpo"].startswith("## Resumen")
    assert [n["id"] for n in get("/api/noticias")] == [propia["id"], link["id"]]  # newest first

    assert client.delete(f"/api/admin/noticias/{link['id']}", auth=ADMIN).status_code == 204
    assert client.delete(f"/api/admin/noticias/{link['id']}", auth=ADMIN).status_code == 404
    assert client.put("/api/admin/noticias/99999", json=LINK, auth=ADMIN).status_code == 404


def test_noticias_validation():
    for bad in [
        {**LINK, "url": "javascript:alert(1)"},
        {**LINK, "url": ""},
        {**LINK, "medio": " "},
        {**LINK, "seccion": "otra"},
        {**LINK, "resumen": "corto"},
        {**PROPIA, "cuerpo": ""},
        {**LINK, "tipo": "otro"},
    ]:
        assert client.post("/api/admin/noticias", json=bad, auth=ADMIN).status_code == 422, bad


def test_noticias_admin_needs_password_and_same_origin():
    assert client.post("/api/admin/noticias", json=LINK).status_code == 401
    assert client.get("/api/admin/noticias").status_code == 401
    evil = {"Origin": "https://evil.example"}
    assert client.post("/api/admin/noticias", json=LINK, auth=ADMIN, headers=evil).status_code == 403
    assert client.delete("/api/admin/noticias/1", auth=ADMIN, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    ok = {"Origin": "http://testserver", "Sec-Fetch-Site": "same-origin"}
    assert client.post("/api/admin/noticias", json=LINK, auth=ADMIN, headers=ok).status_code == 201


def test_donar_and_noticia_events_are_logged():
    n = client.post("/api/admin/noticias", json=LINK, auth=ADMIN).json()
    assert client.post("/api/hit", json={"tipo": "evento", "ruta": "donar", "datos": {}}).status_code == 204
    assert client.post("/api/hit", json={"tipo": "evento", "ruta": "noticia-abrir", "datos": {"id": n["id"]}}).status_code == 204
    assert client.post("/api/hit", json={"tipo": "evento", "ruta": "noticia-abrir", "datos": {"id": 99999}}).status_code == 422


CASO = {"titulo": "Visita del Papa", "fecha": "2026-11-06", "resumen": "Lo que gastó el Estado en la visita.",
        "items": [
            {"concepto": "Escenario", "organismo": "Intendencia", "monto": 1000, "moneda": "UYU", "estado": "confirmado",
             "fuente": "Compra 1/2026", "fuente_url": "https://www.comprasestatales.gub.uy/x"},
            {"concepto": "Vallas", "organismo": "Intendencia", "monto": 500, "moneda": "UYU", "estado": "confirmado",
             "fuente_url": "https://www.comprasestatales.gub.uy/y"},
            {"concepto": "Vuelos", "organismo": "Fuerza Aérea", "monto": 10, "moneda": "USD", "estado": "estimado",
             "fuente_url": "https://example.com/z"},
            {"concepto": "Policía", "organismo": "Ministerio del Interior", "monto": 999, "estado": "pedido"},
        ]}


def test_gastos_crud_and_totals():
    c = client.post("/api/admin/gastos-recientes", json=CASO, auth=ADMIN)
    assert c.status_code == 201, c.text
    c = c.json()
    assert c["slug"] == "visita-del-papa"
    assert c["totales"] == {"confirmado": {"UYU": 1500}, "estimado": {"USD": 10}, "pendientes": 1}
    assert c["items"][3]["monto"] is None  # no figure without a source
    assert "items" not in get("/api/gastos-recientes")[0]
    assert [i["concepto"] for i in get("/api/gastos-recientes/visita-del-papa")["items"]] == ["Escenario", "Vallas", "Vuelos", "Policía"]

    r = client.put(f"/api/admin/gastos-recientes/{c['id']}", json={**CASO, "titulo": "Otro", "items": CASO["items"][:1],
                                                          "publicado": False}, auth=ADMIN)
    assert r.json()["slug"] == "visita-del-papa" and len(r.json()["items"]) == 1
    assert client.get("/api/gastos-recientes/visita-del-papa").status_code == 404  # draft
    assert client.delete(f"/api/admin/gastos-recientes/{c['id']}", auth=ADMIN).status_code == 204
    assert client.get("/api/admin/gastos-recientes", auth=ADMIN).json() == []


def test_gastos_validation_and_auth():
    item = CASO["items"][0]
    for bad in [
        {**CASO, "items": [{**item, "monto": None}]},
        {**CASO, "items": [{**item, "fuente_url": None}]},
        {**CASO, "items": [{**item, "fuente_url": "javascript:x"}]},
        {**CASO, "items": [{**item, "monto": -1}]},
        {**CASO, "items": [{**item, "moneda": "EUR"}]},
        {**CASO, "items": [{**item, "estado": "inventado"}]},
    ]:
        assert client.post("/api/admin/gastos-recientes", json=bad, auth=ADMIN).status_code == 422, bad
    assert client.post("/api/admin/gastos-recientes", json=CASO).status_code == 401
    assert client.post("/api/admin/gastos-recientes", json=CASO, auth=ADMIN, headers={"Origin": "https://evil.example"}).status_code == 403
