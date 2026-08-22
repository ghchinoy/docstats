---
title: Getting Started
description: Install docstats with uv and run your first readability analysis over MCP or the REST API.
sidebar:
  order: 2
---

Get started with docstats in under a minute by installing the package, starting a server, and scoring sample text.

## Prerequisites

- Python 3.10 or newer
- [`uv`](https://docs.astral.sh/uv/) package manager

## Installation

```bash
git clone https://github.com/ghchinoy/docstats.git
cd docstats
uv sync
```

To read PDFs from Google Cloud Storage (`gs://`), authenticate with Application Default Credentials:

```bash
gcloud auth application-default login
```

## Server Startup

docstats supports three execution modes:

```bash
# Start the MCP server over STDIO (for Claude Code, Gemini CLI, Cursor, etc.)
uv run python main.py --server-type mcp

# Start the local REST API server
uv run uvicorn fastapi_app:fastapi_app --reload
```

See [Server Modes](/docstats/guides/server-modes/) for detailed runtime options, including streamable HTTP transport.

## First Request

With the REST server running, send a scoring request:

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
Readability formulas exhibit variance on short passages. For stable metrics, analyze samples of at least 100 words. See [Troubleshooting](/docstats/guides/troubleshooting/).
:::

## Score Fields

- `flesch_reading_ease`: Scale of 0–100, where higher scores indicate easier reading.
- `flesch_kincaid_grade`: U.S. grade level estimate (years of formal education).
- `text_standard`: Cross-formula consensus grade level.
- `word_count` / `sentence_count`: Structural metrics underlying formula calculations.

For complete field explanations and target bands, see [Interpreting Scores](/docstats/guides/interpreting-scores/).

## Test Suite

```bash
# Full test suite
uv run pytest

# Fast unit tests (no network access required)
uv run pytest test_unit.py

# Exclude slow integration tests
uv run pytest -m "not slow"
```

## Next Steps

- [Inputs & Extraction](/docstats/guides/inputs-and-extraction/): Process web pages, PDF documents, and raw text.
- [MCP & Agent Plugins](/docstats/integrations/mcp/): Connect docstats to AI assistant environments.
- [CI Quality Gate](/docstats/guides/ci-quality-gate/): Add docstats checks to automated pull request workflows.
