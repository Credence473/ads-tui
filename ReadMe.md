# ads-tui

A terminal user interface for searching NASA ADS papers, selecting papers with `fzf`, downloading PDFs, and managing BibTeX references.

Designed for astronomers who prefer working from the terminal.

---

## Features

- Search NASA ADS from the command line
- Interactive paper selection using `fzf`
- Preview paper information:
  - Title
  - Authors
  - Abstract
  - DOI
  - Citation count
  - Keywords
- Download PDFs
- Export BibTeX
- Copy BibTeX to the clipboard
- Append references to an existing `.bib` file
- Copy DOI
- Open ADS pages in a browser
- SQLite caching of searches and metadata

---

# Installation

## Requirements

- Python 3.11 or newer
- `fzf`
- `xdg-open` (Linux)

### Install `fzf`

#### Debian / Ubuntu

```bash
sudo apt install fzf
```

Or follow the instructions at [fzf GitHub](https://github.com/junegunn/fzf#installation).


## Install `ads-tui`:

```bash 
pip install git+https://github.com/Credence473/ads-tui.git
```

Or using `uv`:

```bash
uv tool install git+https://github.com/Credence473/ads-tui.git
```

Or for development:

```bash
git clone https://github.com/Credence473/ads-tui.git
cd ads-tui
pip install -e .
```

---

# ADS API Token

ADS requires an API token.

Create one at:

https://ui.adsabs.harvard.edu/user/settings/token

Set it temporarily:

```bash
export ADS_API_TOKEN="your_token_here"
```

To make it permanent:

```bash
echo 'export ADS_API_TOKEN="your_token_here"' >> ~/.bashrc
```

Alternatively, edit:

```text
~/.config/ads-tui/config.toml
```

Example:

```toml
token = "your_token_here"
```

---

# Usage
Search ADS papers from the terminal.
The query can be a simple string or a comma-separated list of field:value pairs. For example: 'author:Smith,year:2020'.
The following shorthands are also available for common fields:
'a' for author,
'fa' for first_author,
'abs' for abstract,
'y' for year,
'ft' for full text, and
'pub' for publication.
Additionally, the keyword 'astro' can be used to filter results to the astronomy collection. Example: 'astro,author:Smith,year:2020'.

## Search ADS

```bash
ads-tui "magneto asteroseismology"
```

or

```bash
ads-tui "first_author:Casamiquela,year:2024,author:Jash,astro"
```

or

```bash
ads-tui "fa:Casamiquela,y:2024,a:Jash,astro"
```

## Change the number of results

The default is **10 papers**.

For example:

```bash
ads-tui "TESS asteroseismology" -n 25
```

## Multiple selection

Enable multi-selection:

```bash
ads-tui "PLATO stellar oscillations" --multi
```

Inside `fzf`:

| Key | Action |
|------|--------|
| `SPACE` | Select paper |
| `ENTER` | Confirm selection |

---

# Actions

After selecting one or more papers:

| Key | Action |
|------|--------|
| `b` | Copy BibTeX |
| `s` | Save BibTeX |
| `a` | Append BibTeX to `references.bib` |
| `p` | Download PDF |
| `o` | Open PDF |
| `d` | Copy DOI |
| `u` | Open ADS page |
| `q` | Quit |

---

# Configuration

Configuration file:

```text
~/.config/ads-tui/config.toml
```

Example:

```toml
token = ""

results = 10

prefer_arxiv = true

cache_days = 30

download_dir = "~/Downloads/Paper"

default_bib = "~/Downloads/Paper/references.bib"
```

---

# Cache

SQLite cache location:

```text
~/.cache/ads-tui/cache.sqlite
```

Cached data includes:

- Search results
- Paper metadata
- BibTeX entries

Default cache lifetime:

```toml
cache_days = 30
```

---

# Example Workflow

Search:

```bash
ads-tui "fossil magnetic fields hot stars"
```

Select papers:

```text
2025 Smith et al. Magnetic fields in B stars
2024 Neiner et al. Fossil fields and rotation
```

Press:

```text
b
```

BibTeX is copied to the clipboard:

```bibtex
@ARTICLE{2025ApJ....
...
}
```

Paste directly into your manuscript:

```latex
\cite{2025ApJ....}
```

---

# Development

Run locally:

```bash
python -m ads_tui.cli search "asteroseismology"
```

---

# Roadmap

Planned features:

- Search by first author, author, year, or journal
- Citation graph exploration

# Acknowledgements
This project uses the [NASA ADS API](https://ui.adsabs.harvard.edu/help/api/).

![License](https://img.shields.io/badge/license-MIT-green.svg)
