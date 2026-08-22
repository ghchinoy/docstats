---
title: House-Style Linting
description: Deterministic editorial pattern checking in Axis B, including the ten rules, AIPatternScoresModel schema, and ai_tell_score calculations.
sidebar:
  order: 2
---

Axis B enforces crisp, direct technical prose through deterministic pattern checks. It provides house-style linting rather than statistical AI detection. This reference details the underlying rules, the data model, and score calculation mechanics.

## Deterministic House-Style Linting

In benchmark evaluations, heuristic pattern rules demonstrated limited classification power for detecting synthetic origin (**AUC = 0.577 general, AUC = 0.403 technical**). In technical writing, em-dash usage inverts: human technical authors employ em dashes as frequently as language models. Axis B makes no provenance determination; it enforces direct technical house style across all prose.

## Rule Classification

The ten rules originated in the `technical-post-editorial` skill. Machine-detectable rules feed Axis B automated checks; human-only dimensions rely on editorial review.

| # | Rule | Verification Method | Axis B Signal | Notes / Exceptions |
|---|---|---|---|---|
| 1 | No em dashes in prose | Automated | `em_dash_count` | Excludes code spans and tables; allows markdown list separators. |
| 2 | Active voice, named actors | Human-assisted | `passive_hint_count` (weak) | Passive detection is heuristic; false agency requires human judgment. |
| 3 | No filler adverbs | Automated | `adverb_ly_rate` | Excludes technical allowlist (atomically, synchronously, recursively, etc.). |
| 4 | No throat-clearing openers | Automated | `throat_clearing_count` | Phrase matching: "Here's the thing", "It's worth noting", "It turns out". |
| 5 | No binary contrast framing | Automated | `binary_contrast_count` | Pattern matching: "not X, it's Y", "isn't … it's", "not only … but". |
| 6 | No staccato fragmentation | Automated (heuristic) | `fragment_count` | Flags verbless sentence fragments as advisory hints. |
| 7 | No Wh- sentence starters | Automated | `wh_starter_rate` | Sentence-initial What, When, Where, Which, Who, Why, How. |
| 8 | Vary sentence rhythm | Automated (advisory) | `sentence_len_cv`, `list_of_three_count` | Advisory hint. Prompting models with hard CV targets degrades rhythm variance. |
| 9 | No vague declaratives | Automated (heuristic) | `vague_declarative_count` | Flags announcement phrasing ("The implications are significant"). |
| 10 | Trust the reader | Human judgment | None | Evaluates permission-granting, hand-holding, and meta-commentary. |

## Pattern Scores Model

Axis B executes through the shared analysis engine alongside Axis A:

| Field | Type | Description |
|---|---|---|
| `em_dash_count` | int | Em dashes in prose (excludes code blocks and tables). |
| `adverb_ly_rate` | float | Non-technical -ly adverbs per 100 words. |
| `throat_clearing_count` | int | Matched opening preamble phrases. |
| `binary_contrast_count` | int | Matched binary contrast frames. |
| `wh_starter_rate` | float | Wh- sentence openings per 100 sentences. |
| `fragment_count` | int | Heuristic sentence fragment count. |
| `list_of_three_count` | int | Three-item parallel lists in prose. |
| `sentence_len_cv` | float | Coefficient of variation of sentence length (advisory). |
| `vague_declarative_count` | int | Vague significance announcements. |
| `passive_hint_count` | int | Heuristic passive-voice occurrences. |
| `total_tells` | int | Total high-confidence tell count. |
| `ai_tell_score` | float | Aggregate style conformity score (0–10 scale, 10 = clean). |
| `confidence` | str | Evaluation confidence ("high" or "low" for word_count < 100). |

Detectors execute on extracted prose only. Code blocks, inline code spans, and table cells are stripped beforehand.

## Style Conformity Score Computation

`ai_tell_score` maps to a 0–10 scale, where 10 represents clean prose without style violations. It penalizes normalized rates according to confidence tiers:

- **High-confidence patterns** (rules 1, 3, 4, 5, 7): Full penalty weight.
- **Heuristic patterns** (rules 6, 9) and **passive hints**: Reduced penalty weight.
- **Rhythm metrics** (`sentence_len_cv`): Evaluated as advisory indicators without penalties.

**Passing threshold: `ai_tell_score >= 7.0`**

### Axis B Verdict Thresholds

- **Pass**: `ai_tell_score >= 7.0` with no single high-confidence category elevated.
- **Warn**: `ai_tell_score` between 5.0 and 6.9, or one elevated high-confidence category.
- **Fail**: `ai_tell_score < 5.0`, or multiple elevated high-confidence categories.

## Editorial Override Protocol

Human reviewers may retain flagged patterns when context justifies the device (such as an intentional contrast or technical emphasis). The scorecard records overrides with an explicit rationale, preserving auditability while respecting editorial discretion.

## Rhythm Variance Guidelines

`sentence_len_cv` measures sentence length variation. Low coefficient of variation values indicate potential monotone pacing. Research (experiment E4 in the [research program](/docstats/deep-dives/research-program/)) demonstrated that prompting language models with hard CV targets degrades natural sentence variation. Use CV exclusively as an advisory diagnostic.
