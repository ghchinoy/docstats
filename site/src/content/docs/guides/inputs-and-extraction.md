---
title: Inputs & Extraction
description: Supported input sources (direct text, web URLs, and Google Cloud Storage PDFs) and the preprocessing pipeline.
sidebar:
  order: 2
---

Every docstats request accepts **exactly one** input source. The extraction pipeline extracts clean prose before scoring, preventing code blocks, markup, and boilerplate from skewing metrics.

## Direct Text (`text`)

A plaintext or markdown string, suitable for editor buffers, single paragraphs, and terminal queries.

```json
{ "text": "Your draft content here..." }
```

## Web URL (`web_url`)

A publicly reachable HTTP or HTTPS URL.

- **HTML pages**: Content is retrieved and parsed with `BeautifulSoup`, removing `<script>`, `<style>`, and navigation boilerplate to isolate prose.
- **Web PDFs**: For URLs ending in `.pdf` or returning `application/pdf`, docstats streams the file and extracts text page by page with `pypdf`.

```json
{ "web_url": "https://en.wikipedia.org/wiki/Readability" }
```

## Google Cloud Storage PDF (`gcs_pdf_uri`)

A URI referencing a PDF stored in Google Cloud Storage:

```
gs://bucket-name/path/to/document.pdf
```

### Authentication

Reading from `gs://` URIs requires Google Cloud Application Default Credentials (ADC). Authenticate locally via:

```bash
gcloud auth application-default login
```

Alternatively, set `GOOGLE_APPLICATION_CREDENTIALS` to a service account key path with `roles/storage.objectViewer` permissions on the bucket.

## Extraction and Axis B

Axis B ([house-style linting](/docstats/deep-dives/house-style-linting/)) evaluates extracted prose only. The pipeline strips code blocks, inline code, and table cells before running pattern detectors. This ensures technical exceptions hold automatically, preventing markdown syntax and code operators from triggering lint warnings.
