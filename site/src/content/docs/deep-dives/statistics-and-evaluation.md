---
title: Statistics & Evaluation
description: The empirical evidence behind docstats' design — why live metrics don't help generation, the limits of pattern-based detection, and the non-circular evaluation standards that keep results honest.
sidebar:
  order: 4
---

docstats' design is grounded in measurement, not intuition. This page collects the empirical findings that shaped it and the statistical standards it holds itself to.

## Why docstats is a gate, not a dial

The central design choice — post-hoc gate rather than in-loop generative dial — comes from a controlled experiment.

Augmenting an AI rewriter with live, deterministic docstats metrics during generation did **not** improve technical prose over clear text-only editorial guidance. The stats-augmented arm versus the text-only editorial arm was inconclusive: **p = 0.7253**. Both editorial arms beat the no-guidance control (p < 0.01), so *editorial guidance matters* — but feeding the model live numbers on top of it added nothing measurable, and it introduces a real failure mode: **metric gaming**, where the model optimizes the visible number while the prose degrades.

The conclusion: use qualitative guidance to draft, and use docstats afterward as an acceptance check.

## The limits of pattern-based detection

Axis B is a house-style linter, and the statistics are the reason it is framed that way rather than as an AI detector.

- General-domain classification: **AUC = 0.577**.
- Technical-domain classification: **AUC = 0.403** — below chance.
- The em-dash signal, a popular "AI tell," **inverts** in technical writing: technical human authors use em dashes freely.

An AUC near 0.5 means the patterns barely separate synthetic from human text; below 0.5 in the technical domain means the naive rule points the wrong way. docstats therefore makes no provenance claim. It enforces clean, direct style regardless of authorship. See [House-Style Linting](/docstats/deep-dives/house-style-linting/).

## Non-circular evaluation standards

To keep results honest, docstats strictly separates two things that are easy to conflate.

### Internal drift anchors (the golden set)

The four committed reference samples (`level_primary`, `level_middle`, `level_academic`, `level_legal`) in `samples/baseline_results.json` are **deterministic code-drift anchors only**. Any refactor of `extraction.py` or `metrics.py` must maintain exact zero drift against them. They verify that the *code* still computes the same numbers — nothing more.

### Independent external evaluation

When judging the quality of AI-rewritten or edited text, docstats' own scoring **must never be the sole arbiter** — that would be circular. Valid evaluation uses decoupled, held-out methods:

- **Blind judging** — outputs are de-identified and randomized before scoring.
- **Held-out readability grading** — a separate FK computation, not docstats' own telemetry.
- **Distribution-free statistics** — the Wilcoxon signed-rank test (exact for small n, normal approximation with continuity correction for large n), gated at p < 0.05 for any "significant" claim.

docstats telemetry can be recorded for every candidate, but it never dictates the win/loss verdict.

## Reproducibility guarantees

Every experiment in the program upholds:

- **Blind judging** on de-identified, randomized outputs.
- **Independent held-out metrics** — docstats numbers are recorded but non-authoritative (anti-circularity).
- **Distribution-free statistics** — dependency-free Wilcoxon signed-rank testing.
- **Machine-generated tables** — every number in a report is generated from the run's `summary.json`; no hand-typed statistics.
- **Golden-set zero-drift** — metric changes are validated against the golden set before being relied upon.

For the full experiment portfolio behind these findings, see the [Research Program](/docstats/deep-dives/research-program/).
