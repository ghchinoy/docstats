---
title: Troubleshooting
description: Common edge cases in docstats, including sample size limits, null Spache scores, authentication errors, and score divergence.
sidebar:
  order: 4
---

## Short Text Warning (Under 100 Words)

Readability formulas lose statistical stability on short inputs. For passages under 100 words, docstats logs a warning and marks Axis B `confidence` as `low`. For definitive scoring, provide passages of at least 100 words.

## Null Spache Score

The Spache formula requires a minimum sample length and is calibrated exclusively for primary-grade reading levels. Returns of `null` are expected for technical texts and brief passages.

## Google Cloud ADC Authentication Errors

When processing `gs://` URIs, authenticate local credentials via:

```bash
gcloud auth application-default login
```

Verify that the active identity holds `roles/storage.objectViewer` on the bucket. Alternatively, point `GOOGLE_APPLICATION_CREDENTIALS` to an authorized service account key file.

## Divergence Across Formulas

Formulas diverge because each assigns distinct weights to sentence length versus syllable or character counts. For example, character-based formulas diverge from syllable-based formulas on technical jargon. Report `text_standard` as the primary metric, and explain formula-specific outliers when relevant. See [Interpreting Scores](/docstats/guides/interpreting-scores/).

## Reading Ease Directionality

`flesch_reading_ease` scales inversely with grade levels: higher scores indicate simpler prose, whereas higher grade levels indicate greater complexity. Early primary text can score over 100 on Reading Ease alongside negative grade levels.
