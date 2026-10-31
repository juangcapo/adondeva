#!/usr/bin/env python3
"""Check the official sources for new data, download what changed and rebuild the derived CSVs.

Usage:
  python3 update.py                    check every source
  python3 update.py dgi ine            only these sources
  python3 update.py --dry-run          report what changed without writing anything
  python3 update.py --summary FILE     also write a Markdown summary (the body of the update pull request)

Sources: dgi (tax revenue), ine (CPI), mef (Rendición de Cuentas: the years we have, and the next one
once MEF publishes it, usually by 30 June). OPP retired its open-data portal, so 2011–2024 are final.

Only files we already keep are downloaded. A new file on a source page is listed as skipped and never
fetched: MEF publishes some files with personal data (Adscriptos.xlsx lists names and salaries), and
whatever the updater downloads ends up on a branch pushed to GitHub. Add a file by hand after checking it.

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

# Hosts that don't send their intermediate certificate: where to get it (the AIA URL in the
# server certificate) and its SHA-256. Verification stays on; this only completes the chain.
# The AIA URL is plain HTTP, so the certificate is used only if its hash matches: otherwise
# anyone on the network path could swap in their own CA. When Sectigo rotates it, check the new
# one chains to a trusted root (openssl verify) and update the hash.
INTERMEDIATES = {
    "www5.ine.gub.uy": ("http://crt.sectigo.com/SectigoPublicServerAuthenticationCADVR36.crt",
                        "8c54c334b66ba4e426772af4a3f9136c19a1aec729fdb28c535c07a5a4ef22e0"),
}


# ---------------------------------------------------------------- fetching

def https_only(url):
    if urllib.parse.urlsplit(url).scheme != "https":
        raise ValueError(f"refusing non-HTTPS URL {url}")


def read(req, **kwargs):
    """(bytes, headers), refusing a redirect away from HTTPS."""
    with urllib.request.urlopen(req, timeout=120, **kwargs) as r:
        https_only(r.geturl())
        return r.read(), r.headers


def intermediate_context(host):
    """An SSL context with the default roots plus the host's pinned intermediate certificate."""
    url, want = INTERMEDIATES[host]
    with urllib.request.urlopen(url, timeout=60) as r:
        der = r.read()
    if sha256(der) != want:
        raise ssl.SSLError(f"intermediate certificate for {host} from {url} has SHA-256 {sha256(der)}, "
                           f"expected {want}; check it and update INTERMEDIATES")
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cadata=der)
    return ctx


def fetch(url):
    """(bytes, headers) for an HTTPS url; retries once with the host's intermediate certificate if verification fails."""
    https_only(url)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        return read(req)
    except urllib.error.URLError as e:
        host = urllib.parse.urlsplit(url).hostname
        if not isinstance(e.reason, ssl.SSLCertVerificationError) or host not in INTERMEDIATES:
            raise
        return read(req, context=intermediate_context(host))


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
# Each source's `files` returns ({local path: url} to download, [names on the page it skips]),
# plus how to rebuild and describe it.

DGI_DIR = UY / "dgi" / "recaudacion"
DGI_PAGE = "https://www.gub.uy/direccion-general-impositiva/datos-y-estadisticas/estadisticas/recaudacion-anual-mensual-impuesto"
DGI_TITLE = "Recaudación por impuesto - Series anuales"


def dgi_files():
    files = {}
    for label, url in page_links(DGI_PAGE):
        m = re.match(rf"Descargar: {re.escape(DGI_TITLE)} \(\.(csv|xlsx)\b", label)
        if m:
            files[DGI_DIR / "raw" / f"{DGI_TITLE}.{m.group(1)}"] = url
    return files, []


def dgi_coverage():
    rows = (DGI_DIR / "recaudacion_anual.csv").read_text(encoding="utf-8").splitlines()[1:]
    years = sorted({int(r.split(",", 1)[0]) for r in rows})
    return f"{years[0]}–{years[-1]}"


INE_DIR = UY / "inflation" / "ine-ipc"
INE_PAGE = "https://www.gub.uy/instituto-nacional-estadistica/datos-y-estadisticas/estadisticas/series-historicas-ipc-base-octubre-2022100"
INE_FILES = ["IPC gral y variaciones_base 2022.xlsx", "IPC General_Total Pais_Montevideo_Interior_base 2022.xlsx"]


def ine_files():
    return {INE_DIR / "raw" / name: url for name, url in page_links(INE_PAGE) if name in INE_FILES}, []


def ine_coverage():
    last = (INE_DIR / "ipc_mensual.csv").read_text(encoding="utf-8").splitlines()[-1].split(",")
    return f"monthly to {last[0]}-{int(last[1]):02}"


MEF_DIR = UY / "mef" / "rendicion-cuentas"
MEF_PAGE = ("https://www.gub.uy/ministerio-economia-finanzas/comunicacion/publicaciones/"
            "rendicion-cuentas-balance-ejecucion-presupuestal-ejercicio-{year}-datos")


def mef_kind(name):
    """A file name with its year masked, so "Metadata RC2025.ods" matches next year's "Metadata RC2026.ods"."""
    return re.sub(r"(19|20)\d\d", "AAAA", name)


def mef_files():
    have = sorted(int(p.name) for p in MEF_DIR.iterdir() if p.name.isdigit())
    keep = {mef_kind(p.name) for p in (MEF_DIR / str(have[-1])).iterdir()}
    files, skipped = {}, []
    for year in [*have, have[-1] + 1]:
        page = MEF_PAGE.format(year=year)
        if year not in have and not page_exists(page):
            continue
        for label, url in page_links(page):
            if not label.startswith("Descargar:"):
                continue
            if mef_kind(file_name(url)) in keep:
                files[MEF_DIR / str(year) / file_name(url)] = url
            else:
                skipped.append(f"{year}/{file_name(url)}")
    return files, skipped


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
    wanted, skipped = src["files"]()
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
    notes = [f"- Skipped `{name}`: not a file we keep. Check it by hand before adding it." for name in skipped]
    if not changed:
        return [f"### {src['name']}", "", *notes, ""] if notes else []
    if src["build"] and not dry_run:
        subprocess.run([sys.executable, src["build"].name], cwd=src["build"].parent, check=True, stdout=sys.stderr)
    after = src["coverage"]()
    head = f"### {src['name']}\n\nCoverage: {before}" + (f" → **{after}**" if after != before else " (unchanged)")
    return [head, "", *changed, *notes, ""]


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
