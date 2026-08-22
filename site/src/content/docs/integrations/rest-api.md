---
title: REST API
description: FastAPI REST endpoints (/scores/, /patterns/, and /analyze/) with request payloads, curl examples, and response schemas.
sidebar:
  order: 3
---

The FastAPI server exposes the analysis engine over HTTP and JSON. Interactive OpenAPI documentation is accessible at `/docs` when the server is active.

## Starting the Server

```bash
uv run uvicorn fastapi_app:fastapi_app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000/docs` to access the interactive Swagger interface.

## Endpoints

| Endpoint | Method | Axis | Returns |
|---|---|---|---|
| `/scores/` | POST | A | Readability metrics and structural counts. |
| `/patterns/` | POST | B | House-style pattern counts, rates, flags, and `ai_tell_score`. |
| `/analyze/` | POST | A + B | Combined two-axis scorecard. |

## Request Payloads

Every endpoint accepts **exactly one** input source parameter:

```json
{ "text": "The quick brown fox jumps over the lazy dog." }
```

```json
{ "web_url": "https://en.wikipedia.org/wiki/Readability" }
```

```json
{ "gcs_pdf_uri": "gs://bucket-name/path/to/document.pdf" }
```

See [Inputs & Extraction](/docstats/guides/inputs-and-extraction/) for input handling specifications.

## Request Examples

**Score direct text (Axis A):**

```bash
curl -X POST "http://127.0.0.1:8000/scores/" \
  -H "Content-Type: application/json" \
  -d '{"text": "The quick brown fox jumps over the lazy dog."}'
```

**Analyze a web page (Axes A + B):**

```bash
curl -X POST "http://127.0.0.1:8000/analyze/" \
  -H "Content-Type: application/json" \
  -d '{"web_url": "https://en.wikipedia.org/wiki/Readability"}'
```

## Combined Response Schema

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

For field definitions, see [Interpreting Scores](/docstats/guides/interpreting-scores/) and [Readability Formulas](/docstats/deep-dives/readability-formulas/).
