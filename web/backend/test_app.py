"""Run from the repo root: .venv/bin/pytest web/backend"""
import pytest
from fastapi.testclient import TestClient

from web.backend.app import app

client = TestClient(app)


def get(url, **params):
    r = client.get(url, params=params)
    assert r.status_code == 200, r.text
    return r.json()


def test_sources_cover_every_dataset():
    data = get("/api/sources")
    assert {d["id"] for d in data["datasets"] if d["cobertura"]} >= {"opp-historico", "opp", "mef", "ine-ipc"}
    assert any(t["sigla"] == "IVA" for t in data["impuestos"])


def test_spending_real_equals_nominal_in_base_year():
    data = get("/api/spending", base=2020)
    row = next(r for r in data["anios"] if r["anio"] == 2020)
    assert row["real"] == pytest.approx(row["nominal"])


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
