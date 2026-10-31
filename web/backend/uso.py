"""Usage log: every page view, API query and tracked interaction, one row each, in SQLite.

No IP addresses or cookies are stored. A visitor is an HMAC of the IP and user agent with a random key that
changes every day; yesterday's key is deleted, so nobody (not even with the database and the server) can
recompute which IP a visitor was, nor follow a person from one day to the next. Referrers keep only the site
and path, never the query string.

Settings (environment):
  USO_DB   SQLite file (default .cache/uso.db; on Fly, /data/uso.db on a volume)
"""
import csv
import hashlib
import hmac
import io
import json
import os
import queue
import re
import secrets
import sqlite3
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB = Path(os.environ.get("USO_DB", Path(__file__).resolve().parents[2] / ".cache" / "uso.db"))

COLUMNS = ["ts", "tipo", "ruta", "params", "estado", "ms", "visitante", "referrer", "navegador", "dispositivo",
           "idioma", "region", "bot"]
SCHEMA = """
CREATE TABLE IF NOT EXISTS usos (
  id INTEGER PRIMARY KEY,
  ts TEXT NOT NULL,          -- UTC, ISO 8601
  tipo TEXT NOT NULL,        -- pagina | api | evento
  ruta TEXT NOT NULL,        -- page path, API path or event name
  params TEXT,               -- JSON: query parameters or event data
  estado INTEGER,            -- HTTP status (api)
  ms REAL,                   -- response time (api)
  visitante TEXT,
  referrer TEXT,
  navegador TEXT,
  dispositivo TEXT,
  idioma TEXT,
  region TEXT,               -- Fly edge region that took the request, a rough location
  bot INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS usos_ts ON usos (ts);
-- Today's key for the visitor hash; older ones are deleted.
CREATE TABLE IF NOT EXISTS clave (dia TEXT PRIMARY KEY, clave BLOB NOT NULL);
"""

_queue = queue.Queue()
_started = threading.Lock()
_writer = None


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    return con


def _write_forever():
    con = connect()
    while True:
        rows = [_queue.get()]
        while not _queue.empty() and len(rows) < 500:
            rows.append(_queue.get_nowait())
        try:
            with con:
                con.executemany(f"INSERT INTO usos ({', '.join(COLUMNS)}) VALUES ({', '.join('?' * len(COLUMNS))})",
                                [[r.get(c) for c in COLUMNS] for r in rows])
        except sqlite3.Error as e:
            print(f"uso: could not write {len(rows)} rows: {e}", flush=True)
        for _ in rows:
            _queue.task_done()


def record(**row):
    """Queue one row; a background thread writes it so requests never wait on the disk."""
    global _writer
    if _writer is None:
        with _started:
            if _writer is None:
                _writer = threading.Thread(target=_write_forever, daemon=True, name="uso-writer")
                _writer.start()
    row.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    _queue.put(row)


def flush():
    """Wait until every queued row is written (tests)."""
    _queue.join()


# ---------------------------------------------------------------- request details

BOT = re.compile(r"bot|crawl|spider|slurp|preview|monitor|curl|wget|python|httpx|go-http|headless|lighthouse", re.I)


def browser(ua):
    for name, pattern in [("Edge", "Edg/"), ("Opera", "OPR/"), ("Samsung", "SamsungBrowser"), ("Chrome", "Chrome/"),
                          ("Firefox", "Firefox/"), ("Safari", "Safari/")]:
        if pattern in ua:
            return name
    return "otro"


def device(ua):
    if re.search(r"iPad|Tablet", ua):
        return "tablet"
    return "móvil" if re.search(r"Mobi|Android", ua) else "escritorio"


_key = {"dia": None, "clave": b""}
_key_lock = threading.Lock()


def daily_key():
    """Today's random key, shared through the database so restarts keep counting visitors the same way."""
    day = datetime.now(timezone.utc).date().isoformat()
    with _key_lock:
        if _key["dia"] != day:
            con = connect()
            with con:
                con.execute("INSERT OR IGNORE INTO clave VALUES (?, ?)", (day, secrets.token_bytes(32)))
                con.execute("DELETE FROM clave WHERE dia != ?", (day,))
                _key.update(dia=day, clave=con.execute("SELECT clave FROM clave WHERE dia = ?", (day,)).fetchone()[0])
            con.close()
        return _key["clave"]


# Fly's proxy sets Fly-Client-IP; anywhere else a client could forge it, so it is trusted only on Fly.
ON_FLY = bool(os.environ.get("FLY_APP_NAME"))


def client_ip(request):
    if ON_FLY and request.headers.get("fly-client-ip"):
        return request.headers["fly-client-ip"]
    return request.client.host if request.client else ""


def details(request):
    """Visitor, browser, device, language, region and bot flag for a request; never the IP."""
    h = request.headers
    ua = h.get("user-agent", "")
    visitor = hmac.new(daily_key(), f"{client_ip(request)}|{ua}".encode(), hashlib.sha256).hexdigest()[:16]
    lang = h.get("accept-language", "").split(",")[0].split(";")[0].strip()[:20]
    return {"visitante": visitor, "navegador": browser(ua), "dispositivo": device(ua), "idioma": lang,
            "region": h.get("fly-region", "")[:10], "bot": int(not ua or bool(BOT.search(ua)))}


def clip(s, n=300):
    return None if s is None else str(s)[:n]


def referrer(url):
    """Only the site and path of a referrer: query strings can carry emails, tokens or tracking ids."""
    if not url:
        return None
    m = re.match(r"(https?://[^/?#\s]+)(/[^?#\s]*)?", url)
    return m.group(1) + (m.group(2) or "") if m else None


class Limiter:
    """At most `limit` events per `window` seconds per key, in memory (one machine)."""

    def __init__(self, limit, window):
        self.limit, self.window = limit, window
        self.events = defaultdict(deque)
        self.lock = threading.Lock()

    def _recent(self, key, now):
        q = self.events[key]
        while q and q[0] <= now - self.window:
            q.popleft()
        return q

    def blocked(self, key):
        with self.lock:
            return len(self._recent(key, time.monotonic())) >= self.limit

    def add(self, key):
        with self.lock:
            now = time.monotonic()
            self._recent(key, now).append(now)
            if len(self.events) > 50_000:  # forget idle keys so memory stays bounded
                for k in [k for k, q in self.events.items() if not q or q[-1] <= now - self.window]:
                    del self.events[k]

    def allow(self, key):
        """Count one event; False when the key is over the limit."""
        with self.lock:
            now = time.monotonic()
            q = self._recent(key, now)
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


def safe_cell(v):
    """Keep spreadsheets from running a logged value as a formula (CSV injection)."""
    return "'" + v if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r") else v


def params_json(query_params):
    """Query parameters as JSON; repeated keys (breakdown's path) become lists."""
    out = {}
    for k, v in query_params.multi_items():
        out.setdefault(k[:40], []).append(v[:200])
    return json.dumps({k: v[0] if len(v) == 1 else v for k, v in out.items()}, ensure_ascii=False) if out else None


# ---------------------------------------------------------------- reports

def since(days):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")


def stats(days):
    """Everything the admin page shows, for the last `days` days, bots left out."""
    con = connect()
    con.row_factory = sqlite3.Row
    t0 = since(days)

    def q(sql, *args):
        return [dict(r) for r in con.execute(sql, (t0, *args))]

    base = "FROM usos WHERE ts >= ? AND bot = 0"
    top = lambda col, tipo, n=15, extra="": q(
        f"SELECT {col} AS nombre, COUNT(*) AS n, COUNT(DISTINCT visitante) AS visitantes {base} AND tipo = ? {extra} "
        f"GROUP BY nombre ORDER BY n DESC LIMIT {n}", tipo)
    totals = q(f"SELECT COUNT(DISTINCT visitante) AS visitantes, SUM(tipo = 'pagina') AS paginas, "
               f"SUM(tipo = 'api') AS consultas, SUM(tipo = 'evento') AS eventos {base}")[0]
    out = {
        "dias": days,
        "totales": {k: v or 0 for k, v in totals.items()},
        "por_dia": q(f"SELECT substr(ts, 1, 10) AS dia, COUNT(DISTINCT visitante) AS visitantes, "
                     f"SUM(tipo = 'pagina') AS paginas, SUM(tipo = 'api') AS consultas {base} GROUP BY dia ORDER BY dia"),
        "paginas": top("ruta", "pagina"),
        "referrers": top("referrer", "pagina", extra="AND referrer IS NOT NULL AND referrer != ''"),
        "navegadores": top("navegador", "pagina"),
        "dispositivos": top("dispositivo", "pagina"),
        "idiomas": top("idioma", "pagina"),
        "regiones": top("region", "pagina"),
        "api": top("ruta", "api"),
        "eventos": top("ruta || ' ' || coalesce(params, '')", "evento", 20, "AND ruta != 'recaudacion-impuesto'"),
        "desglose": top("coalesce(json_extract(params, '$.year'), 'último') || ' · ' || "
                        "coalesce(json_extract(params, '$.path'), 'todo el gasto')", "api", 20, "AND ruta = '/api/breakdown'"),
        "calculadora": q(f"SELECT substr(ruta, 10) AS nombre, COUNT(*) AS n, COUNT(DISTINCT visitante) AS visitantes, "
                         f"MIN(CAST(json_extract(params, '$.monto') AS REAL)) AS monto_min, "
                         f"MAX(CAST(json_extract(params, '$.monto') AS REAL)) AS monto_max "
                         f"{base} AND tipo = 'api' AND ruta LIKE '/api/tax/%' GROUP BY nombre ORDER BY n DESC"),
        # Taxes picked in Recaudación's "Cada impuesto": how many people chose each, the clearest sign of interest.
        "impuestos": q(f"SELECT json_extract(params, '$.sigla') AS sigla, "
                       f"COUNT(DISTINCT CASE WHEN json_extract(params, '$.accion') = 'agregar' THEN visitante END) AS visitantes, "
                       f"SUM(json_extract(params, '$.accion') = 'agregar') AS agregado, "
                       f"SUM(json_extract(params, '$.accion') = 'quitar') AS quitado "
                       f"{base} AND tipo = 'evento' AND ruta = 'recaudacion-impuesto' "
                       f"GROUP BY sigla ORDER BY visitantes DESC, agregado DESC"),
        "ncm": top("json_extract(params, '$.q')", "api", 20, "AND ruta = '/api/ncm'"),
        "errores": q(f"SELECT ruta AS nombre, estado, COUNT(*) AS n {base} AND tipo = 'api' AND estado >= 400 "
                     f"GROUP BY ruta, estado ORDER BY n DESC LIMIT 15"),
        "bots": q("SELECT COUNT(*) AS n FROM usos WHERE ts >= ? AND bot = 1")[0]["n"],
    }
    con.close()
    return out


def export_csv(days=None):
    """Every row (bots included) as CSV, oldest first."""
    con = connect()
    rows = con.execute(f"SELECT {', '.join(COLUMNS)} FROM usos WHERE ts >= ? ORDER BY id",
                       (since(days) if days else "",))
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(COLUMNS)
    w.writerows([safe_cell(v) for v in r] for r in rows)
    con.close()
    return buf.getvalue()
