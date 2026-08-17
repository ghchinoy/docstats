---
name: readability-analysis
description: Assess readability and lint technical prose for house-style conformity and synthetic writing patterns. Computes comprehensive readability scores (Flesch-Kincaid, Gunning Fog, SMOG, consensus grade level) and provides deterministic house-style linting (throat-clearing openers, binary contrasts, non-technical adverbs, rhetorical em dashes). Designed as a post-hoc acceptance gate and editorial QA linter.
license: Apache-2.0
metadata:
  version: "1.2.0"
---

# Readability & Technical Editorial Analysis

This skill provides multi-dimensional analysis of text complexity and house-style linting, converting raw statistical metrics into actionable editorial guidance. It is backed by the `docstats` multi-protocol engine.

> **Design Role:** `docstats` is designed as a **post-hoc acceptance gate** (for CI/CD pipelines, PR reviews, and pre-publish QA) rather than an in-loop generative dial. Empirical evaluations show that injecting live numeric metrics during generation does not improve prose quality over clear textual guidance and risks artificial metric gaming.

## Available MCP Tools (Server `readability-docstats`)

### 1. `analyze_document` (Preferred)
Performs comprehensive two-axis assessment:
- **Axis A (Readability):** 10 grade-level and reading ease formulas + consensus standard.
- **Axis B (House-Style Linting):** Deterministic counts and rates of throat-clearing openers, binary contrast frames, non-technical filler adverbs, prose em dashes, and rhythm variation hints. Computes `ai_tell_score` (0.0–10.0 scale, floor ≥ 7.0).

### 2. `get_readability_scores`
Calculates Axis A readability scores and raw text statistics (syllables, words, sentences).

### 3. `get_ai_pattern_scores`
Calculates Axis B house-style lint counts, rates, diagnostic flags, and `ai_tell_score`.

---

## How to Run It

### Recommended Workflow: Post-Hoc Acceptance Gate
Use `docstats` asynchronously after drafting or during automated review:
1. Generate or edit the draft using qualitative editorial guidelines.
2. Run `analyze_document` as a quality gate.
3. If Axis B or Axis A fails, apply targeted edits to resolve diagnostic flags.

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

### Axis B: House-Style Linting & Pattern Tells

> **Empirical Context:** Axis B patterns are **deterministic house-style linting checks**, not a statistical AI classifier. Empirical benchmarks show heuristic pattern detectors achieve low classification capability (AUC = 0.577 general, AUC = 0.403 technical; em-dash correlation is even inverted in technical prose). Axis B enforces crisp, uncluttered technical style regardless of author provenance.

| Metric | Target / Passing Threshold | Actionable Guidance |
|---|---|---|
| `ai_tell_score` | **≥ 7.0 / 10.0** | Floor threshold; below 7.0 indicates high density of forbidden stylistic tropes. |
| `em_dash_count` | ≤ 0.5 per 100 words in prose | Sparse grammatical breaks allowed; eliminate rhetorical drama dashes. |
| `throat_clearing_count` | 0 | Cut openers ("Here's the thing:", "It's worth noting that", "In today's..."). |
| `binary_contrast_count` | 0 | Eliminate "Not X, it's Y" and "X isn't the problem, Y is" framing. |
| `adverb_ly_rate` | ≤ 1.5 per 100 words | Remove non-technical -ly filler adverbs ("fundamentally", "genuinely"). |
| `sentence_len_cv` | *Advisory Hint* (~0.20–0.40) | Advisory rhythm indicator only. **Do NOT** enforce strict numeric CV targets in generation prompts (research shows this degrades natural sentence rhythm variation). |
| `flags` | Empty list | Address specific diagnostic suggestions returned by the tool. |

---

## Combined Verdict Matrix & Provenance-Aware Guidance

The acceptance verdict combines audience fit (Axis A) and house-style compliance (Axis B), adapted by document provenance:

| Axis A (Audience Fit) | Axis B (Style Score) | General Verdict | Provenance-Aware Guidance |
|---|---|---|---|
| **In Band** | **≥ 7.0 (Pass)** | **Ship** | Ready to publish. Text is well-calibrated and authentic. |
| **In Band** | **< 7.0 (Fail)** | **Revise for Voice** | **Raw AI Draft:** Aggressively restructure to remove synthetic tropes.<br>**Human Text:** Apply light-touch linting on specific flags; preserve authorial voice. |
| **Off-Target** | **≥ 7.0 (Pass)** | **Revise for Complexity** | Adjust sentence length and vocabulary for the target audience band without altering voice. |
| **Off-Target** | **< 7.0 (Fail)** | **Full Rewrite** | **Raw AI Draft:** Complete overhaul of complexity and style.<br>**Human Text:** Refactor dense sections for clarity; address style lints. |

