---
title: Skills
description: The readability-analysis skill provides model-facing guidance for running docstats and translating metrics into editorial revisions.
sidebar:
  order: 2
---

The `readability-analysis` skill provides prompt instructions for AI coding assistants. It guides models in executing docstats tools and converting raw metrics into actionable editorial improvements.

## Skill Specifications

- Guidance on choosing among the three MCP tools, prioritizing `analyze_document`.
- Asynchronous, post-hoc review workflow steps.
- Target audience bands for Axis A and passing thresholds for Axis B.
- A combined acceptance matrix with provenance-aware revision paths.

The skill definition resides at `skills/readability-analysis/SKILL.md`, with reference examples in `skills/readability-analysis/references/score-interpretation.md`.

## Recommended Post-Hoc Workflow

The skill directs models to run docstats asynchronously after completing a draft:

1. Draft or edit text using qualitative style guidelines.
2. Invoke `analyze_document` as a verification gate.
3. If either axis flags issues, apply targeted revisions to clear diagnostic warnings.
4. Re-run docstats to confirm compliance.

This workflow enforces post-hoc evaluation. Providing live metrics during generation produces no measurable quality benefit and risks metric gaming.

## Two-Axis Scorecard Interpretation

### Axis A: Audience Target Bands

| Target Band | Consensus Grade | Reading Ease | Target Document Types |
|---|---|---|---|
| **Very Accessible** | ≤ 6 | > 70 | Tutorials, quickstarts, onboarding guides |
| **Accessible** | 7–10 | 50–70 | General developer blog posts, READMEs |
| **Dense** | 10–15 | 30–50 | Technical guides, architecture write-ups |
| **Very Dense** | 15–20 | 10–30 | Specifications, RFCs, kernel documentation |
| **Impenetrable** | > 20 | < 10 | Academic research papers, formal legal agreements |

### Axis B: House-Style Thresholds

| Metric | Passing Threshold | Description |
|---|---|---|
| `ai_tell_score` | ≥ 7.0 / 10.0 | Minimum passing score across editorial rules. |
| `em_dash_count` | ≤ 0.5 per 100 words | Limit rhetorical em dashes in prose. |
| `throat_clearing_count` | 0 | Remove opening preambles and announcements. |
| `binary_contrast_count` | 0 | State claims directly without "not X, it's Y" framing. |
| `adverb_ly_rate` | ≤ 1.5 per 100 words | Remove non-technical filler adverbs. |
| `sentence_len_cv` | Advisory (~0.20–0.40) | Sentence length variation indicator. |
| `flags` | Empty list | Resolve all returned diagnostic items. |

:::caution
`sentence_len_cv` serves as an advisory rhythm indicator. The skill instructs models to avoid targeting explicit CV numbers in generative prompts, which empirical research shows degrades natural sentence variation.
:::

## Provenance-Aware Acceptance Verdicts

The skill combines audience fit and house-style compliance, adapting recommended actions based on authorial provenance:

| Axis A (Audience Fit) | Axis B (Style Score) | Verdict | Provenance-Aware Guidance |
|---|---|---|---|
| **In Band** | **≥ 7.0 (Pass)** | **Ship** | Publication ready. |
| **In Band** | **< 7.0 (Fail)** | **Revise for Voice** | Raw AI drafts: Restructure sentences to eliminate synthetic tropes. Human-authored text: Address specific diagnostic flags while preserving authorial voice. |
| **Off-Target** | **≥ 7.0 (Pass)** | **Revise for Complexity** | Adjust sentence length and vocabulary for the target band without altering voice. |
| **Off-Target** | **< 7.0 (Fail)** | **Full Rewrite** | Raw AI drafts: Overhaul complexity and style. Human-authored text: Decompose dense sections and address style lints. |

## Related References

- [House-Style Linting](/docstats/deep-dives/house-style-linting/): The ten editorial rules and `ai_tell_score` computation.
- [MCP & Agent Plugins](/docstats/integrations/mcp/): Tool definitions and registration instructions.
