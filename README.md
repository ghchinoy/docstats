# docstats

Docstats calculates readability scores and provides deterministic house-style linting for plain text, web pages, and PDFs. Designed as a post-hoc acceptance gate for CI/CD pipelines, PR reviews, and pre-publish editorial QA, docstats runs as an MCP server for AI coding assistants or as a FastAPI web service.

## Table of Contents
- [Features](#features)
- [Recommended Workflow: Post-Hoc Acceptance Gate](#recommended-workflow-post-hoc-acceptance-gate)
- [Quickstart](#quickstart)
- [Installation](#installation)
- [Agent Plugin & MCP Usage](#agent-plugin--mcp-usage)
- [Server Modes](#server-modes)
- [Development & Testing](#development--testing)
- [Readability Scores](#readability-scores)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License & Disclaimer](#license--disclaimer)

## Features

- **Readability scoring (Axis A):** Computes consensus grade level plus 9 standard formulas (Flesch Reading Ease, Flesch-Kincaid, Gunning Fog, SMOG, Coleman-Liau, and more).
- **House-style linting (Axis B):** Deterministic pattern checking for throat-clearing openers, binary contrast frames, non-technical filler adverbs, rhetorical em dashes, and rhythm indicators.
- **Multiple inputs:** Reads direct text, public web pages, and PDFs from web URLs or Google Cloud Storage (`gs://`).
- **Agent Plugin v1.0.0:** Native MCP STDIO tool (`readability-docstats`) and prompt skill (`readability-analysis`).
- **Flexible runtime:** Runs as a local REST API, an MCP STDIO server, or a streamable HTTP server.

## Recommended Workflow: Post-Hoc Acceptance Gate

Docstats is optimized as an **asynchronous acceptance gate and editorial linter** rather than an in-prompt generative dial. Empirical research indicates that injecting live numeric metrics during text generation does not improve prose quality over clear textual guidance and risks artificial metric gaming. Use `docstats` to audit drafts, run pre-commit checks, or gate documentation CI workflows.

## Quickstart

Run docstats right away with `uv`:

```bash
# Start the MCP server over STDIO (for Claude Code, Gemini CLI, Cursor, etc.)
uv run python main.py --server-type mcp

# Or start the local REST API server
uv run uvicorn fastapi_app:fastapi_app --reload
```

Send a test request to the REST API:

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

## Installation

### Prerequisites
- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) package manager

### Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/ghchinoy/docstats.git
cd docstats
uv sync
```

*(Optional)* If you read PDFs from Google Cloud Storage (`gs://`), log in with Application Default Credentials:
```bash
gcloud auth application-default login
```

## Agent Plugin & MCP Usage

Docstats implements the [Agent Plugins v1.0.0 spec](https://github.com/agentplugins/agent-plugins-spec). Agent runtimes find the plugin manifest, MCP tool, and skill guidance automatically.

| File | Purpose |
|---|---|
| [`plugin.json`](./plugin.json) | Plugin metadata and version information |
| [`mcp.json`](./mcp.json) | MCP STDIO server declaration |
| [`skills/readability-analysis/SKILL.md`](./skills/readability-analysis/SKILL.md) | Skill guidance for AI assistants |

### Manual MCP Client Setup

To configure an MCP client manually (such as in `~/.claude/settings.json` or Gemini CLI):

```json
{
  "mcpServers": {
    "readability_docstats": {
      "command": "uv",
      "args": ["run", "python", "/ABSOLUTE/PATH/TO/docstats/main.py", "--server-type", "mcp"],
      "cwd": "/ABSOLUTE/PATH/TO/docstats"
    }
  }
}
```

## Server Modes

Docstats supports three execution modes:

1. **MCP STDIO Server:**
   ```bash
   uv run python main.py --server-type mcp
   ```
2. **FastAPI REST API:**
   ```bash
   uv run uvicorn fastapi_app:fastapi_app --host 127.0.0.1 --port 8000 --reload
   ```
   Interactive Swagger docs open at `http://127.0.0.1:8000/docs`.
3. **MCP Streamable HTTP Server:**
   ```bash
   uv run python main.py --server-type mcp-http --host 127.0.0.1 --port 8001
   ```

## Development & Testing

### Run Tests
Run the test suite with pytest:

```bash
# Run all tests
uv run pytest

# Run fast unit tests only (no network needed)
uv run pytest test_unit.py

# Run tests without slow integration tests
uv run pytest -m "not slow"
```

### Golden Set Benchmarks
Check score consistency against baseline sample files:

```bash
uv run python baseline_analysis.py
```

### Code Quality
Run formatting and lint checks:

```bash
uv run ruff check .
uv run ruff format --check .
```

## Readability Scores

Docstats provides the following metrics:

| Metric | Target / Range | Description |
|---|---|---|
| **Text Standard** | Consensus grade | Best overall summary grade |
| **Flesch Reading Ease** | 0 to 100 (higher is easier) | 90–100: Grade 5; 60–70: Plain English; <30: Difficult |
| **Flesch-Kincaid Grade** | Grade level | Years of education needed |
| **Gunning Fog Index** | Grade level | Counts complex words with 3 or more syllables |
| **SMOG Index** | Grade level | Standard for consumer and health copy |
| **Coleman-Liau Index** | Grade level | Based on character count per word |
| **Automated Readability (ARI)** | Grade level | Based on letter and sentence counts |
| **Linsear Write** | Grade level | Common technical writing formula |
| **Dale-Chall Score** | 0.0 to 10.0+ | Measures hard words outside common word lists |
| **Spache Score** | Primary grade level | For primary school level texts |

## Documentation

The full documentation site is published at **[ghchinoy.github.io/docstats](https://ghchinoy.github.io/docstats/)** (built with Astro Starlight; source in [`site/`](./site/)). It covers a user-first explainer, MCP and skills integration, and technical deep dives on the linguistics and statistics.

Source-of-truth references:

- [User Guide](docs/user_guide.md) — Comprehensive guide to configuration, endpoints, extraction pipelines, and troubleshooting.
- [Scoring Specification](docs/scoring-spec.md) — Specification for two-axis assessment and house-style linting.
- [Readability Analysis Skill](skills/readability-analysis/SKILL.md) — Model-facing prompt skill and interpretation guide.

## Contributing

We welcome contributions!

1. Fork and clone the repository.
2. Create a feature branch (`git checkout -b feature/my-feature`).
3. Run tests (`uv run pytest`) and linters (`uv run ruff check .`).
4. Check baseline scores (`uv run python baseline_analysis.py`).
5. Open a Pull Request.

## License & Disclaimer

- **License:** Apache License 2.0. See [LICENSE](./LICENSE) for details.
- **Disclaimer:** This is not an officially supported Google product.