---
name: readability-analysis
description: Assess and improve the readability of text, web pages, or PDFs. Computes Flesch Reading Ease, Flesch-Kincaid, Gunning Fog, SMOG, ARI, Coleman-Liau, Linsear Write, Dale-Chall, Spache and a consensus grade level, then explains what the scores mean and how to simplify content. Use when the user asks how readable a document is, what grade level or reading age it targets, whether writing suits an audience, or asks to make text easier to read.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Readability Analysis

This skill measures how hard a piece of writing is to read and turns the raw
scores into actionable guidance. It is backed by the docstats readability
engine, which exposes a single capability: `get_readability_scores`.

## When to use this skill

- The user asks "what grade level / reading age is this?" or "how readable is
  this?"
- The user wants to check whether a document fits a target audience (e.g. a
  general public page should sit around grade 8).
- The user asks to simplify, shorten, or grade-level-tune text.

## How to run it

### Preferred: the MCP tool

Call the `get_readability_scores` MCP tool (server `readability-docstats`,
provided by this plugin's `mcp.json`). Pass **exactly one** of these inputs —
supplying zero or more than one is a validation error:

- `text` — a string of the content to analyze.
- `web_url` — a publicly reachable URL. HTML pages are scraped
  (BeautifulSoup); `.pdf` URLs are extracted with pypdf.
- `gcs_pdf_uri` — a `gs://…` URI pointing at a PDF in Google Cloud Storage.

The tool returns a JSON object of scores (see **Interpreting the scores**).

### Fallback: CLI

If the MCP server is not wired up, the same engine runs from a clone of the
repo:

```bash
# One-shot STDIO MCP server (what mcp.json launches):
uv run python main.py --server-type mcp

# HTTP API server:
uv run python main.py --server-type fastapi --host 127.0.0.1 --port 8000
```

### Fallback: HTTP API

With the FastAPI server running, POST one source to `/scores/`:

```bash
curl -X POST "http://127.0.0.1:8000/scores/" \
  -H "Content-Type: application/json" \
  -d '{ "text": "This is a sample text for readability analysis." }'
```

Swap `text` for `web_url` or `gcs_pdf_uri` as needed (still exactly one).

## Important caveats

- **Short text is unreliable.** Under ~100 words most formulas are noisy; the
  engine logs a warning and results should be treated as indicative only.
  Feed at least a few paragraphs when possible.
- **`spache` may be `null`.** The Spache formula requires ~100 words; when the
  input is too short it is returned as `null` rather than a number. Don't treat
  a missing Spache value as an error.
- **`gcs_pdf_uri` needs Google credentials.** Reading from `gs://…` uses
  Application Default Credentials (ADC). If they are not configured, run
  `gcloud auth application-default login` (or set `GOOGLE_APPLICATION_CREDENTIALS`)
  before using a GCS source.
- **`uv` on first run** may need network access to resolve dependencies. In an
  offline environment, run `uv sync` beforehand where the network is available.

## Interpreting the scores

Most fields are **U.S. grade levels** — the number of years of schooling a
reader needs to understand the text on one read. Lower is easier.

| Score | Meaning | Direction |
|---|---|---|
| `flesch_reading_ease` | 0–100 scale; **higher = easier** (90–100 ≈ 5th grade, 60–70 ≈ plain English, <30 = very difficult) | higher is easier |
| `flesch_kincaid_grade` | U.S. grade level | lower is easier |
| `gunning_fog` | Years of education needed | lower is easier |
| `smog_index` | Grade level, tuned for health/consumer material | lower is easier |
| `automated_readability_index` | Grade level from characters/word | lower is easier |
| `coleman_liau_index` | Grade level from characters/word | lower is easier |
| `linsear_write_formula` | Grade level | lower is easier |
| `dale_chall_readability_score` | Uses a familiar-word list; ~4.9 or below ≈ grade 4 and under, 9–10 ≈ college | lower is easier |
| `spache` | Grade level for **primary-age** text; may be `null` | lower is easier |
| `text_standard` | **Consensus grade** across the formulas — the best single summary | lower is easier |
| `syllable_count` / `word_count` / `sentence_count` | Raw text statistics | — |

### Rough audience targets

- **Grade ≤ 6** — general public, marketing, health information for patients.
- **Grade 7–9** — most web content, news, product docs.
- **Grade 10–12** — informed adult readers, business writing.
- **Grade 13+** — academic, legal, and technical/specialist audiences.

Lead with `text_standard` (the consensus grade) and `flesch_reading_ease`, then
cite the individual formulas that support or dissent. When asked to simplify:
shorten sentences, prefer common words, cut multi-syllable jargon, and split
dense paragraphs — then re-score to confirm the grade level dropped.

For worked examples across primary, middle, academic, and legal text, see
[references/score-interpretation.md](references/score-interpretation.md).
