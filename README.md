# adsread

Fetch a paper's **TeX** or **Markdown** from arXiv, resolving NASA-ADS bibcodes / DOIs —
the astronomer's answer to Hugging Face's `hf papers read`. Dumps clean paper text into an
agent's context (stdout by default), so a coding/research agent can actually *read* the paper.

**Design:** ADS is the resolver/metadata layer, arXiv is the content source.
`bibcode → (ADS API) → arXiv id → fetch`. arXiv ids and DOIs work too.

## Usage

```bash
adsread 2511.20639                       # arXiv id  -> Markdown on stdout
adsread 2511.20639 -f tex -o paper.tex   # raw LaTeX source (e-print tarball)
adsread 2025ApJ...991..157Z              # ADS bibcode (needs ADS_DEV_KEY)
adsread 10.3847/1538-4357/ade8f0         # DOI        (needs ADS_DEV_KEY)
```

- `-f md` (default) — `arxiv.org/html` → fallback `ar5iv.org` → pandoc, LaTeXML noise stripped, math kept as `$…$`.
- `-f tex` — downloads `arxiv.org/e-print/<id>`, extracts the tarball, inlines `\input`/`\include`.
- `-o FILE` — write to file instead of stdout.

## Install

Requires **Python 3** with `requests` + `beautifulsoup4`, and **pandoc** on your PATH (for `-f md`).

```bash
pip install -r requirements.txt          # requests, beautifulsoup4
# pandoc:  brew install pandoc  (macOS)  /  apt install pandoc  (Linux)
chmod +x adsread.py
./adsread.py 2511.20639
```

Put it on your PATH (pick one):

```bash
ln -s "$PWD/adsread.py" /usr/local/bin/adsread        # symlink
# or, in ~/.zshrc:  alias adsread="$HOME/Documents/AI/adsread/adsread.py"
```

## ADS token (only for bibcodes / DOIs)

arXiv ids need no token. To resolve **bibcodes/DOIs**, get a free key at
<https://ui.adsabs.harvard.edu/user/settings/token> and:

```bash
export ADS_DEV_KEY="your-token"     # add to ~/.zshrc
```

## Use as an agent skill (Claude Code & Codex)

This repo doubles as an [Agent Skill](https://agentskills.io) (`SKILL.md` + `adsread.py`), so a
coding/research agent can read papers on demand. One `SKILL.md` serves both agents. Install (one
source, symlinked into each agent's skills dir):

```bash
git clone https://github.com/zh-zuo/adsread.git
ln -s "$PWD/adsread"            ~/.agents/skills/adsread     # Codex, Cursor, OpenCode, …
ln -s ../../.agents/skills/adsread ~/.claude/skills/adsread  # Claude Code
ln -s ../../.agents/skills/adsread ~/.codex/skills/adsread   # Codex (explicit)
```

Then in a chat — *"read arXiv 2511.20639"*, *"summarize this bibcode"*, *"what does <paper> say"* —
the agent invokes `adsread` and pulls the full text into context.

## Notes / limits

- **PDF-only** submissions have no `.tex` → use `-f md` (or there may be no HTML either).
- Complex **tables** fall back to inline HTML in the markdown (still readable).
- Figures appear as image links with arXiv-relative paths (not downloaded).

## Possible next steps

- Package as a Claude Code skill (mirror `hf skills add --claude`) so agents invoke it directly.
- `--abstract-only`, `--strip-figures`, `--bibtex`, batch input, local caching.
- A reverse `--bib` mode: given an arXiv id, print the ADS BibTeX entry.
