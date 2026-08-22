---
title: House-Style Linting
description: A deep dive into Axis B — the ten editorial rules, which are machine-detectable versus human-only, the AIPatternScoresModel field shapes, and how the ai_tell_score is computed.
sidebar:
  order: 2
---

Axis B enforces crisp, direct technical prose through deterministic pattern checks. It is a **house-style linter, not a statistical AI detector**. This page covers the rules, the model that carries them, and the score they roll up into.

## Deterministic linting, not AI detection

It is tempting to read Axis B as an "AI writing detector." It is not, and it does not claim to be.

Benchmark evaluations show heuristic pattern rules have low classification power for detecting synthetic origin: **AUC = 0.577 general, AUC = 0.403 technical**. In technical writing the em-dash correlation even *inverts* — human technical authors use em dashes at least as much as models do. Axis B therefore makes no provenance claim. It enforces a clean, direct house style regardless of who or what wrote the text.

## The ten rules

The rules originate in the `technical-post-editorial` skill. They split by whether a detector can reliably flag them: machine-detectable rules feed Axis B; human-only rules stay with editorial judgment.

| # | Rule | Detectability | Axis B signal | Notes / exceptions |
|---|---|---|---|---|
| 1 | No em dashes in prose | Machine | `em_dash_count` | Excludes code spans and tables; markdown list separators allowed. |
| 2 | Active voice, named actors | Human-assisted | `passive_hint_count` (weak) | Passive detection is heuristic; false agency needs judgment. |
| 3 | No filler adverbs | Machine | `adverb_ly_rate` | Subtracts a technical-adverb allowlist (atomically, synchronously, recursively, …). |
| 4 | No throat-clearing openers | Machine | `throat_clearing_count` | Phrase list: "Here's the thing", "It's worth noting", "It turns out", … |
| 5 | No binary contrasts as frame | Machine | `binary_contrast_count` | "not X, it's Y", "isn't … it's", "not only … but". |
| 6 | No staccato fragmentation | Machine (heuristic) | `fragment_count` | Very short verbless sentences; noisy, reported as a hint. |
| 7 | No Wh- sentence starters | Machine | `wh_starter_rate` | Sentence-initial What/When/Where/Which/Who/Why/How. |
| 8 | Vary rhythm | Machine (advisory) | `sentence_len_cv`, `list_of_three_count` | **Advisory hint only.** Prompting models with hard CV targets degrades rhythm variance. |
| 9 | No vague declaratives | Machine (heuristic) | `vague_declarative_count` | "The implications are significant", "This is the single decision that …". |
| 10 | Trust the reader | Human | none | Hand-holding and permission-granting; needs judgment. |

## The AIPatternScoresModel

Axis B is served through the same async funnel as Axis A, so REST, MCP, and CLI all expose both. Its fields:

| Field | Type | Meaning |
|---|---|---|
| `em_dash_count` | int | Em dashes in prose (code/tables excluded). |
| `adverb_ly_rate` | float | -ly adverbs per 100 words, allowlist removed. |
| `throat_clearing_count` | int | Throat-clearing openers matched. |
| `binary_contrast_count` | int | "not X, it's Y" style frames. |
| `wh_starter_rate` | float | Wh- sentence starts per 100 sentences. |
| `fragment_count` | int | Heuristic sentence fragments (hint). |
| `list_of_three_count` | int | Three-item parallel lists in prose. |
| `sentence_len_cv` | float | Coefficient of variation of sentence length (advisory rhythm hint). |
| `vague_declarative_count` | int | Significance-announcing sentences (hint). |
| `passive_hint_count` | int | Heuristic passive-voice hits (weak, advisory). |
| `total_tells` | int | Sum of high-confidence tell counts. |
| `ai_tell_score` | float | Rolled-up 0–10 style-conformity score (10 = clean). |
| `confidence` | str | "high" / "low" (low when word_count < 100). |

Detectors run on extracted prose only. Code blocks, inline code, and table cells are stripped first, so the technical exceptions hold automatically.

## How `ai_tell_score` is computed

`ai_tell_score` is a 0–10 scale where 10 means clean prose with no tells. It penalizes normalized tell rates with weighting by confidence:

- **High-confidence tells** (rules 1, 3, 4, 5, 7) carry full weight.
- **Heuristic tells** (rules 6, 9) and the **weak passive hint** carry reduced weight.
- **Rhythm** (`sentence_len_cv`) is treated as an advisory indicator, not a penalty.

**Floor: `ai_tell_score >= 7.0` to pass.**

### Axis B verdict

- **Pass** — `ai_tell_score >= 7.0` and no single high-confidence tell count is egregious.
- **Warn** — 5.0 to 6.9, or one high-confidence category elevated.
- **Fail** — below 5.0, or multiple high-confidence categories elevated.

## The Core Tension override

A human reviewer may keep a flagged device when it earns its place. The scorecard records the override with a one-line justification, so the count is explained rather than silently suppressed. Determinism gates; judgment gets the final word.

## The rhythm trap

`sentence_len_cv` measures how much sentence length varies. A low CV can signal monotone pacing — but it is strictly advisory. Research (experiment E4 in the [research program](/docstats/deep-dives/research-program/)) shows that prompting a model with a hard CV target *degrades* natural rhythm variance. Report it as a hint; never enforce it as a number.
