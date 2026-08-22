---
title: What is docstats?
description: An introduction to docstats, the two-axis model, post-hoc acceptance gating, and supported runtime environments.
sidebar:
  order: 1
---

docstats calculates readability scores and provides deterministic house-style linting for plain text, web pages, and PDFs. It runs as an MCP server for AI coding assistants or as a FastAPI web service.

## Core Problem

Technical documents fail in two distinct dimensions:
1. **Audience calibration**: Prose can miss its target reading level (for example, excessive sentence complexity in beginner documentation).
2. **Editorial discipline**: Prose can accumulate synthetic stylistic tropes, such as throat-clearing openers, binary contrast framing, non-technical filler adverbs, and rhetorical em dashes.

These challenges are orthogonal. Easy-to-read text can violate house style, and lint-clean text can overshoot its audience's reading level. docstats evaluates both dimensions independently.

## The Two Axes

| Axis | Name | Focus | Measurement |
|---|---|---|---|
| **A** | Readability | Audience reading level | Ten standard formulas and consensus grade level. |
| **B** | House-Style Linting | Prose clarity and directness | Deterministic pattern checks rolled into a 0–10 score. |

docstats reports a **two-axis scorecard without a blended headline number**. A draft passes only when both axes pass independently. See [The Two-Axis Model](/docstats/deep-dives/two-axis-model/) for the complete verdict matrix.

## Post-Hoc Acceptance Gating

docstats functions as an **asynchronous acceptance gate and editorial linter**.

In controlled evaluations, injecting live numeric metrics during generation produced no measurable prose quality improvement over direct textual guidance ($p = 0.7253$). Live metrics also encourage metric gaming, where models alter sentence structure solely to satisfy numerical targets. Recommended workflow:

1. Draft or edit with qualitative editorial guidelines.
2. Run docstats as a post-hoc quality gate.
3. Apply targeted edits to resolve diagnostic flags.
4. Re-run docstats to verify the resolution.

For detailed experimental data, see [Statistics & Evaluation](/docstats/deep-dives/statistics-and-evaluation/).

## Target Users

- **AI coding assistants**: docstats provides MCP tools allowing agents (Claude Code, Gemini CLI, Cursor, Antigravity) to audit prose after drafting.
- **CI/CD pipelines**: Automate documentation merge gating against readability and style thresholds.
- **Technical writers and editors**: Run fast, deterministic pre-publish checks across markdown files, live URLs, or PDF documents.

## Technology Stack

docstats runs on Python 3.10+ using `textstat`, `py-readability-metrics`, `fastapi`, and the official `mcp` SDK. It extracts and analyzes direct text, public web pages, and PDFs from HTTP URLs or Google Cloud Storage.

## Next Steps

- [Getting Started](/docstats/guides/getting-started/): Install and run your first analysis.
- [Interpreting Scores](/docstats/guides/interpreting-scores/): Review the two-axis scorecard format.
- [MCP & Agent Plugins](/docstats/integrations/mcp/): Connect docstats to AI agent environments.
