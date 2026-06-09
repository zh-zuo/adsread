#!/usr/bin/env python3
"""adsread — fetch a paper's TeX or Markdown from arXiv, resolving ADS bibcodes/DOIs.

Like Hugging Face's `hf papers read`, but for astronomers: ADS is the resolver/metadata
layer, arXiv is the content source. Designed to dump clean paper text into an agent's
context (stdout by default).

Usage:
  adsread <arxiv-id | ADS-bibcode | DOI> [--format md|tex] [--out FILE]

Examples:
  adsread 2511.20639                      # arXiv id -> markdown on stdout
  adsread 2511.20639 -f tex -o paper.tex  # raw LaTeX source
  adsread 2025ApJ...991..157Z             # ADS bibcode (needs ADS_DEV_KEY)

Env:
  ADS_DEV_KEY (or ADS_TOKEN)  — only needed to resolve bibcodes/DOIs.
                                Free token: https://ui.adsabs.harvard.edu/user/settings/token
"""
import sys, os, re, io, gzip, tarfile, subprocess, argparse
import requests

UA = {"User-Agent": "adsread/0.1 (https://github.com/zh-zuo)"}
ARXIV_RE  = re.compile(r'^(\d{4}\.\d{4,5})(v\d+)?$')
BIBCODE_RE = re.compile(r'^\d{4}[A-Za-z0-9.&+]{14}[A-Z]$')   # 19 chars, ends in 1st-author initial
DOI_RE    = re.compile(r'^10\.\d{4,9}/\S+$', re.I)


def detect(idstr):
    s = idstr.strip()
    if s.lower().startswith('arxiv:'):
        s = s[6:]
    if ARXIV_RE.match(s):
        return 'arxiv', ARXIV_RE.match(s).group(1)
    if s.lower().startswith('doi:'):
        return 'doi', s[4:]
    if DOI_RE.match(s):
        return 'doi', s
    if BIBCODE_RE.match(s):
        return 'bibcode', s
    return 'unknown', s


def ads_to_arxiv(field, value):
    token = os.environ.get('ADS_DEV_KEY') or os.environ.get('ADS_TOKEN')
    if not token:
        sys.exit(f"[adsread] '{value}' needs ADS resolution but no token is set.\n"
                 f"          export ADS_DEV_KEY=... (free: https://ui.adsabs.harvard.edu/user/settings/token)\n"
                 f"          or pass the arXiv id directly.")
    r = requests.get("https://api.adsabs.harvard.edu/v1/search/query",
                     params={"q": f'{field}:"{value}"', "fl": "identifier,bibcode,title"},
                     headers={"Authorization": f"Bearer {token}", **UA}, timeout=30)
    if r.status_code == 401:
        sys.exit("[adsread] ADS rejected the token (401). Check ADS_DEV_KEY.")
    r.raise_for_status()
    docs = r.json().get("response", {}).get("docs", [])
    if not docs:
        sys.exit(f"[adsread] ADS found no record for {field}:{value}")
    for ident in docs[0].get("identifier", []):
        m = re.match(r'arXiv:(\d{4}\.\d{4,5})', ident, re.I)
        if m:
            return m.group(1)
    sys.exit(f"[adsread] ADS record {docs[0].get('bibcode')} has no arXiv e-print.")


def resolve_arxiv(idstr):
    kind, val = detect(idstr)
    if kind == 'arxiv':
        return val
    if kind in ('bibcode', 'doi'):
        return ads_to_arxiv(kind, val)
    return val  # unknown -> try as arXiv id


def fetch_tex(arxiv_id):
    r = requests.get(f"https://arxiv.org/e-print/{arxiv_id}", headers=UA, timeout=60)
    r.raise_for_status()
    data, texts = r.content, {}
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as tar:
            for m in tar.getmembers():
                if m.isfile() and m.name.lower().endswith('.tex'):
                    texts[m.name] = tar.extractfile(m).read().decode('utf-8', 'replace')
    except tarfile.ReadError:
        try:
            texts['main.tex'] = gzip.decompress(data).decode('utf-8', 'replace')
        except Exception:
            texts['main.tex'] = data.decode('utf-8', 'replace')
    if not texts:
        sys.exit(f"[adsread] no .tex in the e-print for {arxiv_id} (PDF-only submission?). Try -f md.")
    main = next((n for n, t in texts.items() if '\\documentclass' in t),
                max(texts, key=lambda n: len(texts[n])))

    def inline(t):
        def repl(m):
            fn = m.group(1).strip()
            base = os.path.basename(fn)
            for n in texts:
                if n in (fn, fn + '.tex') or os.path.basename(n) in (base, base + '.tex'):
                    return texts[n]
            return m.group(0)
        return re.sub(r'\\(?:input|include)\{([^}]+)\}', repl, t)

    return inline(texts[main])


def fetch_md(arxiv_id):
    for url in (f"https://arxiv.org/html/{arxiv_id}", f"https://ar5iv.org/html/{arxiv_id}"):
        try:
            r = requests.get(url, headers=UA, timeout=60, allow_redirects=True)
        except requests.RequestException:
            continue
        if r.status_code != 200 or '<html' not in r.text.lower():
            continue
        html = r.text
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            art = soup.find('article') or soup.find('div', class_=re.compile('ltx_page_main|ltx_document'))
            if art:
                for tag in art.find_all(True):   # strip LaTeXML class/id/style noise pandoc would keep
                    for a in [x for x in list(tag.attrs) if x in ('class', 'id', 'style') or x.startswith('data-')]:
                        del tag[a]
                for tag in art.find_all(['div', 'span']):   # flatten bare containers
                    tag.unwrap()
                html = str(art)
        except Exception:
            pass
        p = subprocess.run(
            ["pandoc", "-f", "html",
             "-t", "markdown-raw_html-fenced_divs-bracketed_spans-header_attributes-link_attributes",
             "--wrap=none"],
            input=html.encode(), capture_output=True)
        if p.returncode == 0 and p.stdout.strip():
            sys.stderr.write(f"[adsread] markdown via {url.split('//')[1].split('/')[0]}\n")
            return p.stdout.decode()
    sys.exit(f"[adsread] no HTML rendering for {arxiv_id} (arxiv.org/html or ar5iv). Try -f tex.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("identifier", help="arXiv id, ADS bibcode, or DOI")
    ap.add_argument("-f", "--format", choices=["md", "tex"], default="md")
    ap.add_argument("-o", "--out", help="write to FILE (default: stdout)")
    args = ap.parse_args()

    arxiv_id = resolve_arxiv(args.identifier)
    sys.stderr.write(f"[adsread] {args.identifier} -> arXiv:{arxiv_id} ({args.format})\n")
    out = fetch_tex(arxiv_id) if args.format == "tex" else fetch_md(arxiv_id)
    if args.out:
        with open(args.out, "w") as f:
            f.write(out)
        sys.stderr.write(f"[adsread] wrote {args.out} ({len(out):,} chars)\n")
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
