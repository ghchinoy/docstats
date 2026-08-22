---
title: Readability Formulas
description: Linguistic foundations and mathematical mechanics of the ten readability formulas in Axis A.
sidebar:
  order: 1
---

Axis A computes ten standardized readability formulas and a consensus grade level. This reference details the linguistic features, mathematical inputs, and operational boundaries of each formula.

## Linguistic Inputs

Formulas compute weighted linear combinations of core structural and lexical features:

- **Sentence length**: Words per sentence ($W/S$). Longer sentences raise grade levels across nearly all formulas.
- **Word complexity (syllables)**: Syllables per word ($S/W$) or percentage of polysyllabic words (3+ syllables). Used in Flesch, Flesch-Kincaid, Gunning Fog, and SMOG.
- **Word complexity (characters)**: Characters or letters per 100 words ($L/100W$). Used in Coleman-Liau and ARI to eliminate syllable-counter inaccuracies.
- **Lexical familiarity**: Proportion of words outside a curated vocabulary list. Used in Dale-Chall (3,000 common words) and Spache (primary school vocabulary).

Understanding which feature a formula isolates helps guide text simplification:
- High Coleman-Liau: Shorten word lengths.
- High Gunning Fog: Replace multi-syllable jargon.
- High Dale-Chall: Swap specialized terms for familiar vocabulary.

## Formula Reference

| Metric | Output Range | Linguistic Mechanics |
|---|---|---|
| **Flesch Reading Ease** | 0–100 (Higher = Simpler) | Combines words per sentence and syllables per word. Scores of 60–70 denote plain English; scores below 30 indicate legal/academic prose. |
| **Flesch-Kincaid Grade** | U.S. Grade Level | Re-expresses Flesch inputs as formal years of U.S. schooling. |
| **Gunning Fog Index** | U.S. Grade Level | Weights average sentence length against the percentage of complex words (≥3 syllables), heavily penalizing technical jargon. |
| **SMOG Index** | U.S. Grade Level | Counts polysyllabic words across a fixed 30-sentence sample. Standard in clinical, health, and consumer disclosures. |
| **Coleman-Liau Index** | U.S. Grade Level | Computes letters per 100 words and sentences per 100 words, relying entirely on character counts. |
| **Automated Readability (ARI)** | U.S. Grade Level | Computes characters per word and words per sentence. |
| **Linsear Write** | U.S. Grade Level | Developed for technical manuals; classifies words into easy (1–2 syllables) and hard (3+ syllables) categories over 100-word blocks. |
| **Dale-Chall Score** | 0.0–10.0+ | Measures the percentage of words outside a 3,000-word common vocabulary list alongside sentence length. |
| **Spache Score** | Primary Grade Level | Evaluates unfamiliar vocabulary and sentence length calibrated specifically for primary school texts (grades 1–4). |
| **Text Standard** | Consensus Grade | Aggregate consensus grade level across all applicable formulas. |

## Consensus Grade Robustness

Individual formulas diverge based on their structural weights. On the golden-set legal sample, Coleman-Liau reports 14.7 while Linsear Write reports 25.0 on identical text, representing a ten-grade spread. Reporting any single formula in isolation risks selective interpretation.

`text_standard` computes the consensus across formulas, dampening the variance of individual metrics. Cite `text_standard` as the primary grade level, noting specific formula outliers when diagnostic context is required.

## Operational Boundaries

### Inverse Scaling in Reading Ease

`flesch_reading_ease` scales inversely with grade levels: higher scores indicate simpler reading. The golden-set primary sample scores 106.9 on Reading Ease alongside a negative grade level, whereas the academic sample scores -29.8 with a grade level exceeding 22. Always specify the direction of scale when citing metrics.

### Sample Size Requirements

Readability formulas require sufficient sample volume for stable lexical ratios. For passages under 100 words, docstats marks metrics as low confidence, and the Spache formula may return `null`. See [Troubleshooting](/docstats/guides/troubleshooting/).

## Structural Diagnostics

Raw structural statistics (`word_count`, `sentence_count`, `syllable_count`) identify the causes of high grade levels:

- **Sentence length**: The golden-set legal sample averages 36 words per sentence (109 words across 3 sentences). Splitting compound sentences provides the fastest reduction in grade level.
- **Syllable density**: The academic sample contains 358 syllables in 140 words (2.56 syllables/word). Replacing multi-syllable terms directly lowers Flesch-Kincaid and SMOG scores.

For mapping scores to audience targets, see [Interpreting Scores](/docstats/guides/interpreting-scores/).
