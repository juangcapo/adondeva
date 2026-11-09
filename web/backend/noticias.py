"""News board: links to press articles about the site's data, and adondeva's own articles, in SQLite.

Press links carry our own summary and, at most, a short quote with its source; never the article's text or
its photos (copyright: Ley 9.739, art. 45). Own articles have a body written in a small subset of Markdown
that the frontend renders (paragraphs, ## headings, - lists, [text](https://...) links).

Settings (environment):
  CONTENIDO_DB   SQLite file shared with gastos.py (default .cache/contenido.db; on Fly, /data/contenido.db on the volume)
"""
import os
import re
import sqlite3
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

DB = Path(os.environ.get("CONTENIDO_DB", Path(__file__).resolve().parents[2] / ".cache" / "contenido.db"))

SECCIONES = ("gasto", "recaudacion", "impuestos")
FIELDS = ["tipo", "slug", "titulo", "medio", "autor", "fecha", "url", "resumen", "cita", "cuerpo", "seccion", "publicada"]
SCHEMA = """
CREATE TABLE IF NOT EXISTS noticias (
  id INTEGER PRIMARY KEY,
  tipo TEXT NOT NULL,          -- link (press article) | propia (adondeva's own)
  slug TEXT UNIQUE,            -- own articles: /noticias/<slug>
  titulo TEXT NOT NULL,
  medio TEXT,                  -- links: the outlet
  autor TEXT,
  fecha TEXT NOT NULL,         -- publication date, YYYY-MM-DD
  url TEXT,                    -- links: the article
  resumen TEXT NOT NULL,       -- our own words
  cita TEXT,                   -- links: a short quote, shown with its source
  cuerpo TEXT,                 -- own articles: the text
  seccion TEXT,                -- gasto | recaudacion | impuestos, or NULL
  publicada INTEGER NOT NULL DEFAULT 1,
  creada TEXT NOT NULL,
  actualizada TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS noticias_fecha ON noticias (fecha);
"""


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def blank_to_none(v):
    return v.strip() or None if isinstance(v, str) else v


def http_url(v):
    """Only web links: no javascript:, data: or other schemes a visitor's browser would run."""
    if v is not None and (not re.fullmatch(r"https?://[^\s/]+\.[^\s/]+(/\S*)?", v) or any(ord(c) < 32 for c in v)):
        raise ValueError("El link tiene que empezar con http:// o https://.")
    return v


class Noticia(BaseModel):
    tipo: Literal["link", "propia"]
    titulo: str = Field(min_length=3, max_length=200)
    medio: str | None = Field(None, max_length=100)
    autor: str | None = Field(None, max_length=100)
    fecha: date
    url: str | None = Field(None, max_length=1000)
    resumen: str = Field(min_length=10, max_length=600)
    cita: str | None = Field(None, max_length=400)
    cuerpo: str | None = Field(None, max_length=50_000)
    seccion: Literal[SECCIONES] | None = None  # type: ignore[valid-type]
    publicada: bool = True

    _blank = field_validator("medio", "autor", "url", "cita", "cuerpo", "seccion", mode="before")(blank_to_none)

    @field_validator("titulo", "resumen", mode="before")
    @classmethod
    def strip(cls, v):
        return v.strip() if isinstance(v, str) else v

    _url = field_validator("url")(http_url)

    @model_validator(mode="after")
    def by_type(self):
        if self.tipo == "link":
            if not self.url or not self.medio:
                raise ValueError("Un link a un medio necesita el link y el nombre del medio.")
            self.cuerpo = None
        else:
            if not self.cuerpo:
                raise ValueError("Una nota propia necesita el texto.")
            self.cita = None
        return self


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:80].strip("-") or "nota"


def unique_slug(con, titulo, own_id=None):
    base, n = slugify(titulo), 1
    slug = base
    while (row := con.execute("SELECT id FROM noticias WHERE slug = ?", (slug,)).fetchone()) and row["id"] != own_id:
        n += 1
        slug = f"{base}-{n}"
    return slug


def as_dict(row, cuerpo=True):
    d = dict(row)
    d["publicada"] = bool(d["publicada"])
    if not cuerpo:
        d.pop("cuerpo", None)
    return d


def listar(todas=False):
    """Newest first; the public list leaves out drafts and the bodies of own articles."""
    with connect() as con:
        rows = con.execute(f"SELECT * FROM noticias {'' if todas else 'WHERE publicada = 1'} "
                           "ORDER BY fecha DESC, id DESC").fetchall()
    return [as_dict(r, cuerpo=todas) for r in rows]


def por_slug(slug):
    with connect() as con:
        row = con.execute("SELECT * FROM noticias WHERE slug = ? AND tipo = 'propia' AND publicada = 1",
                          (slug,)).fetchone()
    return as_dict(row) if row else None


def guardar(n: Noticia, id=None):
    """Insert (id None) or update; returns the saved row, or None if `id` does not exist."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    values = n.model_dump()
    values["fecha"] = n.fecha.isoformat()
    with connect() as con:
        old = con.execute("SELECT slug FROM noticias WHERE id = ?", (id,)).fetchone() if id is not None else None
        if id is not None and not old:
            return None
        # An own article keeps its first address when its title changes, so shared links keep working.
        values["slug"] = (old and old["slug"] or unique_slug(con, n.titulo, id)) if n.tipo == "propia" else None
        if id is None:
            cur = con.execute(f"INSERT INTO noticias ({', '.join(FIELDS)}, creada, actualizada) "
                              f"VALUES ({', '.join('?' * len(FIELDS))}, ?, ?)", [values[f] for f in FIELDS] + [now, now])
            id = cur.lastrowid
        else:
            con.execute(f"UPDATE noticias SET {', '.join(f'{f} = ?' for f in FIELDS)}, actualizada = ? WHERE id = ?",
                        [values[f] for f in FIELDS] + [now, id])
        return as_dict(con.execute("SELECT * FROM noticias WHERE id = ?", (id,)).fetchone())


def borrar(id):
    with connect() as con:
        return con.execute("DELETE FROM noticias WHERE id = ?", (id,)).rowcount > 0
