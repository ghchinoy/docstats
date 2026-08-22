---
title: Interpreting Scores
description: How to read the two-axis docstats scorecard, map scores to audience-target bands, and turn numbers into concrete edits.
sidebar:
  order: 3
---

docstats hands you numbers. This page turns them into decisions and edits.

## The scorecard at a glance

A full `analyze_document` result carries both axes:

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

## Axis A: audience-target bands

Report `text_standard` (the consensus grade) first, then `flesch_reading_ease`. Map the consensus grade to an audience band:

| Target band | Consensus grade (`text_standard`) | Reading ease | Recommended document types |
|---|---|---|---|
| **Very accessible** | ≤ 6 | > 70 | Beginner tutorials, onboarding guides |
| **Accessible** | 7–10 | 50–70 | General developer blog posts, READMEs |
| **Dense** | 10–15 | 30–50 | Deep technical guides, architecture write-ups |
| **Very dense** | 15–20 | 10–30 | Formal specifications, RFCs, kernel docs |
| **Impenetrable** | > 20 | < 10 | Academic papers, dense legal agreements |

A general developer post should land in **Accessible to Dense**. Landing in "Impenetrable" is a failure unless the document type explicitly allows it (spec, legal, academic).

:::caution
`flesch_reading_ease` runs *opposite* to the grade scores: higher means easier. Always state which direction you mean when reporting a number.
:::

## Axis B: house-style thresholds

| Metric | Passing threshold | Actionable guidance |
|---|---|---|
| `ai_tell_score` | **≥ 7.0 / 10.0** | The floor. Below 7.0 signals a high density of forbidden tropes. |
| `em_dash_count` | ≤ 0.5 per 100 words | Sparse grammatical breaks are fine; cut rhetorical drama dashes. |
| `throat_clearing_count` | 0 | Delete openers like "Here's the thing:", "It's worth noting that". |
| `binary_contrast_count` | 0 | Rewrite "Not X, it's Y" and "X isn't the problem, Y is" framing. |
| `adverb_ly_rate` | ≤ 1.5 per 100 words | Remove non-technical filler adverbs ("fundamentally", "genuinely"). |
| `sentence_len_cv` | *advisory only* (~0.20–0.40) | A rhythm hint, not a gate. **Do not** enforce a numeric CV target — research shows it degrades natural rhythm. |
| `flags` | empty list | Address the specific diagnostic suggestions returned by the tool. |

## Turning scores into edits

1. Report `text_standard` and `flesch_reading_ease`, then state the audience fit.
2. If the text is above target, look at average sentence length (`word_count / sentence_count`) and syllable density to pick the lever:
   - Long sentences → split them.
   - High syllables per word → replace jargon with common words.
   - High `dale_chall_readability_score` → too many unfamiliar words; simplify vocabulary.
3. Re-run and confirm the consensus grade moved toward the target.

## Worked reference points

These values come from docstats' committed golden set, so you can calibrate what a number "feels" like:

| Sample | Intended audience | `text_standard` | `flesch_reading_ease` |
|---|---|---|---|
| `level_primary.txt` | Early primary readers | -1.0 (below grade 1) | 106.9 (extremely easy) |
| `level_middle.txt` | Middle / high school | 15.0 | 35.3 (difficult) |
| `level_academic.txt` | University / research | 23.0 | -29.8 (very difficult) |
| `level_legal.txt` | Legal / specialist | 25.0 | 14.0 (very difficult) |

Two takeaways:

- **The consensus `text_standard` is the most robust single number.** Individual formulas disagree — for the legal sample, Coleman-Liau (14.7) is far below Linsear Write (25.0) — because each weights sentence length versus word difficulty differently.
- **Legal is not hardest on every axis.** The academic sample has the lowest (hardest) reading ease, but the legal sample has the highest consensus grade, driven by very long sentences (~36 words per sentence).

For the mechanics behind each formula, see [Readability Formulas](/docstats/deep-dives/readability-formulas/).
