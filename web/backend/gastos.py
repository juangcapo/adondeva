"""Recent spending: cases (e.g. the Pope's visit) broken down into items, each with its source, in SQLite.

Every amount must trace back to a document (a purchase on comprasestatales, a resolution, an answer to an
access-to-information request). Items without a confirmed figure stay on the list with their status
("sin datos", "pedido en trámite") instead of an estimate of ours, so the page shows what is known and what is not.
Totals only add confirmed amounts, per currency: pesos and dollars are never converted into each other.

Stored in the same SQLite file as the news board (CONTENIDO_DB, see noticias.py).
"""
from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from . import noticias

ESTADOS = ("confirmado", "estimado", "sin_datos", "pedido")
SCHEMA = """
CREATE TABLE IF NOT EXISTS gastos_casos (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,        -- /gastos/<slug>
  titulo TEXT NOT NULL,
  fecha TEXT NOT NULL,              -- when it happened, YYYY-MM-DD
  resumen TEXT NOT NULL,
  notas TEXT,                       -- methodology, caveats
  publicado INTEGER NOT NULL DEFAULT 1,
  creado TEXT NOT NULL,
  actualizado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gastos_items (
  id INTEGER PRIMARY KEY,
  caso INTEGER NOT NULL REFERENCES gastos_casos (id) ON DELETE CASCADE,
  orden INTEGER NOT NULL,
  concepto TEXT NOT NULL,
  organismo TEXT NOT NULL,          -- the unidad ejecutora that bought it
  inciso TEXT,                      -- the organismo contratante, as ARCE lists it: "Ministerio de Salud Pública"
  tipo_contratacion TEXT,           -- as ARCE names it: "Compra Directa", "Licitación Pública"...
  monto REAL,                       -- NULL when unknown
  moneda TEXT NOT NULL,             -- UYU | USD
  estado TEXT NOT NULL,             -- confirmado | estimado (by the source, never ours) | sin_datos | pedido
  fuente TEXT,                      -- what the source is: "Compra directa 123/2026", "Resolución ..."
  fuente_url TEXT,
  nota TEXT
);
CREATE INDEX IF NOT EXISTS gastos_items_caso ON gastos_items (caso, orden);
"""
CASO_FIELDS = ["slug", "titulo", "fecha", "resumen", "notas", "publicado"]
ITEM_FIELDS = ["concepto", "organismo", "inciso", "tipo_contratacion", "monto", "moneda", "estado", "fuente", "fuente_url",
               "nota"]
# What the list page filters by, the way ARCE's search does: organismo contratante, unidad ejecutora, tipo de contratación.
FILTER_FIELDS = ["inciso", "organismo", "tipo_contratacion"]


def connect():
    con = noticias.connect()
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    have = {r["name"] for r in con.execute("PRAGMA table_info(gastos_items)")}
    for col in ("inciso", "tipo_contratacion"):  # added after the first deploy
        if col not in have:
            con.execute(f"ALTER TABLE gastos_items ADD COLUMN {col} TEXT")
    return con


class Item(BaseModel):
    concepto: str = Field(min_length=2, max_length=200)
    organismo: str = Field(min_length=2, max_length=150)
    inciso: str | None = Field(None, max_length=150)
    tipo_contratacion: str | None = Field(None, max_length=100)
    monto: float | None = Field(None, ge=0, allow_inf_nan=False)
    moneda: Literal["UYU", "USD"] = "UYU"
    estado: Literal[ESTADOS]  # type: ignore[valid-type]
    fuente: str | None = Field(None, max_length=200)
    fuente_url: str | None = Field(None, max_length=1000)
    nota: str | None = Field(None, max_length=600)

    _blank = field_validator("inciso", "tipo_contratacion", "fuente", "fuente_url", "nota", mode="before")(noticias.blank_to_none)
    _url = field_validator("fuente_url")(noticias.http_url)

    @model_validator(mode="after")
    def by_status(self):
        if self.estado in ("confirmado", "estimado"):
            if self.monto is None:
                raise ValueError(f"«{self.concepto}»: un monto {self.estado} necesita el monto.")
            if not self.fuente_url:
                raise ValueError(f"«{self.concepto}»: un monto {self.estado} necesita el link a su fuente.")
        else:
            self.monto = None  # no figure until a source gives one
        return self


class Caso(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    fecha: date
    resumen: str = Field(min_length=10, max_length=1000)
    notas: str | None = Field(None, max_length=5000)
    publicado: bool = True
    items: list[Item] = Field(default_factory=list, max_length=200)

    _blank = field_validator("notas", mode="before")(noticias.blank_to_none)


def totales(items):
    """Confirmed and source-estimated amounts, per currency; how many items still lack a figure."""
    out = {"confirmado": {}, "estimado": {}, "pendientes": 0}
    for i in items:
        if i["estado"] in ("confirmado", "estimado"):
            out[i["estado"]][i["moneda"]] = out[i["estado"]].get(i["moneda"], 0) + i["monto"]
        else:
            out["pendientes"] += 1
    return out


def _caso(con, row, con_items=True):
    d = dict(row)
    d["publicado"] = bool(d["publicado"])
    items = [dict(r) for r in con.execute(f"SELECT id, {', '.join(ITEM_FIELDS)} FROM gastos_items "
                                          "WHERE caso = ? ORDER BY orden", (d["id"],))]
    d["totales"] = totales(items)
    if con_items:
        d["items"] = items
    else:  # the list page doesn't need the items, only what to filter them by
        d["filtros"] = [dict(t) for t in dict.fromkeys(tuple((f, i[f]) for f in FILTER_FIELDS) for i in items)]
    return d


def listar(todos=False):
    with connect() as con:
        rows = con.execute(f"SELECT * FROM gastos_casos {'' if todos else 'WHERE publicado = 1'} "
                           "ORDER BY fecha DESC, id DESC").fetchall()
        return [_caso(con, r, con_items=todos) for r in rows]


def por_slug(slug):
    with connect() as con:
        row = con.execute("SELECT * FROM gastos_casos WHERE slug = ? AND publicado = 1", (slug,)).fetchone()
        return _caso(con, row) if row else None


def guardar(c: Caso, id=None):
    """Insert (id None) or update a case, replacing its items; None if `id` does not exist."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connect() as con:
        old = con.execute("SELECT slug FROM gastos_casos WHERE id = ?", (id,)).fetchone() if id is not None else None
        if id is not None and not old:
            return None
        values = {"slug": old["slug"] if old else unique_slug(con, c.titulo), "titulo": c.titulo,
                  "fecha": c.fecha.isoformat(), "resumen": c.resumen, "notas": c.notas, "publicado": c.publicado}
        if id is None:
            id = con.execute(f"INSERT INTO gastos_casos ({', '.join(CASO_FIELDS)}, creado, actualizado) "
                             f"VALUES ({', '.join('?' * len(CASO_FIELDS))}, ?, ?)",
                             [values[f] for f in CASO_FIELDS] + [now, now]).lastrowid
        else:
            con.execute(f"UPDATE gastos_casos SET {', '.join(f'{f} = ?' for f in CASO_FIELDS)}, actualizado = ? "
                        "WHERE id = ?", [values[f] for f in CASO_FIELDS] + [now, id])
            con.execute("DELETE FROM gastos_items WHERE caso = ?", (id,))
        con.executemany(f"INSERT INTO gastos_items (caso, orden, {', '.join(ITEM_FIELDS)}) "
                        f"VALUES (?, ?, {', '.join('?' * len(ITEM_FIELDS))})",
                        [[id, n] + [i.model_dump()[f] for f in ITEM_FIELDS] for n, i in enumerate(c.items)])
        return _caso(con, con.execute("SELECT * FROM gastos_casos WHERE id = ?", (id,)).fetchone())


def unique_slug(con, titulo):
    base = noticias.slugify(titulo)
    slug, n = base, 1
    while con.execute("SELECT 1 FROM gastos_casos WHERE slug = ?", (slug,)).fetchone():
        n += 1
        slug = f"{base}-{n}"
    return slug


def borrar(id):
    with connect() as con:
        return con.execute("DELETE FROM gastos_casos WHERE id = ?", (id,)).rowcount > 0

