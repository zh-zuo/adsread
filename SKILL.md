---
name: adsread
description: >
  Fetch the full text (clean Markdown or raw LaTeX) of a paper from arXiv — resolving NASA ADS
  bibcodes and DOIs to the arXiv id — so the whole paper can be read in context, not just the
  abstract. Use this skill whenever the user references a paper by arXiv id (e.g. 2511.20639),
  ADS bibcode (e.g. 2025ApJ...991..157Z), or DOI and wants it read, summarized, quoted, or its
  methods / results / limitations analyzed. Triggers: "read this paper", "fetch arXiv <id>",
  "pull the tex/markdown for <bibcode>", "what does <paper> actually say", "get the full text of
  <id>", "summarize <arxiv id>". Prefer this over fetching only the abstract when the user wants
  the actual paper content.
---

# adsread — fetch a paper's full text from arXiv

Pulls clean **Markdown** (default) or raw **LaTeX** for a paper so you can read the *whole* thing.
ADS is the resolver (bibcode/DOI → arXiv id); arXiv is the content source. Source / issues:
<https://github.com/zh-zuo/adsread>.

## How to run

`adsread.py` sits next to this `SKILL.md` (the repo is the skill). Run it and read its stdout into
your context, then answer the user. If installed the standard way the path is
`~/.agents/skills/adsread/adsread.py`:

```bash
# Markdown (default): clean text, LaTeXML noise stripped, math kept as $...$  — best for reading
python3 ~/.agents/skills/adsread/adsread.py 2511.20639

# Raw LaTeX source (e-print tarball, \input/\include inlined)
python3 ~/.agents/skills/adsread/adsread.py 2511.20639 -f tex

# ADS bibcode or DOI (needs ADS_DEV_KEY in the environment)
python3 ~/.agents/skills/adsread/adsread.py 2025ApJ...991..157Z

# Write to a file instead of stdout (useful for long papers)
python3 ~/.agents/skills/adsread/adsread.py 2511.20639 -o /tmp/paper.md
```

If `adsread` is on the user's PATH, `adsread <id>` works too.

## Requirements

- Python 3 with `requests` + `beautifulsoup4`; `pandoc` on PATH (for `-f md`).
- `ADS_DEV_KEY` env var **only** for bibcode/DOI input (free token:
  <https://ui.adsabs.harvard.edu/user/settings/token>). Plain arXiv ids need no token.

## Notes

- PDF-only submissions have no `.tex` → use `-f md` (or there may be no HTML either).
- Long papers can be big; prefer `-o FILE` then read the sections you need.
- Complex tables fall back to inline HTML in the Markdown (still readable).
