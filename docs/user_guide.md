# Docstats User Guide

Comprehensive documentation for running, configuring, and integrating **docstats** as a REST API, Model Context Protocol (MCP) server, or Agent Plugin.

---

## Table of Contents
- [1. Overview & Architecture](#1-overview--architecture)
- [2. Input Sources & Extraction](#2-input-sources--extraction)
- [3. Execution Modes](#3-execution-modes)
  - [FastAPI HTTP Server](#fastapi-http-server)
  - [MCP STDIO Server](#mcp-stdio-server)
  - [MCP Streamable HTTP Server](#mcp-streamable-http-server)
- [4. AI Agent Integration (MCP & Plugin)](#4-ai-agent-integration-mcp--plugin)
- [5. Metric Definitions & Interpretations](#5-metric-definitions--interpretations)
- [6. Two-Axis Assessment (Readability + AI Patterns)](#6-two-axis-assessment-readability--ai-patterns)
- [7. Golden Set Benchmarking & Quality Gates](#7-golden-set-benchmarking--quality-gates)
- [8. Troubleshooting & Edge Cases](#8-troubleshooting--edge-cases)

---

## 1. Overview & Architecture

Docstats evaluates written documents along two primary dimensions:
1. **Axis A (Readability):** Ten standardized readability formulas and consensus grade levels.
2. **Axis B (House-Style Linting):** Deterministic pattern checking (e.g. non-technical filler adverbs, throat-clearing openers, binary contrast frames, and rhythm indicators).

Docstats is designed as a **post-hoc acceptance gate** (for CI/CD pipelines, PR checks, and pre-publish QA) rather than an in-loop generative dial. Empirical research demonstrates that providing live numeric metrics during text generation does not improve quality over pure editorial guidelines and risks artificial metric gaming.

Docstats is built with Python (3.10+) using `textstat`, `py-readability-metrics`, `fastapi`, and the official `mcp` SDK.

```
                  +--------------------------------+
                  |         Text Sources           |
                  |  (Direct Text / URL / GCS PDF) |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |      Extraction Pipeline       |
                  |  (BeautifulSoup4 / PyPDF / GCS)|
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |         Analysis Engine        |
                  | (Axis A: Metrics / Axis B: AI) |
                  +---------------+----------------+
                                  |
        +-------------------------+-------------------------+
        |                         |                         |
        v                         v                         v
+---------------+         +---------------+         +---------------+
|  FastAPI REST |         |   MCP STDIO   |         | MCP HTTP / SSE|
| (Port 8000)   |         | (Agent Subproc|         | (Port 8001)   |
+---------------+         +---------------+         +---------------+
```

---

## 2. Input Sources & Extraction

Docstats accepts exactly one input source per request:

### Direct Text (`text`)
Raw plaintext string. Ideal for interactive queries, inline code comments, or editor buffers.

### Web URL (`web_url`)
A publicly accessible `http://` or `https://` URL.
- **HTML Pages:** Content is fetched and parsed with `BeautifulSoup`, stripping `<script>`, `<style>`, and navigation boilerplate to extract the main article prose.
- **Web PDFs:** If the URL ends with `.pdf` (or returns `application/pdf`), the document is streamed and extracted page-by-page using `pypdf`.

### Google Cloud Storage PDF (`gcs_pdf_uri`)
A URI pointing to a PDF file in Google Cloud Storage in the format:
```
gs://bucket-name/path/to/document.pdf
```
*Authentication:* Requires Google Cloud Application Default Credentials (ADC). Configure credentials locally via:
```bash
gcloud auth application-default login
```
or by setting the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to a service account key path.

---

## 3. Execution Modes

Docstats can be launched via `main.py` or dedicated runners.

### FastAPI HTTP Server

Provides a standard RESTful API with interactive Swagger / OpenAPI docs.

**Recommended for development (with auto-reload):**
```bash
uv run uvicorn fastapi_app:fastapi_app --host 127.0.0.1 --port 8000 --reload
```

**Interactive Swagger UI:** Visit `http://127.0.0.1:8000/docs` in your browser.

**Example REST API Request (Direct Text):**
```bash
curl -X POST "http://127.0.0.1:8000/scores/" \
  -H "Content-Type: application/json" \
  -d '{"text": "The quick brown fox jumps over the lazy dog."}'
```

**Example REST API Request (Web URL):**
```bash
curl -X POST "http://127.0.0.1:8000/scores/" \
  -H "Content-Type: application/json" \
  -d '{"web_url": "https://en.wikipedia.org/wiki/Readability"}'
```

---

### MCP STDIO Server

Communicates over standard input/output using JSON-RPC. This is the primary interface for AI agent runtimes (Claude Code, Gemini CLI, Cursor, Antigravity).

**Launch Command:**
```bash
uv run python main.py --server-type mcp
```

---

### MCP Streamable HTTP Server

Exposes the MCP server over HTTP using Server-Sent Events (SSE) or plain JSON responses.

**Launch Command (SSE Streaming):**
```bash
uv run python main.py --server-type mcp-http --host 127.0.0.1 --port 8001
```

**Launch Command (Plain JSON Responses):**
```bash
uv run python main.py --server-type mcp-http --mcp-http-json-response --host 127.0.0.1 --port 8001
```

---

## 4. AI Agent Integration (MCP & Plugin)

### Agent Plugins v1.0.0 Standard

Docstats conforms to the [Agent Plugins v1.0.0 Specification](https://github.com/agentplugins/agent-plugins-spec).

Root-level manifest files:
- [`plugin.json`](file:///Users/ghchinoy/projects/docstats/plugin.json): Declares plugin metadata, tools, and skills.
- [`mcp.json`](file:///Users/ghchinoy/projects/docstats/mcp.json): Declares the STDIO server command using `${PLUGIN_ROOT}`:
  ```json
  {
    "mcpServers": {
      "readability-docstats": {
        "command": "uv",
        "args": ["run", "python", "${PLUGIN_ROOT}/main.py", "--server-type", "mcp"]
      }
    }
  }
  ```
- [`skills/readability-analysis/`](file:///Users/ghchinoy/projects/docstats/skills/readability-analysis/): Contains the prompt skill and reference interpretation guide.

### Manual Client Configuration

To configure clients that do not automatically discover plugin manifests:

**Claude Code (`~/.claude/settings.json`) or Gemini CLI (`~/.gemini/settings.json`):**
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

---

## 5. Metric Definitions & Interpretations

| Metric | Output Range | Description & Target Audience |
|---|---|---|
| **Text Standard** | Consensus Grade | Aggregate consensus grade level across all formulas. |
| **Flesch Reading Ease** | 0–100 (*Higher = Easier*) | 90–100: Grade 5 (very easy)<br>60–70: Plain English (Grade 8–9)<br>30–50: College level<br><30: Academic/Legal |
| **Flesch-Kincaid Grade** | U.S. Grade Level | Corresponds to years of U.S. formal education. |
| **Gunning Fog Index** | U.S. Grade Level | Weights words with 3+ syllables; penalizes jargon. |
| **SMOG Index** | U.S. Grade Level | Standard metric in health and medical writing. |
| **Coleman-Liau Index** | U.S. Grade Level | Calculated from letter count per 100 words. |
| **Automated Readability (ARI)** | U.S. Grade Level | Calculated from characters per word and words per sentence. |
| **Linsear Write** | U.S. Grade Level | Developed for U.S. Air Force technical manuals. |
| **Dale-Chall Score** | 0.0–10.0+ | Evaluates text against a list of 3,000 common words. |
| **Spache Score** | Grade Level | Specifically calibrated for primary texts under 4th grade. |

---

## 6. Two-Axis Assessment (Readability + House-Style Linting)

Docstats provides unified two-axis evaluation via `analyze_document`:

```json
{
  "readability": {
    "flesch_reading_ease": 45.1,
    "flesch_kincaid_grade": 8.8,
    "text_standard": "8.0",
    "word_count": 250,
    "sentence_count": 18
  },
  "ai_patterns": {
    "em_dash_count": 0,
    "em_dash_rate": 0.0,
    "adverb_ly_count": 2,
    "adverb_ly_rate": 0.8,
    "throat_clearing_count": 0,
    "binary_contrast_count": 0,
    "wh_starter_count": 0,
    "wh_starter_rate": 0.0,
    "fragment_count": 0,
    "list_of_three_count": 0,
    "sentence_len_cv": 0.65,
    "vague_declarative_count": 0,
    "passive_hint_count": 1,
    "total_tells": 0,
    "ai_tell_score": 10.0,
    "confidence": "high",
    "flags": []
  }
}
```

### House-Style Pattern Indicators (Axis B)
Axis B evaluates deterministic editorial rules rather than functioning as a statistical AI detector (empirical benchmarks show low classification capability for detection, e.g., AUC = 0.577 general, 0.403 technical). It enforces clean, direct technical prose:
- **High-Offender Adverbs:** Flags non-technical filler adverbs (e.g. *seamlessly*, *delicately*, *testament*).
- **Throat-Clearing Openers:** Flags rhetorical announcements (*"It is important to remember that..."*, *"In today's fast-paced world..."*).
- **Binary Contrast Frames:** Detects artificial antithesis (*"It's not just X, it's Y"*).
- **Rhythm Indicator (Advisory):** Measures sentence length coefficient of variation (CV). A low CV (< 0.20) signals potential monotone pacing. *Note: CV is an advisory hint only; do NOT enforce numeric CV targets in generation prompts as it degrades natural sentence rhythm.*

---

## 7. Golden Set Benchmarking & Non-Circular Evaluation

The `samples/` directory contains reference texts across difficulty levels:
- `level_primary.txt` (Grade ~1)
- `level_middle.txt` (Grade ~12-15)
- `level_academic.txt` (Grade ~22-23)
- `level_legal.txt` (Grade ~25)

### Internal Drift Anchors vs External Evaluation
- **Internal Drift Anchors (Golden Set):** The baseline sample files anchor internal regression tests (`baseline_analysis.py`). They ensure that changes to parsing, tokenization, or formula implementations produce zero unexpected drift in calculated scores.
- **Independent Non-Circular External Validation:** When evaluating the quality of text generated or edited by AI agents, docstats scores should not be used as the sole circular judge. Rigorous evaluations must utilize independent, decoupled scoring frameworks (e.g., blind human/LLM comparative judging, held-out readability grading, and non-parametric statistical tests like Wilcoxon signed-rank).

### Running Baseline Verification
Run the baseline analyzer to confirm zero drift after changing extraction or metric algorithms:
```bash
uv run python baseline_analysis.py
```

### Running Test Quality Gates
```bash
# Run full test suite
uv run pytest

# Run linter and formatter
uv run ruff check .
uv run ruff format --check .
```

---

## 8. Troubleshooting & Edge Cases

### Short Text Warning (< 100 words)
Readability algorithms become statistically noisy on short text fragments. When analyzing inputs under 100 words, docstats logs a warning and scores should be considered indicative.

### `spache` Returns `null`
The Spache formula requires a minimum sample length and is designed only for primary-grade writing. A `null` value is normal for adult/technical texts or short samples.

### Google Cloud ADC Error
If receiving authentication errors when processing `gs://` URIs:
```bash
gcloud auth application-default login
```
Ensure the authenticated Google account or service account has `roles/storage.objectViewer` on the target bucket.
