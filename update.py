#!/usr/bin/env python3
"""Check the official sources for new data, download what changed and rebuild the derived CSVs.

Usage:
  python3 update.py                    check every source
  python3 update.py dgi ine            only these sources
  python3 update.py --dry-run          report what changed without writing anything
  python3 update.py --summary FILE     also write a Markdown summary (the body of the update pull request)

Sources: dgi (tax revenue), ine (CPI), mef (Rendición de Cuentas: the years we have, and the next one
once MEF publishes it, usually by 30 June). OPP retired its open-data portal, so 2011–2024 are final.

Each file is found by its link on the source's page, because gub.uy file URLs change with each upload.
A file counts as changed when its bytes differ from the local copy. Standard library only.
Exit status 1 if a source could not be checked or a rebuild failed.
"""
import argparse
import hashlib
import html
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UY = ROOT / "data" / "uy"
USER_AGENT = "adondeva-updater (+https://github.com/juangcapo/adondeva)"

# Hosts that don't send their intermediate certificate, and where to get it (the AIA URL in
# the server certificate). Verification stays on; this only completes the chain.
INTERMEDIATES = {
    "www5.ine.gub.uy": "http://crt.sectigo.com/SectigoPublicServerAuthenticationCADVR36.crt",
}


# ---------------------------------------------------------------- fetching

def fetch(url):
    """(bytes, headers) for url; retries once with the host's intermediate certificate if verification fails."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read(), r.headers
    except urllib.error.URLError as e:
        host = urllib.parse.urlsplit(url).hostname
        if not isinstance(e.reason, ssl.SSLCertVerificationError) or host not in INTERMEDIATES:
            raise
        with urllib.request.urlopen(INTERMEDIATES[host], timeout=60) as r:
            ctx = ssl.create_default_context()
            ctx.load_verify_locations(cadata=r.read())
        with urllib.request.urlopen(req, timeout=120, context=ctx) as r:
            return r.read(), r.headers


def page_links(url):
    """[(label, absolute url)] for every link on a page; label is the aria-label or, failing that, the file name."""
    body, _ = fetch(url)
    out = []
    for tag in re.findall(r"<a\s[^>]*>", body.decode("utf-8", "replace")):
        href = re.search(r"""href=(["'])(.*?)\1""", tag)
        if not href:
            continue
        # Some pages put raw accented characters in hrefs; percent-encode them, leaving existing escapes alone.
        link = urllib.parse.quote(urllib.parse.urljoin(url, html.unescape(href.group(2))), safe=":/?#[]@!$&'()*+,;=%~")
        label = re.search(r'aria-label="([^"]*)"', tag)
        out.append((html.unescape(label.group(1)) if label else file_name(link), link))
    return out


def file_name(url):
    return urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit("/", 1)[-1])


def page_exists(url):
    try:
        fetch(url)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise


# ---------------------------------------------------------------- sources
# Each source returns {local path: url} for the files it wants, plus how to rebuild and describe it.

DGI_DIR = UY / "dgi" / "recaudacion"
DGI_PAGE = "https://www.gub.uy/direccion-general-impositiva/datos-y-estadisticas/estadisticas/recaudacion-anual-mensual-impuesto"
DGI_TITLE = "Recaudación por impuesto - Series anuales"


def dgi_files():
    files = {}
    for label, url in page_links(DGI_PAGE):
        m = re.match(rf"Descargar: {re.escape(DGI_TITLE)} \(\.(csv|xlsx)\b", label)
        if m:
            files[DGI_DIR / "raw" / f"{DGI_TITLE}.{m.group(1)}"] = url
    return files


def dgi_coverage():
    rows = (DGI_DIR / "recaudacion_anual.csv").read_text(encoding="utf-8").splitlines()[1:]
    years = sorted({int(r.split(",", 1)[0]) for r in rows})
    return f"{years[0]}–{years[-1]}"


INE_DIR = UY / "inflation" / "ine-ipc"
INE_PAGE = "https://www.gub.uy/instituto-nacional-estadistica/datos-y-estadisticas/estadisticas/series-historicas-ipc-base-octubre-2022100"
INE_FILES = ["IPC gral y variaciones_base 2022.xlsx", "IPC General_Total Pais_Montevideo_Interior_base 2022.xlsx"]


def ine_files():
    return {INE_DIR / "raw" / name: url for name, url in page_links(INE_PAGE) if name in INE_FILES}


def ine_coverage():
    last = (INE_DIR / "ipc_mensual.csv").read_text(encoding="utf-8").splitlines()[-1].split(",")
    return f"monthly to {last[0]}-{int(last[1]):02}"


MEF_DIR = UY / "mef" / "rendicion-cuentas"
MEF_PAGE = ("https://www.gub.uy/ministerio-economia-finanzas/comunicacion/publicaciones/"
            "rendicion-cuentas-balance-ejecucion-presupuestal-ejercicio-{year}-datos")


def mef_files():
    have = sorted(int(p.name) for p in MEF_DIR.iterdir() if p.name.isdigit())
    files = {}
    for year in [*have, have[-1] + 1]:
        page = MEF_PAGE.format(year=year)
        if year not in have and not page_exists(page):
            continue
        for label, url in page_links(page):
            if label.startswith("Descargar:"):
                files[MEF_DIR / str(year) / file_name(url)] = url
    return files


def mef_coverage():
    return ", ".join(sorted(p.name for p in MEF_DIR.iterdir() if (p / "bal_gastos.ods").exists()))


SOURCES = {
    "dgi": {"name": "DGI, recaudación por impuesto", "page": DGI_PAGE, "files": dgi_files,
            "build": DGI_DIR / "build_recaudacion.py", "coverage": dgi_coverage},
    "ine": {"name": "INE, IPC", "page": INE_PAGE, "files": ine_files,
            "build": INE_DIR / "build_ipc.py", "coverage": ine_coverage},
    "mef": {"name": "MEF, Rendición de Cuentas", "page": MEF_PAGE.format(year="AAAA"), "files": mef_files,
            "build": None, "coverage": mef_coverage},
}


# ---------------------------------------------------------------- update

def sha256(data):
    return hashlib.sha256(data).hexdigest()


def update(key, dry_run):
    """Markdown lines describing what changed in one source; raises if it could not be checked."""
    src = SOURCES[key]
    before = src["coverage"]()
    wanted = src["files"]()
    if not wanted:
        raise RuntimeError(f"no files found on {src['page']} (did the page change?)")
    changed = []
    for path, url in sorted(wanted.items()):
        data, headers = fetch(url)
        old = path.read_bytes() if path.exists() else None
        if old is not None and sha256(old) == sha256(data):
            continue
        stamp = headers.get("Last-Modified", "no Last-Modified")
        changed.append(f"- `{path.relative_to(ROOT)}`: {'new' if old is None else 'changed'} ({stamp}) from <{url}>")
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if not changed:
        return []
    if src["build"] and not dry_run:
        subprocess.run([sys.executable, src["build"].name], cwd=src["build"].parent, check=True, stdout=sys.stderr)
    after = src["coverage"]()
    head = f"### {src['name']}\n\nCoverage: {before}" + (f" → **{after}**" if after != before else " (unchanged)")
    return [head, "", *changed, ""]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("sources", nargs="*", metavar="SOURCE", help=f"any of: {', '.join(SOURCES)} (default: all)")
    ap.add_argument("--dry-run", action="store_true", help="report changes without writing files")
    ap.add_argument("--summary", type=Path, metavar="FILE", help="write a Markdown summary here")
    args = ap.parse_args()
    unknown = set(args.sources) - set(SOURCES)
    if unknown:
        ap.error(f"unknown source(s): {', '.join(sorted(unknown))}")

    lines, failed = [], []
    for key in args.sources or SOURCES:
        print(f"checking {key}…", file=sys.stderr)
        try:
            lines += update(key, args.dry_run)
        except Exception as e:  # report every source, then fail at the end
            failed.append(key)
            lines += [f"### {SOURCES[key]['name']}", "", f"**Could not update:** {type(e).__name__}: {e}", ""]

    text = "\n".join(lines) if lines else "No changes in any source."
    print(text)
    if args.summary:
        args.summary.write_text(text + "\n", encoding="utf-8")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
