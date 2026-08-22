---
title: Inputs & Extraction
description: The three input sources docstats accepts — direct text, web URLs, and Google Cloud Storage PDFs — and how each is extracted into clean prose.
sidebar:
  order: 2
---

Every docstats request accepts **exactly one** input source. The extraction pipeline turns that source into clean prose before any scoring runs, so code blocks, markup, and boilerplate do not distort the metrics.

## Direct text (`text`)

A raw plaintext or markdown string. Ideal for interactive queries, inline code comments, or editor buffers.

```json
{ "text": "Your draft content here..." }
```

## Web URL (`web_url`)

A publicly accessible `http://` or `https://` URL.

- **HTML pages** — content is fetched and parsed with `BeautifulSoup`, stripping `<script>`, `<style>`, and navigation boilerplate to extract the main article prose.
- **Web PDFs** — if the URL ends with `.pdf` (or returns `application/pdf`), the document is streamed and extracted page by page using `pypdf`.

```json
{ "web_url": "https://en.wikipedia.org/wiki/Readability" }
```

## Google Cloud Storage PDF (`gcs_pdf_uri`)

A URI pointing to a PDF file in Google Cloud Storage:

```
gs://bucket-name/path/to/document.pdf
```

### Authentication

Reading from `gs://` requires Google Cloud Application Default Credentials (ADC). Configure them locally:

```bash
gcloud auth application-default login
```

Or set `GOOGLE_APPLICATION_CREDENTIALS` to a service account key path. The account must have `roles/storage.objectViewer` on the target bucket. See [Troubleshooting](/docstats/guides/troubleshooting/) if you hit an ADC error.

## Why extraction matters for Axis B

Axis B ([house-style linting](/docstats/deep-dives/house-style-linting/)) runs on extracted prose only. Code blocks, inline code, and table cells are stripped before detection, so the technical exceptions in the house-style rules hold automatically — an em dash inside a code sample never counts as a rhetorical em dash.
