# Empirical Evaluation Report: Formal Stats vs Text Guidance

**Run Identifier:** `20260816_170512`
**Model:** `gemini-3.7-flash`
**Evaluation Date:** `2026-08-16T17:12:29.629532+00:00`
**Corpus Size:** 14 document(s)

---

## 1. Executive Summary & Verdict

⚖️ **NEUTRAL / INCONCLUSIVE**

Performance between Text-Only (Arm B) and Stats-Augmented (Arm C) was statistically comparable (overall delta: +0.00).

### Key Aggregate Metrics:
- **Win Rates:**
  - control: **0.0%**
  - stats_augmented: **50.0%**
  - text_only_rewriter1: **50.0%**
  - text_only_rewriter2: **0.0%**
- **Overall Quality Delta (Stats vs Reference):** **+0.00 / 10**

---

## 2. Experimental Premise & Research Question

Technical writing produced or revised by Large Language Models often exhibits synthetic stylistic tropes: throat-clearing openers, binary contrast frames ("not X, it's Y"), metronomic sentence structures, and unearned rhetorical markers.

The `technical-post-editorial` framework establishes rule-based guidance to counteract these patterns. This experiment evaluates whether **coupling this guidance with live, multi-protocol statistical feedback (docstats MCP `analyze_document`)** yields superior outcomes compared to providing text rules alone.

### Experimental Conditions:
1. **Arm A (Control):** Standard LLM polish without specific constraints.
2. **Arm B1 (Text-Only Rewriter 1):** Guided by `technical-post-editorial` rules.
3. **Arm B2 (Text-Only Rewriter 2):** Alternate rewriter with editorial rules.
4. **Arm C (Stats-Augmented):** Guided by rules + live docstats MCP feedback.

---

## 3. Methodology & Independence Guarantees

- **Blind LLM Judge:** Candidate revisions were anonymized, randomized (`Candidate 1, 2, ...`), and evaluated by an independent judge model instance with no awareness of arm assignment.
- **Multi-Dimensional Criteria:** Candidates were evaluated across Directness, Rhythm, Voice Authenticity, Density, Technical Integrity, and Overall Quality.
- **Held-Out Telemetry & Movement:** Pre-rewrite baselines and post-rewrite readability / pattern scores were independently measured across all arms.

---

## 4. Empirical Data & Statistical Breakdown

### Dimension Performance (1–10 Scale)

| Dimension | Control | Stats Augmented | Text Only Rewriter1 | Text Only Rewriter2 | Delta (Stats vs Primary Text) |
| --- | --- | --- | --- | --- | --- |
| **Overall Score** | 7.44 | 8.79 | 8.99 | 7.14 | -0.20 |
| **Directness** | 7.11 | 8.82 | 9.14 | 8.00 | -0.32 |
| **Rhythm** | 7.57 | 8.75 | 8.71 | 6.00 | +0.04 |
| **Authenticity** | 7.29 | 9.18 | 8.96 | 6.89 | +0.22 |
| **Density** | 7.18 | 8.82 | 9.14 | 7.75 | -0.32 |
| **Technical Integrity** | 8.39 | 8.75 | 9.00 | 8.11 | -0.25 |


### Objective Pre -> Post Movement

| Arm | Δ AI Tell Score | Δ FK Grade | Δ Total Tells |
|---|---|---|---|
| **control** | +0.58 | +1.45 | -2.2 |
| **stats_augmented** | +0.88 | +1.56 | -2.4 |
| **text_only_rewriter1** | +0.91 | +0.76 | -2.4 |
| **text_only_rewriter2** | +0.93 | -0.19 | -2.4 |

---

## 5. Document-by-Document Evaluations

### Document: `01-rest-to-grpc-g25`

- **Blind Rankings:** Candidate 3, Candidate 4, Candidate 2, Candidate 1
- **Overall Scores:** control: `6.5` | stats_augmented: `9.7` | text_only_rewriter1: `8.9` | text_only_rewriter2: `7.0`
- **Judge Rationale:** Candidate 3 wins by a wide margin because it reads exactly like a real internal engineering wiki. By injecting practical, real-world implementation details (schema registries, keepalives, explicit error handling), it respects the target audience's expertise and provides actionable technical guidance.

### Document: `01-rest-to-grpc-g37`

- **Blind Rankings:** Candidate 1, Candidate 3, Candidate 2, Candidate 4
- **Overall Scores:** control: `7.5` | stats_augmented: `9.0` | text_only_rewriter1: `8.2` | text_only_rewriter2: `7.8`
- **Judge Rationale:** Candidate 1 wins decisively by demonstrating true engineering authenticity: it catches and fixes a missing early return in the Node.js error-first callback snippet, preventing a runtime bug where an undefined response would be logged. The other candidates merely copy-pasted the flawed code.

### Document: `02-distributed-caching-g25`

- **Blind Rankings:** Candidate 2, Candidate 1, Candidate 4, Candidate 3
- **Overall Scores:** control: `7.5` | stats_augmented: `7.0` | text_only_rewriter1: `9.5` | text_only_rewriter2: `5.5`
- **Judge Rationale:** Candidate 2 wins by delivering a highly authentic, dense, and precise engineering narrative. It elevates the vocabulary with accurate terminology ('mutations', 'hot write path') without hallucinating facts, whereas Candidate 4 invents architectural details and Candidate 1 relies on generic AI tropes.

### Document: `02-distributed-caching-g37`

- **Blind Rankings:** Candidate 2, Candidate 1, Candidate 3, Candidate 4
- **Overall Scores:** control: `7.8` | stats_augmented: `7.4` | text_only_rewriter1: `9.4` | text_only_rewriter2: `7.5`
- **Judge Rationale:** Candidate 2 is the clear winner. It demonstrates superior engineering writing by front-loading the problem metric (160ms latency), stripping away marketing fluff, and enhancing technical precision (e.g., specifying 'monotonic' logical counters and 'out-of-order' writes). The formatting improvements also make it much easier to scan.

### Document: `03-async-job-queues-g25`

- **Blind Rankings:** Candidate 3, Candidate 4, Candidate 2, Candidate 1
- **Overall Scores:** control: `7.1` | stats_augmented: `9.7` | text_only_rewriter1: `8.8` | text_only_rewriter2: `7.0`
- **Judge Rationale:** Candidate 3 wins by perfectly capturing the voice of a senior systems architect. It replaces generic descriptions with concrete technical primitives (e.g., `delivery_mode=2`, `SET key NX EX 86400`, `basic.nack(requeue=false)`), drastically increasing information density and authenticity without adding fluff. Candidate 4 is a strong runner-up, offering excellent readability and directness.

### Document: `03-async-job-queues-g37`

- **Blind Rankings:** Candidate 2, Candidate 4, Candidate 1, Candidate 3
- **Overall Scores:** control: `8.4` | stats_augmented: `9.2` | text_only_rewriter1: `8.1` | text_only_rewriter2: `7.2`
- **Judge Rationale:** Candidate 2 wins decisively by demonstrating superior technical integrity. It is the only candidate to catch the contradiction between the diagram (Direct Exchange) and the text (topic exchange). Furthermore, it elevates the prose with highly authentic, precise engineering terminology ('head-of-line queue blocking', 'prefetch ceiling') while correctly fixing the original draft's misuse of the term 'starvation' in the backpressure section.

### Document: `04-index-tuning-g25`

- **Blind Rankings:** Candidate 4, Candidate 1, Candidate 3, Candidate 2
- **Overall Scores:** control: `6.5` | stats_augmented: `9.5` | text_only_rewriter1: `8.8` | text_only_rewriter2: `7.2`
- **Judge Rationale:** Candidate 4 wins by a wide margin because it understands the 'tutorial' format and the developer audience. By introducing concrete SQL examples, specific architectural details (like BRIN's 128-page default), and clear trade-offs, it sounds like an experienced database engineer. Candidate 1 is a solid runner-up for its concise, fluff-free prose, while Candidates 3 and 2 suffer from choppy rhythm and retained filler, respectively.

### Document: `04-index-tuning-g37`

- **Blind Rankings:** Candidate 3, Candidate 1, Candidate 4, Candidate 2
- **Overall Scores:** control: `8.4` | stats_augmented: `8.2` | text_only_rewriter1: `9.4` | text_only_rewriter2: `7.2`
- **Judge Rationale:** Candidate 3 wins by demonstrating deep, authentic PostgreSQL knowledge. It uses precise internal terminology and corrects a subtle technical inaccuracy in the original draft regarding BRIN clustering requirements.

### Document: `05-sample-migration`

- **Blind Rankings:** Candidate 4, Candidate 3, Candidate 2, Candidate 1
- **Overall Scores:** control: `8.6` | stats_augmented: `8.8` | text_only_rewriter1: `9.5` | text_only_rewriter2: `8.2`
- **Judge Rationale:** Candidate 4 wins by achieving the best balance of directness, high information density, and strict technical accuracy. It successfully adopts an authentic engineering voice without hallucinating new metrics or architectural details, unlike Candidate 3.

### Document: `06-sdk-pagination`

- **Blind Rankings:** Candidate 1, Candidate 3, Candidate 2, Candidate 4
- **Overall Scores:** control: `6.5` | stats_augmented: `9.2` | text_only_rewriter1: `8.2` | text_only_rewriter2: `6.0`
- **Judge Rationale:** Candidate 1 wins by significantly elevating the technical depth of the original draft. It introduces a practical code snippet and clearly explains the mechanics of lazy evaluation and cursor state, resulting in a highly authentic and dense piece of technical writing. Candidate 3 is a solid, concise alternative but lacks the illustrative code. Candidates 2 and 4 suffer from AI-like phrasing and poor rhythm, respectively.

### Document: `07-observability-slop`

- **Blind Rankings:** Candidate 1, Candidate 2, Candidate 3, Candidate 4
- **Overall Scores:** control: `7.0` | stats_augmented: `8.5` | text_only_rewriter1: `9.3` | text_only_rewriter2: `7.8`
- **Judge Rationale:** Candidate 1 wins by perfectly capturing the tone of an internal engineering RFC. It eliminates the original's fluff, gets straight to the point, and translates vague requirements into concrete, actionable technical specifications without losing the original intent.

### Document: `08-fastapi-clean`

- **Blind Rankings:** Candidate 1, Candidate 2, Candidate 3, Candidate 4
- **Overall Scores:** control: `7.2` | stats_augmented: `9.0` | text_only_rewriter1: `9.5` | text_only_rewriter2: `6.5`
- **Judge Rationale:** Candidate 1 wins by combining high information density with an authoritative, instructional tone. It replaces conversational filler with precise technical explanations and uses the lead-in to the code block to actually teach the implementation (`Depends`), whereas other candidates merely announce the example.

### Document: `09-sqlite-wal-guide`

- **Blind Rankings:** Candidate 2, Candidate 4, Candidate 1, Candidate 3
- **Overall Scores:** control: `7.9` | stats_augmented: `9.3` | text_only_rewriter1: `8.8` | text_only_rewriter2: `7.6`
- **Judge Rationale:** Candidate 2 wins by transforming the text with strong active verbs, clarifying the architectural shift ('reverses this relationship'), and introducing precise API references (`sqlite3_wal_checkpoint_v2`) that elevate the authenticity and authority of the piece.

### Document: `10-standard-readme`

- **Blind Rankings:** Candidate 4, Candidate 1, Candidate 2, Candidate 3
- **Overall Scores:** control: `7.2` | stats_augmented: `8.5` | text_only_rewriter1: `9.4` | text_only_rewriter2: `7.5`
- **Judge Rationale:** Candidate 4 wins by significantly improving the technical precision of the text (using terms like 'exported functions', 'code examples', and 'codebases') while simultaneously increasing information density. It strips away throat-clearing transitions in favor of direct, actionable statements that resonate with an engineering audience.


---

## 6. Replication Guide

To independently reproduce this evaluation run:

```bash
# 1. Sync evaluation dependencies
uv sync --group dev --group eval

# 2. Configure model credentials (Gemini Developer API or Vertex AI)
export GEMINI_API_KEY="<your-key>"

# 3. Execute experiment across corpus
uv run python eval/run_experiment.py --primary-model gemini-3.7-flash

# 4. Evaluate with blind judge and generate report
uv run python eval/judge.py --run-dir eval/results/20260816_170512
uv run python eval/analyze_results.py --run-dir eval/results/20260816_170512
uv run python eval/writeup.py --run-dir eval/results/20260816_170512
```

---
*Report automatically generated by `eval/writeup.py`.*
