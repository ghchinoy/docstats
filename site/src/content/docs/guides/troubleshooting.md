---
title: Troubleshooting
description: Common docstats edge cases — short-text noise, null Spache scores, and Google Cloud ADC authentication errors — and how to resolve them.
sidebar:
  order: 4
---

## Short text warning (under 100 words)

Readability algorithms become statistically noisy on short fragments. When analyzing inputs under 100 words, docstats logs a warning and marks Axis B `confidence` as `low`. Treat the scores as indicative, not authoritative. For meaningful results, analyze at least ~100 words.

## `spache` returns `null`

The Spache formula requires a minimum sample length and is calibrated only for primary-grade writing. A `null` value is normal for adult or technical texts and for short samples. Nothing is broken.

## Google Cloud ADC error

If you receive authentication errors when processing a `gs://` URI, refresh your Application Default Credentials:

```bash
gcloud auth application-default login
```

Ensure the authenticated account or service account has `roles/storage.objectViewer` on the target bucket. Alternatively, set `GOOGLE_APPLICATION_CREDENTIALS` to a valid service account key path.

## Individual formulas disagree

This is expected, not a bug. Each formula weights sentence length versus word difficulty differently, so they legitimately diverge on the same text. Report the consensus `text_standard` first, then explain notable outliers. See [Interpreting Scores](/docstats/guides/interpreting-scores/) for a worked example.

## Reading ease looks "backwards"

`flesch_reading_ease` runs opposite to the grade scores: higher means *easier*. A primary text can score ~107 on ease while its grade level is negative. Always state which direction you mean.
