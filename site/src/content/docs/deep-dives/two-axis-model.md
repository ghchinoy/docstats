---
title: The Two-Axis Model
description: Architectural rationale for maintaining separate readability and house-style evaluation axes, golden-set calibration, and the combined acceptance matrix.
sidebar:
  order: 3
---

docstats evaluates documents along two independent axes without combining them into a single aggregate score.

## Orthogonal Evaluation Dimensions

High-quality technical documentation satisfies two independent criteria:

- **Readability (Axis A)**: Calibrates text complexity to target audience reading levels using standardized statistical formulas.
- **House-Style Conformity (Axis B)**: Enforces direct, concise technical writing rules (eliminating throat-clearing preambles, binary contrast frames, non-technical adverbs, and rhetorical em dashes).

These dimensions are orthogonal. Text can achieve high reading ease while violating house style conventions. Conversely, text can strictly adhere to house style while exceeding the audience's reading comprehension level.

## Independence of Scores

Combining readability metrics with editorial lint scores creates ambiguity: a composite score obscures whether a document suffers from excessive vocabulary complexity or stylistic violations. docstats evaluates both dimensions independently, requiring passing marks on both axes before publication.

## Golden Set Band Calibration

Audience target bands are anchored against docstats' committed baseline (`samples/baseline_results.json`):

| Golden Set Sample | Reading Ease | FK Grade | Consensus `text_standard` |
|---|---|---|---|
| `level_primary` | 106.9 | -0.08 | -1.0 |
| `level_middle` | 35.3 | 12.56 | 15.0 |
| `level_academic` | -29.8 | 22.38 | 23.0 |
| `level_legal` | 13.95 | 20.34 | 25.0 |

The sample names represent relative complexity rather than direct grade school equivalencies (`level_middle` anchors at grades 12–15).

| Band | FK Grade | Reading Ease | Golden Set Anchor | Target Use Case |
|---|---|---|---|---|
| Very Accessible | < 6 | > 70 | `level_primary` | Onboarding materials, beginner tutorials |
| Accessible | 6–10 | 50–70 | Calibrated target | General developer blogs, READMEs |
| Dense | 10–16 | 30–50 | `level_middle` | In-depth technical guides, architecture write-ups |
| Very Dense | 16–22 | 10–30 | `level_legal` | Specifications, RFCs, kernel documentation |
| Impenetrable | > 22 | < 10 | `level_academic` | Academic papers, formal legal text |

### Axis A Verdict Criteria

- **Pass**: Consensus grade falls within the target band for the declared document type.
- **Warn**: Consensus grade is one band away from the target band.
- **Fail**: Consensus grade is two or more bands away from target, or falls in "Impenetrable" for general documentation.

For passages under 100 words, formula reliability degrades; docstats marks Axis A as low confidence without issuing binary pass/fail determinations.

## Combined Acceptance Matrix

The final recommendation surface evaluates both axes together, providing provenance-aware guidance:

| Axis A (Audience Fit) | Axis B (Style Score) | Verdict | Provenance-Aware Guidance |
|---|---|---|---|
| **Pass** | **Pass** | **Ship** | Publication ready. |
| **Pass** | **Warn / Fail** | **Revise for Voice** | Raw AI drafts: Restructure sentences to eliminate synthetic tropes. Human-authored text: Address specific diagnostic flags while preserving authorial voice. |
| **Warn / Fail** | **Pass** | **Revise for Complexity** | Adjust sentence length and vocabulary for the target band without altering voice. |
| **Fail** | **Fail** | **Full Rewrite** | Raw AI drafts: Overhaul complexity and style. Human-authored text: Decompose dense sections and address style lints. |

Publication requires passing marks on both axes.

## Metric Specifications

- Axis A formulas and linguistics: [Readability Formulas](/docstats/deep-dives/readability-formulas/).
- Axis B pattern detection: [House-Style Linting](/docstats/deep-dives/house-style-linting/).
- Empirical evaluation and experimental data: [Statistics & Evaluation](/docstats/deep-dives/statistics-and-evaluation/).
