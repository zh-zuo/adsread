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

> `adsread` below is the installed command (see [Install](#install)); without that, use `python3 adsread.py …`.

- `-f md` (default) — `arxiv.org/html` → fallback `ar5iv.org` → pandoc, LaTeXML noise stripped, math kept as `$…$`.
- `-f tex` — downloads `arxiv.org/e-print/<id>`, extracts the tarball, inlines `\input`/`\include`.
- `-o FILE` — write to file instead of stdout.

## Install

`adsread` is a single Python script — clone it and run it. Requirements:

- **Python 3.8+** with `requests` and `beautifulsoup4`
- **pandoc** on your PATH — needed only for Markdown (`-f md`); the `-f tex` path needs nothing else

```bash
git clone https://github.com/zh-zuo/adsread.git
cd adsread
pip install -r requirements.txt          # requests, beautifulsoup4  (a venv is optional but tidy)
python3 adsread.py 2511.20639            # smoke test
```

Install **pandoc** for your platform:

| OS | command |
|----|---------|
| macOS | `brew install pandoc` |
| Debian / Ubuntu | `sudo apt install pandoc` |
| Fedora | `sudo dnf install pandoc` |
| Arch | `sudo pacman -S pandoc` |
| Windows | `winget install JohnMacFarlane.Pandoc` (or `choco install pandoc`) |
| other | download from <https://pandoc.org/installing.html> |

That's enough — `python3 adsread.py <id>` works from the cloned folder.

### Optional: a bare `adsread` command

```bash
chmod +x adsread.py
mkdir -p ~/.local/bin
ln -s "$PWD/adsread.py" ~/.local/bin/adsread     # make sure ~/.local/bin is on your PATH
adsread 2511.20639
```

The bare command runs under your *default* `python3` (via the `#!/usr/bin/env python3` shebang), so
make sure `requests`/`beautifulsoup4` are installed for **that** interpreter (e.g. `pip install
--user requests beautifulsoup4`) — or just keep calling `python3 /path/to/adsread.py`. On **Windows**
use `python adsread.py <id>` (symlinks need Developer Mode; an alias or a tiny `.bat` wrapper is simpler).

## ADS token (only for bibcodes / DOIs)

Plain arXiv ids need **no** token. To resolve **bibcodes/DOIs**, grab a free key at
<https://ui.adsabs.harvard.edu/user/settings/token> and set `ADS_DEV_KEY` in your environment:

```bash
export ADS_DEV_KEY="your-token"        # bash/zsh — add to ~/.bashrc or ~/.zshrc
# fish:         set -Ux ADS_DEV_KEY your-token
# Windows (PS): setx ADS_DEV_KEY "your-token"
```

## Optional: use it as an agent skill

If your coding agent supports [Agent Skills](https://agentskills.io) — Claude Code, Codex, Cursor,
OpenCode, … — this repo *is* a skill (`SKILL.md` + `adsread.py`), so the agent reads papers on
demand. Link the cloned repo into the skills folder your agent watches:

```bash
cd adsread     # the folder you cloned

# shared location read by Codex / Cursor / OpenCode / …
mkdir -p ~/.agents/skills && ln -s "$PWD" ~/.agents/skills/adsread
# Claude Code
mkdir -p ~/.claude/skills && ln -s "$HOME/.agents/skills/adsread" ~/.claude/skills/adsread
# Codex (if it reads ~/.codex/skills)
mkdir -p ~/.codex/skills  && ln -s "$HOME/.agents/skills/adsread" ~/.codex/skills/adsread
```

Then *"read arXiv 2511.20639"* / *"summarize this bibcode"* / *"what does this paper say"* triggers it.
(On **Windows** without Developer Mode, copy the folder into the skills dir instead of symlinking.)
Not using an Agent-Skills agent? Skip this entirely — just tell your agent to run `python3 adsread.py <id>`.

## Notes / limits

- **PDF-only** submissions have no `.tex` → use `-f md` (or there may be no HTML either).
- Complex **tables** fall back to inline HTML in the markdown (still readable).
- Figures appear as image links with arXiv-relative paths (not downloaded).

## Possible next steps

- Package as a Claude Code skill (mirror `hf skills add --claude`) so agents invoke it directly.
- `--abstract-only`, `--strip-figures`, `--bibtex`, batch input, local caching.
- A reverse `--bib` mode: given an arXiv id, print the ADS BibTeX entry.
