# adondeva web

The same data as `adondeva.py`, as a website in Spanish: spending by year and drill-down, tax calculator, inflation and data sources.

- `backend/`: FastAPI. It imports `adondeva.py` and serves the API under `/api` (docs at `/api/docs`) and the built frontend.
- `frontend/`: React + TypeScript (Vite), charts with Recharts.

## Run it

From the repo root, once:

```bash
python3 -m venv .venv
.venv/bin/pip install -r web/backend/requirements.txt
(cd web/frontend && npm install)
```

Development, in two terminals (the Vite server sends `/api` to uvicorn):

```bash
.venv/bin/uvicorn web.backend.app:app --reload     # API on :8000
(cd web/frontend && npm run dev)                    # site on :5173
```

Production-like, one process:

```bash
(cd web/frontend && npm run build)
.venv/bin/uvicorn web.backend.app:app               # site and API on :8000
```

The server reads the large budget files in the background at startup (about 15 seconds the first time; then `.cache/` makes it fast).

## Tests

```bash
.venv/bin/pytest web/backend
```

## API

| Endpoint | Returns |
|---|---|
| `GET /api/sources` | datasets with coverage and caveats, and the tax catalog |
| `GET /api/inflation` | yearly inflation, average and December to December |
| `GET /api/spending?base=2025&fondos_terceros=false` | spending per year, nominal and in pesos of `base` |
| `GET /api/breakdown?year=2024&path=…&path=…` | one level of the drill-down; each `path` selects a value of the previous level |
| `GET /api/tax/{sueldo,compra,importar,alquiler}?monto=…` | tax breakdown; same options as `adondeva.py tax` |
| `GET /api/ncm?q=…` | tariff lines by code prefix or description |
