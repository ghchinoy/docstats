---
title: Skills
description: The readability-analysis skill turns raw docstats metrics into actionable editorial guidance, with a recommended post-hoc workflow and a provenance-aware verdict matrix.
sidebar:
  order: 2
---

The `readability-analysis` skill is the model-facing companion to the [MCP tools](/docstats/integrations/mcp/). It tells an AI assistant *how* to run docstats and *how* to interpret the results, converting raw statistical metrics into concrete editorial guidance.

## What the skill provides

- A description of the three MCP tools and when to prefer `analyze_document`.
- The recommended post-hoc acceptance-gate workflow.
- The audience-target bands for Axis A and the passing thresholds for Axis B.
- A combined verdict matrix that adapts guidance to document provenance.

The skill is backed by the docstats multi-protocol engine. It lives at `skills/readability-analysis/SKILL.md`, with worked examples in `skills/readability-analysis/references/score-interpretation.md`.

## Recommended workflow

The skill instructs the model to use docstats **asynchronously**, after drafting:

1. Generate or edit the draft using qualitative editorial guidelines.
2. Run `analyze_document` as a quality gate.
3. If Axis A or Axis B fails, apply targeted edits to resolve the diagnostic flags.
4. Re-run to confirm.

This mirrors the gate-not-a-dial design: injecting live metrics during generation does not improve quality and risks metric gaming.

## Interpreting the two-axis scorecard

### Axis A: audience-target bands

| Target band | Consensus grade | Reading ease | Recommended document types |
|---|---|---|---|
| **Very accessible** | ≤ 6 | > 70 | Beginner tutorials, onboarding guides |
| **Accessible** | 7–10 | 50–70 | General developer blog posts, READMEs |
| **Dense** | 10–15 | 30–50 | Deep technical guides, architecture write-ups |
| **Very dense** | 15–20 | 10–30 | Formal specifications, RFCs, kernel docs |
| **Impenetrable** | > 20 | < 10 | Academic papers, dense legal agreements |

### Axis B: house-style thresholds

| Metric | Passing threshold |
|---|---|
| `ai_tell_score` | ≥ 7.0 / 10.0 (the floor) |
| `em_dash_count` | ≤ 0.5 per 100 words in prose |
| `throat_clearing_count` | 0 |
| `binary_contrast_count` | 0 |
| `adverb_ly_rate` | ≤ 1.5 per 100 words |
| `sentence_len_cv` | advisory hint only (~0.20–0.40) |
| `flags` | empty list |

:::caution
`sentence_len_cv` is an advisory rhythm indicator. The skill explicitly warns models **not** to enforce a strict numeric CV target in generation prompts — research shows this degrades natural sentence-rhythm variation.
:::

## Provenance-aware verdict matrix

The skill combines audience fit and house-style compliance, adapting guidance to whether the text is a raw AI draft or human-authored:

| Axis A (audience fit) | Axis B (style score) | Verdict | Provenance-aware guidance |
|---|---|---|---|
| **In band** | **≥ 7.0 (pass)** | **Ship** | Ready to publish; well-calibrated and authentic. |
| **In band** | **< 7.0 (fail)** | **Revise for Voice** | Raw AI draft: aggressively restructure to remove synthetic tropes. Human text: light-touch linting on specific flags; preserve voice. |
| **Off-target** | **≥ 7.0 (pass)** | **Revise for Complexity** | Adjust sentence length and vocabulary for the target band without altering voice. |
| **Off-target** | **< 7.0 (fail)** | **Full Rewrite** | Raw AI draft: complete overhaul. Human text: refactor dense sections; address style lints. |

## Related

- [House-Style Linting](/docstats/deep-dives/house-style-linting/) — the ten rules and how `ai_tell_score` is computed.
- [MCP & Agent Plugins](/docstats/integrations/mcp/) — the tools the skill calls.
