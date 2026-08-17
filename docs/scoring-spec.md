# Scoring Spec: Two-Axis Assessment for AI-Assisted Technical Writing

Status: Phase 0 (spec). No code changes implied by this document.
Scope: defines the target model for combining docstats definitive metrics with
the `technical-post-editorial` skill so drafts can be evaluated, assessed, and
given actionable revision guidance.

## 1. Purpose and principle

A good technical document must satisfy two independent requirements:

- **Readability (Axis A)** — is the prose pitched at the right reading level for its
  target audience? (formulaic, objective; docstats computes this via standard formulas)
- **House-Style Conformity (Axis B)** — does the prose adhere to crisp, direct technical
  editorial standards without throat-clearing, binary contrast framing, non-technical
  adverbs, or excessive rhetorical punctuation?

> **Design Role:** `docstats` is positioned as a **post-hoc acceptance gate** (for CI/CD
> pipelines, PR reviews, and pre-publish QA) rather than an in-loop generative dial.
> Empirical evaluations show that injecting live numeric metrics during generation does not
> improve prose quality over clear textual guidance ($p = 0.7253$) and risks artificial
> metric gaming.

> **Empirical Context on Axis B:** Axis B patterns are **deterministic house-style linting checks**,
> not a statistical AI detector. Benchmark evaluations show that heuristic pattern rules have
> low classification power for detecting synthetic origin (AUC = 0.577 general, AUC = 0.403
> technical; em-dash correlation even inverts in technical writing). Axis B enforces clean,
> direct technical house style regardless of author provenance.

These axes are orthogonal. Text can be easy to read and still violate house style; text can be
lint-clean and pitched at the wrong grade level. We therefore report a **two-axis scorecard
with no blended headline number**. A draft passes only when both axes pass.

## 2. The two axes

### Axis A — Readability (existing docstats output)

Source: `ReadabilityScoresModel` (`models.py:49-63`), computed by
`calculate_readability_metrics_logic` (`metrics.py:99`). Thirteen fields:
ten readability scores, a consensus `text_standard`, and three raw counts.

Axis A is interpreted as an **audience-fit band**, not a pass/fail on any
single formula. The primary signals are `flesch_kincaid_grade`,
`flesch_reading_ease`, and `text_standard` (the cross-formula consensus grade).
Secondary signals (`gunning_fog`, `smog_index`, `coleman_liau_index`, etc.)
corroborate and are used for drift detection, not gating.

### Axis B — House-Style Pattern Density

Source: `AIPatternScoresModel`, served alongside Axis A through the same
async funnel so REST, MCP, and CLI all expose both. Axis B turns the
machine-detectable subset of editorial rules into counts, rates, diagnostic flags,
and a rolled-up 0-10 style conformity score.

## 3. Readability bands (Axis A targets)

Bands are calibrated against the committed Golden Set baseline
(`samples/baseline_results.json`), which anchors the four reference levels:

| Golden Set sample | flesch_reading_ease | flesch_kincaid_grade | text_standard |
|---|---|---|---|
| level_primary | 106.9 | -0.08 | -1.0 |
| level_middle | 35.3 | 12.56 | 15.0 |
| level_academic | -29.8 | 22.38 | 23.0 |
| level_legal | 13.95 | 20.34 | 25.0 |

Observation: `level_middle` already scores at grade ~12-15, so the sample
names describe *relative* complexity, not literal US school grades. Bands
below are expressed in Flesch-Kincaid grade and Flesch Reading Ease and tuned
so each Golden Set sample lands in a distinct band. Per the Phase 0 decision,
bands are tuned across all four levels equally before any per-doc-type
specialization.

| Band | FK grade | Flesch Reading Ease | Golden Set anchor | Intended use |
|---|---|---|---|---|
| Very accessible | < 6 | > 70 | level_primary | Onboarding, tutorials for beginners |
| Accessible | 6 - 10 | 50 - 70 | (target zone for dev blogs) | General developer-facing posts |
| Dense | 10 - 16 | 30 - 50 | level_middle | Advanced/architecture write-ups |
| Very dense | 16 - 22 | 10 - 30 | level_legal | Specs, reference, legal |
| Impenetrable | > 22 | < 10 | level_academic | Flag for revision unless intentional |

Default target for the primary calibration set: a general developer post
should land in **Accessible to Dense** (FK grade 6-16, Reading Ease 30-70).
Landing in "Impenetrable" is an Axis A failure unless the document type
explicitly allows it (spec/legal/academic).

Axis A verdict:
- **Pass** — consensus grade falls inside the target band for the declared
  document type.
- **Warn** — one band away from target.
- **Fail** — two or more bands away, or in "Impenetrable" for a doc type that
  should be accessible.

Guardrail: `word_count < 100` degrades formula reliability (`metrics.py:62`)
and makes `spache` uncomputable (`metrics.py:65-80`). Under 100 words, Axis A
is reported as **low-confidence** rather than pass/fail.

## 4. Skill-rule classification (machine-detectable vs human-only)

The ten rules in `technical-post-editorial/SKILL.md` split by whether a
detector can reliably flag them. Machine-detectable rules feed Axis B;
human-only rules stay with the skill's judgment and the Core Tension test.

| # | Rule | Detectability | Axis B signal | Notes / exceptions |
|---|---|---|---|---|
| 1 | No em dashes in prose | Machine | `em_dash_count` | Exclude code spans and tables; markdown list separators allowed |
| 2 | Active voice, named actors | Human-assisted | `passive_hint_count` (weak) | Passive detection is heuristic; false-agency needs judgment |
| 3 | No adverbs | Machine | `adverb_ly_rate` | Subtract technical-adverb allowlist (atomically, synchronously, recursively, ...) |
| 4 | No throat-clearing openers | Machine | `throat_clearing_count` | Phrase list: "Here's the thing", "It's worth noting", "It turns out", ... |
| 5 | No binary contrasts as frame | Machine | `binary_contrast_count` | Patterns: "not X, it's Y", "isn't ... it's", "not only ... but" |
| 6 | No staccato fragmentation | Machine (heuristic) | `fragment_count` | Very short verbless sentences; noisy, report as hint |
| 7 | No Wh- sentence starters | Machine | `wh_starter_rate` | Sentence-initial What/When/Where/Which/Who/Why/How |
| 8 | Vary rhythm | Machine (advisory) | `sentence_len_cv`, `list_of_three_count` | **Advisory hint only.** Research (E4) shows prompting models with hard CV targets degrades rhythm variance. |
| 9 | No vague declaratives | Machine (heuristic) | `vague_declarative_count` | "The implications are significant", "This is the single decision that ..." |
| 10 | Trust the reader | Human | none | Hand-holding/permission-granting; needs judgment |

Rubric dimensions map to Axis B signals as follows:

| Rubric dimension | Grounded in Axis B signal(s) | Scored by |
|---|---|---|
| Directness | throat_clearing_count, vague_declarative_count, binary_contrast_count | Axis B (objective floor) |
| Rhythm | sentence_len_cv (advisory), list_of_three_count | Axis B (advisory hint) / Human |
| Density | words/sentence, total cuttable-pattern count | Axis B (objective floor) |
| Authenticity | none | Human only |
| Trust | passive_hint_count (weak) | Human primary |

## 5. AIPatternScoresModel (field shapes)

Pydantic model sitting beside `ReadabilityScoresModel`:

| Field | Type | Meaning |
|---|---|---|
| `em_dash_count` | int | Em dashes in prose (code/tables excluded) |
| `adverb_ly_rate` | float | -ly adverbs per 100 words, allowlist removed |
| `throat_clearing_count` | int | Throat-clearing openers matched |
| `binary_contrast_count` | int | "not X, it's Y" style frames |
| `wh_starter_rate` | float | Wh- sentence starts per 100 sentences |
| `fragment_count` | int | Heuristic sentence fragments (hint) |
| `list_of_three_count` | int | Three-item parallel lists in prose |
| `sentence_len_cv` | float | Coefficient of variation of sentence length (advisory rhythm hint) |
| `vague_declarative_count` | int | Significance-announcing sentences (hint) |
| `passive_hint_count` | int | Heuristic passive-voice hits (weak, advisory) |
| `total_tells` | int | Sum of high-confidence tell counts |
| `ai_tell_score` | float | Rolled-up 0-10 style conformity score (10 = clean); see Section 6 |
| `confidence` | str | "high" / "low" (low when word_count < 100) |

Detectors run on extracted prose only. Code blocks, inline code, and table
cells are stripped before detection so the technical exceptions in
`SKILL.md` hold automatically.

## 6. Axis B score and floor

`ai_tell_score` is a 0-10 scale (10 = clean prose, no tells). It is computed
by penalizing normalized tell rates. High-confidence tells (rules 1, 3, 4, 5,
7) carry full weight; heuristic tells (rules 6, 9) and the weak passive hint
carry reduced weight; rhythm (`sentence_len_cv`) is treated as an advisory indicator.

Floor: `ai_tell_score >= 7.0` to pass.

Axis B verdict:
- **Pass** — `ai_tell_score >= 7.0` and no single high-confidence tell count
  is egregious.
- **Warn** — 5.0 to 6.9, or one high-confidence category elevated.
- **Fail** — below 5.0, or multiple high-confidence categories elevated.

The Core Tension override still applies: a human reviewer may keep a flagged
device when it earns its place. The scorecard records the override with a
one-line justification so the count is explained, not silently suppressed.

## 7. The two-axis scorecard & Combined Verdict Matrix

The recommendation surface reports both axes and a combined verdict. Example:

```
DOCUMENT: migration-guide.md   (declared type: developer blog)

Axis A  Readability
  text_standard (consensus): grade 11    band: Dense       -> target Accessible-Dense  [PASS]
  flesch_reading_ease: 42.3   flesch_kincaid_grade: 11.2   word_count: 1840

Axis B  House-Style Conformity
  ai_tell_score: 6.4 / 10                                                            [WARN]
  em dashes in prose: 3   throat-clearing: 2   binary contrasts: 4   Wh- starts: high
  adverb rate: 3.1/100w   sentence-length CV: 0.18 (advisory rhythm hint)

VERDICT: REVISE
  Axis A acceptable. Axis B below floor (6.4 < 7.0): remove 3 em dashes,
  cut 2 throat-clearing openers, rewrite 4 binary-contrast frames.
```

### Combined Verdict Matrix & Provenance-Aware Guidance

| Axis A (Audience Fit) | Axis B (Style Score) | Verdict | Provenance-Aware Action |
|---|---|---|---|
| **Pass** | **Pass** | **Ship** | Ready to publish. |
| **Pass** | **Warn / Fail** | **Revise for Voice** | **Raw AI Draft:** Aggressively restructure to remove synthetic tropes.<br>**Human Text:** Apply light-touch linting for specific diagnostic flags; preserve authorial voice. |
| **Warn / Fail** | **Pass** | **Revise for Complexity** | Adjust sentence length / vocabulary for target audience without altering voice. |
| **Fail** | **Fail** | **Full Rewrite** | **Raw AI Draft:** Overhaul complexity and style.<br>**Human Text:** Refactor dense sections for clarity; address style lints. |

A draft ships only when both axes pass. No blended headline number is emitted.

## 8. Integration target (MCP)

The `technical-post-editorial` skill pulls Axis A and Axis B from the
`readability_docstats` MCP tool during review. The skill consumes the two models,
applies the human-only dimensions and the Core Tension override, and renders the
scorecard in Section 7 as a post-hoc acceptance check.

## 9. Calibration, Drift, and Evaluation Standards

### Internal Drift Anchors vs External Evaluation Standards
To maintain methodological and scientific integrity, docstats strictly separates
internal regression calibration from external performance evaluation:

1. **Internal Regression Drift Anchors (The Golden Set):**
   - The four committed reference samples in `samples/baseline_results.json` (`level_primary.txt`, `level_middle.txt`, `level_academic.txt`, `level_legal.txt`) serve strictly as deterministic code-drift anchors.
   - Any refactoring of `extraction.py` or `metrics.py` must maintain exact zero-drift against these anchors.
2. **Independent Non-Circular External Evaluation Standards:**
   - External validation of editorial rewriters or LLM outputs **must never use docstats' internal scoring as the sole arbiter of quality** (which would be circular).
   - Valid evaluations must employ independent held-out metrics (e.g. decoupled FK grading, blind multi-judge human or LLM scoring, paired Wilcoxon signed-rank significance testing).

## 10. Open items for later phases

- Phase 1: implement `AIPatternScoresModel` + detectors; wire through
  `metrics.py`, `fastapi_app.py`, `mcp_server.py`. (Completed)
- Phase 2: add AI-slop fixtures + expected-findings JSON; automate the
  two-axis regression baseline (`docstats-ysq`).
- Phase 3: update the skill to consume both models and render the scorecard;
  wire the MCP call (`docstats-561`).

