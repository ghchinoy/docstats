---
title: Readability Formulas
description: A linguistic deep dive into the ten readability formulas docstats computes for Axis A — what each measures, its inputs, its range, and why the consensus grade is the most robust signal.
sidebar:
  order: 1
---

Axis A rests on ten well-established readability formulas plus a consensus grade. This page explains the linguistics behind each one: what textual feature it counts, what it outputs, and where it is calibrated to be trustworthy.

## The shared inputs

Almost every formula is a weighted combination of a small set of surface features:

- **Sentence length** — words per sentence. Longer sentences raise grade level across nearly all formulas.
- **Word length** — measured either in **syllables** (Flesch family, SMOG, Gunning Fog) or in **characters/letters** (Coleman-Liau, ARI). Character-based formulas avoid syllable-counting errors.
- **Word familiarity** — whether words appear on a curated list of common words (Dale-Chall, Spache).

Understanding which lever a formula pulls tells you how to move its score. If Coleman-Liau is high, shorten words. If Gunning Fog is high, cut multi-syllable jargon. If Dale-Chall is high, replace unfamiliar vocabulary.

## The ten formulas

| Metric | Output range | What it measures |
|---|---|---|
| **Flesch Reading Ease** | 0–100 (higher = easier) | Syllables per word and words per sentence. 90–100 ≈ grade 5; 60–70 plain English; < 30 academic/legal. |
| **Flesch-Kincaid Grade** | U.S. grade level | The Flesch inputs re-expressed as years of U.S. formal education. |
| **Gunning Fog Index** | U.S. grade level | Sentence length plus the proportion of "complex" words (3+ syllables). Penalizes jargon. |
| **SMOG Index** | U.S. grade level | Polysyllable count over a fixed sentence sample. The standard in health and medical writing. |
| **Coleman-Liau Index** | U.S. grade level | Letters per 100 words and sentences per 100 words. Character-based, so no syllable counting. |
| **Automated Readability Index (ARI)** | U.S. grade level | Characters per word and words per sentence. Also character-based. |
| **Linsear Write** | U.S. grade level | Developed for U.S. Air Force technical manuals; weights easy versus hard words by syllable count. |
| **Dale-Chall Score** | 0.0–10.0+ | Fraction of words *outside* a list of ~3,000 familiar words, plus sentence length. |
| **Spache Score** | Primary grade level | Familiar-word approach calibrated specifically for texts below 4th grade. |
| **Text Standard** | Consensus grade | The cross-formula consensus; the single most robust number docstats reports. |

## Why the consensus is most robust

Individual formulas disagree because they weight sentence length versus word difficulty differently. On the golden-set legal sample, Coleman-Liau reads 14.7 while Linsear Write reads 25.0 — the same text, a ten-grade spread. Reporting any single formula in isolation invites cherry-picking.

`text_standard` aggregates across the formulas, which smooths out the idiosyncrasies of any one. Report it first, then explain notable outliers.

## Two linguistic caveats

### Reading ease runs backwards

`flesch_reading_ease` is the only headline metric where **higher is easier**. Everything else is a grade level where higher is harder. The golden-set primary sample scores ~107 on ease while its grade level is negative; the academic sample scores negative on ease while its grade is 22+. Always state the direction.

### Below ~100 words, trust nothing precisely

Every formula assumes a sample large enough for its ratios to stabilize. Under ~100 words the estimates get noisy, and Spache — which needs a minimum sample — can return `null`. docstats flags this as low confidence rather than pretending the number is precise. See [Troubleshooting](/docstats/guides/troubleshooting/).

## Reading the raw statistics

`word_count`, `sentence_count`, and `syllable_count` explain *why* a score landed where it did:

- **Long sentences inflate grade level.** The golden-set legal sample averages ~36 words per sentence (109 words across 3 sentences); splitting sentences is usually the fastest way to lower the grade.
- **Syllable density drives the Flesch family and SMOG.** The academic sample packs 358 syllables into 140 words (~2.56 syllables/word); swapping multi-syllable jargon for plain words lowers these fast.

For how these numbers map to audience decisions, see [Interpreting Scores](/docstats/guides/interpreting-scores/).
