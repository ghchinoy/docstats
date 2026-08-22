---
title: CI Quality Gate
description: Use docstats as a post-hoc acceptance gate in CI/CD and PR reviews, with the combined verdict matrix and golden-set zero-drift guarantees.
sidebar:
  order: 3
---

docstats is built to gate documentation, not to steer generation. This page shows how to wire it into a pipeline and how to read the pass/warn/fail verdict.

## The recommended workflow

1. Draft or edit with qualitative editorial guidelines.
2. Run docstats as an acceptance gate (in CI, a pre-commit hook, or a PR check).
3. If either axis fails, apply targeted edits to resolve the diagnostic flags.
4. Re-run to confirm the fix.

This is deliberately **post-hoc**. Injecting live metrics during generation does not improve quality (p = 0.7253) and invites metric gaming — see [Statistics & Evaluation](/docstats/deep-dives/statistics-and-evaluation/).

## The combined verdict matrix

A draft ships only when both axes pass. The action depends on which axis failed and on the document's provenance:

| Axis A (audience fit) | Axis B (style score) | Verdict | Provenance-aware action |
|---|---|---|---|
| **Pass** | **Pass** | **Ship** | Ready to publish. |
| **Pass** | **Warn / Fail** | **Revise for Voice** | Raw AI draft: aggressively restructure to remove synthetic tropes. Human text: apply light-touch linting on specific flags; preserve authorial voice. |
| **Warn / Fail** | **Pass** | **Revise for Complexity** | Adjust sentence length and vocabulary for the target audience without altering voice. |
| **Fail** | **Fail** | **Full Rewrite** | Raw AI draft: overhaul complexity and style. Human text: refactor dense sections for clarity; address style lints. |

No blended headline number is emitted. See [The Two-Axis Model](/docstats/deep-dives/two-axis-model/) for the axis-level pass/warn/fail definitions.

## Example scorecard output

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

## Golden-set benchmarking (zero drift)

The `samples/` directory holds four reference texts spanning difficulty levels (`level_primary`, `level_middle`, `level_academic`, `level_legal`). They serve as **internal drift anchors**: any change to parsing, tokenization, or a formula implementation must produce exactly zero drift against the committed baseline.

Run the baseline analyzer after changing extraction or metric code:

```bash
uv run python baseline_analysis.py
```

Compare the output against `samples/baseline_results.json`.

## Quality gates in CI

```bash
# Full test suite
uv run pytest

# Linter and formatter
uv run ruff check .
uv run ruff format --check .
```

## Anti-circularity warning

When you evaluate the quality of text an AI agent generated or edited, **do not use docstats' own scores as the sole judge** — that is circular. Rigorous evaluation uses independent, decoupled frameworks: blind human or LLM comparative judging, held-out readability grading, and non-parametric tests such as the Wilcoxon signed-rank test. docstats telemetry can be recorded for every candidate, but it must never dictate the win/loss verdict.
