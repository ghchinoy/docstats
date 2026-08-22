---
title: Getting Started
description: Install docstats with uv and run your first readability and house-style analysis, over MCP or the REST API.
sidebar:
  order: 2
---

Run docstats in under a minute. You will install it, start a server, and score a sample string.

## Prerequisites

- Python 3.10 or newer
- The [`uv`](https://docs.astral.sh/uv/) package manager

## Install

```bash
git clone https://github.com/ghchinoy/docstats.git
cd docstats
uv sync
```

If you plan to read PDFs from Google Cloud Storage (`gs://`), log in with Application Default Credentials:

```bash
gcloud auth application-default login
```

## Run it

docstats runs in three modes. Pick one:

```bash
# Start the MCP server over STDIO (for Claude Code, Gemini CLI, Cursor, etc.)
uv run python main.py --server-type mcp

# Or start the local REST API server
uv run uvicorn fastapi_app:fastapi_app --reload
```

See [Server Modes](/docstats/guides/server-modes/) for the full comparison, including the streamable HTTP transport.

## Your first request

With the REST server running, score a string:

```bash
curl -X POST "http://127.0.0.1:8000/scores/" \
  -H "Content-Type: application/json" \
  -d '{"text": "Docstats makes readability analysis fast, delightful, and robust."}'
```

Example response:

```json
{
  "flesch_reading_ease": 45.1,
  "flesch_kincaid_grade": 8.8,
  "text_standard": "8.0",
  "word_count": 8,
  "sentence_count": 1
}
```

:::note
Readability formulas become statistically noisy on short fragments. For meaningful scores, analyze at least ~100 words. See [Troubleshooting](/docstats/guides/troubleshooting/).
:::

## What each field means

- `flesch_reading_ease` — 0–100, higher is easier to read.
- `flesch_kincaid_grade` — U.S. grade level (years of education).
- `text_standard` — the consensus grade across all formulas; the most robust single number.
- `word_count` / `sentence_count` — raw statistics that explain *why* a score landed where it did.

For the full interpretation guide, read [Interpreting Scores](/docstats/guides/interpreting-scores/).

## Run the tests (optional)

```bash
# Full suite
uv run pytest

# Fast unit tests only (no network)
uv run pytest test_unit.py

# Skip slow integration tests
uv run pytest -m "not slow"
```

## Next steps

- [Inputs & Extraction](/docstats/guides/inputs-and-extraction/) — analyze web pages and PDFs, not just strings.
- [MCP & Agent Plugins](/docstats/integrations/mcp/) — connect docstats to your AI assistant.
- [CI Quality Gate](/docstats/guides/ci-quality-gate/) — enforce thresholds in your pipeline.
