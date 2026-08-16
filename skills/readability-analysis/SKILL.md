---
name: readability-analysis
description: Assess and improve the readability and stylistic authenticity of text, web pages, or PDFs. Computes comprehensive readability scores (Flesch-Kincaid, Gunning Fog, SMOG, consensus grade level) and detects synthetic AI writing patterns (em dashes, throat-clearing openers, binary contrasts, high-offender adverbs). Use when reviewing technical drafts, tuning reading age, or evaluating AI writing assistance.
license: Apache-2.0
metadata:
  version: "1.1.0"
---

# Readability & Technical Editorial Analysis

This skill provides multi-dimensional analysis of text complexity and AI writing patterns, converting raw statistical metrics into actionable editorial guidance. It is backed by the `docstats` multi-protocol engine.

## Available MCP Tools (Server `readability-docstats`)

### 1. `analyze_document` (Preferred)
Performs comprehensive two-axis assessment:
- **Axis A (Readability):** 10 grade-level and reading ease formulas + consensus standard.
- **Axis B (AI Writing Patterns):** Deterministic counts and rates of prose em dashes, high-offender adverbs, throat-clearing openers, binary contrast frames, and rhythm variation. Computes `ai_tell_score` (0.0–10.0 scale, floor ≥ 7.0).

### 2. `get_readability_scores`
Calculates Axis A readability scores and raw text statistics (syllables, words, sentences).

### 3. `get_ai_pattern_scores`
Calculates Axis B editorial tell counts, rates, diagnostic flags, and `ai_tell_score`.

---

## How to Run It

### MCP Invocation
Pass **exactly one** source parameter:
- `text`: Plain text or markdown string.
- `web_url`: Publicly reachable HTML page or online PDF URL.
- `gcs_pdf_uri`: `gs://...` URI in Google Cloud Storage.

```json
// Example MCP Tool Call
{
  "name": "analyze_document",
  "arguments": {
    "text": "Your draft content here..."
  }
}
```

### CLI Fallback
```bash
# STDIO MCP Server
uv run python main.py --server-type mcp

# FastAPI REST Server (POST /analyze/, POST /scores/, POST /patterns/)
uv run python main.py --server-type fastapi --port 8000
```

---

## Interpreting the Two-Axis Scorecard

### Axis A: Readability & Audience Target Bands

| Target Band | Consensus Grade (`text_standard`) | Reading Ease (`flesch_reading_ease`) | Recommended Document Types |
|---|---|---|---|
| **Very Accessible** | Grade ≤ 6 | > 70 | Beginner tutorials, onboarding guides |
| **Accessible** | Grade 7–10 | 50–70 | General developer blog posts, READMEs |
| **Dense** | Grade 10–15 | 30–50 | Deep technical guides, architecture write-ups |
| **Very Dense** | Grade 15–20 | 10–30 | Formal specifications, RFCs, kernel docs |
| **Impenetrable** | Grade > 20 | < 10 | Academic papers, dense legal agreements |

### Axis B: AI Writing Pattern Tells

| Metric | Target / Passing Threshold | Actionable Guidance |
|---|---|---|
| `ai_tell_score` | **≥ 7.0 / 10.0** | Floor threshold; below 7.0 indicates heavy synthetic tropes. |
| `em_dash_count` | ≤ 0.5 per 100 words in prose | Sparse grammatical breaks allowed; remove rhetorical drama dashes. |
| `throat_clearing_count` | 0 | Cut openers ("Here's the thing:", "It's worth noting that"). |
| `binary_contrast_count` | 0 | Eliminate "Not X, it's Y" and "X isn't the problem, Y is" framing. |
| `adverb_ly_rate` | ≤ 1.5 per 100 words | Remove non-technical -ly adverbs ("fundamentally", "genuinely"). |
| `sentence_len_cv` | ≥ 0.20 | Vary sentence length; avoid metronomic pacing. |
| `flags` | Empty list | Address specific diagnostic suggestions returned by the tool. |

---

## Combined Verdict Matrix

| Axis A (Audience Fit) | Axis B (AI Tell Score) | Combined Recommendation |
|---|---|---|
| **In Band** | **≥ 7.0 (Pass)** | **Ship** (Text is well-calibrated and authentic). |
| **In Band** | **< 7.0 (Fail)** | **Revise for Voice** (Resolve Axis B diagnostic flags). |
| **Off-Target** | **≥ 7.0 (Pass)** | **Revise for Complexity** (Adjust sentence length / vocabulary for target audience). |
| **Off-Target** | **< 7.0 (Fail)** | **Full Rewrite** (Address both readability band and synthetic tropes). |
