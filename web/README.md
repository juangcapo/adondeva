# adondeva web

The same data as `adondeva.py`, as a website in Spanish: spending by year and drill-down, tax revenue by tax since 1982, tax calculator and data sources.

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

## Deploy (Fly.io)

The `Dockerfile` at the repo root builds the frontend, installs the backend and reads the large files once,
so the server starts in seconds. `fly.toml` runs one always-on machine in São Paulo (`gru`) with 512 MB.
`.github/workflows/deploy.yml` deploys on every push to `main`, so merged data updates go live on their own.

Once, to set it up:

```bash
fly auth login
fly apps create adondeva                  # or another name; then change `app` in fly.toml
fly tokens create deploy -a adondeva      # copy the token
gh secret set FLY_API_TOKEN               # paste it
```

Also once, for the usage log (below):

```bash
fly volumes create uso -r gru -s 1 -a adondeva
fly secrets set -a adondeva ADMIN_PASSWORD="$(openssl rand -base64 24)"   # keep it in your password manager
```

By hand: `fly deploy` from the repo root.

## Usage log

`backend/uso.py` records every page view, API query (with its parameters) and tracked interaction (taxes
picked in Recaudación, view toggles) in SQLite: `USO_DB`, `.cache/uso.db` by default, `/data/uso.db` on Fly.
No IP addresses or cookies: a visitor is an HMAC of IP and user agent with a random key that changes every
day, and the old key is deleted, so people count once per day and can't be traced back or followed across days.
Referrers keep only site and path. Bots are flagged by user agent and left out of the reports. `/api/hit` only
accepts the pages and interactions the site sends.

## Security

- Rate limits per IP and minute: 300 API requests, 60 breakdowns, 120 hits (429 beyond). Admin: 10 wrong
  passwords per IP lock it for 15 minutes.
- Headers on every response: a strict Content-Security-Policy (nothing from other sites), `nosniff`,
  `X-Frame-Options: DENY`, HSTS; admin responses are `no-store` and `noindex`.
- The CSV export prefixes values that start with `= + - @` so spreadsheets don't run them as formulas.

`/admin` shows the reports and downloads the raw rows as CSV. It asks for user `admin` and `ADMIN_PASSWORD`;
without that variable it is off. To try it locally: `ADMIN_PASSWORD=x .venv/bin/uvicorn web.backend.app:app`.
In development React runs effects twice, so page views and requests are logged twice; production logs each once.

## Tests

```bash
.venv/bin/pytest web/backend
```

## API

| Endpoint | Returns |
|---|---|
| `GET /api/sources` | datasets with coverage and caveats, and the tax catalog |
| `GET /api/spending?base=2025&fondos_terceros=false` | spending per year, nominal and in pesos of `base` |
| `GET /api/revenue?base=2025` | DGI revenue per year and tax, tax groups, and a factor per year to pesos of `base` |
| `GET /api/breakdown?year=2024&path=…&path=…` | one level of the drill-down; each `path` selects a value of the previous level |
| `GET /api/tax/{sueldo,compra,importar,alquiler}?monto=…` | tax breakdown; same options as `adondeva.py tax` |
| `GET /api/ncm?q=…` | tariff lines by code prefix or description |
| `POST /api/hit` | log a page view or interaction (`{"tipo": "pagina" \| "evento", "ruta": …, "datos": …}`) |
| `GET /api/health` | `{"ok": true}`, for the health check; not logged |
| `GET /api/admin/stats?dias=30`, `/api/admin/export.csv` | usage reports (password) |
