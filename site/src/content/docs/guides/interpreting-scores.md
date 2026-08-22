---
title: Interpreting Scores
description: How to evaluate the two-axis scorecard, map metrics to audience bands, and remediate flagged issues.
sidebar:
  order: 3
---

Translate docstats metrics into concrete editorial actions across both axes.

## Two-Axis Scorecard Structure

A complete `analyze_document` response contains both Axis A (readability) and Axis B (house style):

```json
{
  "readability": {
    "flesch_reading_ease": 45.1,
    "flesch_kincaid_grade": 8.8,
    "text_standard": "8.0",
    "word_count": 250,
    "sentence_count": 18
  },
  "ai_patterns": {
    "em_dash_count": 0,
    "adverb_ly_rate": 0.8,
    "throat_clearing_count": 0,
    "binary_contrast_count": 0,
    "wh_starter_rate": 0.0,
    "sentence_len_cv": 0.65,
    "ai_tell_score": 10.0,
    "confidence": "high",
    "flags": []
  }
}
```

## Axis A: Audience Target Bands

Evaluate `text_standard` (the cross-formula consensus grade) against the target audience band:

| Target Band | Consensus Grade (`text_standard`) | Reading Ease | Typical Document Types |
|---|---|---|---|
| **Very Accessible** | ≤ 6 | > 70 | Beginner tutorials, onboarding guides |
| **Accessible** | 7–10 | 50–70 | General developer blog posts, READMEs |
| **Dense** | 10–15 | 30–50 | Technical guides, architecture write-ups |
| **Very Dense** | 15–20 | 10–30 | Specifications, RFCs, kernel documentation |
| **Impenetrable** | > 20 | < 10 | Academic research, formal legal texts |

General developer documentation typically targets **Accessible to Dense** (grades 7–15). Reaching "Impenetrable" indicates required simplification unless the document is a formal specification.

:::caution
`flesch_reading_ease` scales inversely with grade levels: higher scores indicate simpler reading. Specify the metric direction when citing scores in reviews.
:::

## Axis B: House-Style Thresholds

| Metric | Passing Threshold | Guidance |
|---|---|---|
| `ai_tell_score` | **≥ 7.0 / 10.0** | Passing floor. Scores below 7.0 require structural editing. |
| `em_dash_count` | ≤ 0.5 per 100 words | Use commas, colons, or parentheses instead of rhetorical em dashes. |
| `throat_clearing_count` | 0 | Remove opening announcements ("Here's the thing:", "It's worth noting"). |
| `binary_contrast_count` | 0 | State the substantive point directly; eliminate "not X, it's Y" framing. |
| `adverb_ly_rate` | ≤ 1.5 per 100 words | Remove non-technical filler adverbs ("fundamentally", "genuinely"). |
| `sentence_len_cv` | Advisory (~0.20–0.40) | Rhythm indicator. Avoid enforcing hard numeric CV targets, which degrade natural rhythm variation. |
| `flags` | Empty list | Resolve all diagnostic warnings returned by the tool. |

## Editorial Remediation Steps

1. Check `text_standard` against the target audience band.
2. If grade level exceeds the target, inspect average sentence length (`word_count / sentence_count`) and syllable density:
   - High average sentence length: Split compound sentences.
   - High syllables per word: Replace multi-syllable jargon with direct terms.
   - Elevated `dale_chall_readability_score`: Simplify vocabulary outside common word lists.
3. If Axis B flags style issues:
   - Remove throat-clearing preambles and state assertions directly.
   - Replace prose em dashes with commas, periods, or colons.
   - Convert binary contrast statements into direct assertions.
4. Re-run `analyze_document` to confirm both axes meet passing thresholds.

## Golden Set Calibration Samples

Reference metrics from docstats' committed baseline (`samples/baseline_results.json`):

| Sample | Target Audience | `text_standard` | `flesch_reading_ease` |
|---|---|---|---|
| `level_primary.txt` | Early primary | -1.0 | 106.9 |
| `level_middle.txt` | Middle / secondary | 15.0 | 35.3 |
| `level_academic.txt` | University / research | 23.0 | -29.8 |
| `level_legal.txt` | Legal / specialist | 25.0 | 14.0 |

Key calibration findings:

- **Consensus reliability**: Individual formulas diverge on complex prose. In the legal sample, Coleman-Liau reports 14.7 while Linsear Write reports 25.0 due to differing weights on word length versus sentence length. `text_standard` provides the most stable evaluation.
- **Structural drivers**: The academic sample has the lowest reading ease (-29.8) due to heavy syllable density (2.56 syllables/word), while the legal sample yields the highest consensus grade (25.0) driven by 36-word average sentence lengths.

For formula mechanics, see [Readability Formulas](/docstats/deep-dives/readability-formulas/).
