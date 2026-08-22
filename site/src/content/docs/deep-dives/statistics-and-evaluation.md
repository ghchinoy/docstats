---
title: Statistics & Evaluation
description: Empirical findings on in-loop generation metrics, statistical limits of pattern detection, and non-circular evaluation protocols.
sidebar:
  order: 4
---

docstats' architectural choices reflect empirical measurements from controlled benchmark studies and formal statistical methodology.

## Empirical Evaluation of In-Loop Metrics

A controlled experiment evaluated whether supplying live readability and pattern scores during text generation improves technical prose.

In controlled testing, augmenting an AI rewriter with live docstats metrics during generation yielded no measurable improvement over text-only editorial guidance ($p = 0.7253$). Both guided editorial arms outperformed the unguided control baseline ($p < 0.01$). Supplying numeric targets during drafting induced **metric gaming**, where models altered syntax to satisfy numbers rather than substance.

These findings validate the post-hoc acceptance gate architecture: authors draft against qualitative guidelines and run docstats during review.

## Statistical Limits of Pattern-Based AI Detection

Empirical evaluations demonstrate that heuristic pattern rules lack classification power for identifying AI-generated text:

- General-domain classification: **AUC = 0.577**.
- Technical-domain classification: **AUC = 0.403** (below random chance).
- In technical prose, em-dash frequency inverts: human technical authors employ em dashes as frequently as language models.

Because pattern distributions overlap heavily between human and model prose, Axis B makes no provenance claims. It functions strictly as an editorial style linter. See [House-Style Linting](/docstats/deep-dives/house-style-linting/).

## Non-Circular Evaluation Methodology

### Internal Regression Drift Anchors

The committed samples (`level_primary`, `level_middle`, `level_academic`, `level_legal`) in `samples/baseline_results.json` serve exclusively as deterministic code-drift anchors. Changes to extraction or metric computation must maintain zero drift against these baselines.

### Independent External Evaluation

Evaluating text generation quality using the generation tool's internal metrics introduces circularity. Rigorous evaluation requires independent, held-out assessment protocols:

- **Blind judging**: Candidate outputs are de-identified and randomized prior to scoring.
- **Decoupled readability grading**: A standalone Flesch-Kincaid implementation evaluates complexity independently of docstats telemetry.
- **Distribution-free statistical tests**: Non-parametric Wilcoxon signed-rank tests govern significance claims ($p < 0.05$ threshold).

docstats records telemetry across test runs without determining experimental win/loss outcomes.

## Reproducibility Standards

Every study in the research program adheres to the following criteria:

- **Blind judging**: Candidate outputs are randomized and de-identified before human or LLM judging.
- **Independent metrics**: Telemetry data is isolated from judging criteria to prevent circular scoring.
- **Distribution-free statistics**: Significance testing relies on Wilcoxon signed-rank evaluations.
- **Automated report compilation**: Tables and metrics derive directly from machine-readable `summary.json` run outputs.
- **Zero-drift validation**: Metric modifications are validated against baseline sample texts before release.

For the full study portfolio, see the [Research Program](/docstats/deep-dives/research-program/).
