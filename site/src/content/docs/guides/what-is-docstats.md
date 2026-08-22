---
title: What is docstats?
description: A user-first explainer of docstats — the two-axis model, the post-hoc acceptance gate philosophy, and who it is for.
sidebar:
  order: 1
---

docstats calculates readability scores and provides deterministic house-style linting for plain text, web pages, and PDFs. It runs as an MCP server for AI coding assistants or as a FastAPI web service.

## The problem it solves

Technical documents fail in two independent ways. A page can be pitched at the wrong reading level for its audience — too dense for a tutorial, too breezy for a spec. And a page can carry the stylistic tics of hurried or synthetic prose: throat-clearing openers, "not X, it's Y" framing, filler adverbs, and rhetorical em dashes.

These are orthogonal problems. Easy-to-read text can still violate house style. Lint-clean text can still be pitched at the wrong grade level. docstats measures both and keeps them separate.

## The two axes

| Axis | Name | Question it answers | How it is measured |
|---|---|---|---|
| **A** | Readability | Is the prose at the right reading level for its target audience? | Ten standard formulas plus a consensus grade level (objective, formulaic). |
| **B** | House-Style Linting | Is the prose crisp, direct, and free of editorial tics? | Deterministic pattern checks rolled up into a 0–10 conformity score. |

Because the axes are independent, docstats reports a **two-axis scorecard with no blended headline number**. A draft passes only when both axes pass. See [The Two-Axis Model](/docstats/deep-dives/two-axis-model/) for the full verdict matrix.

## A gate, not a generative dial

docstats is optimized as an **asynchronous acceptance gate and editorial linter**, not as an in-prompt generative dial.

Empirical research indicates that injecting live numeric metrics during text generation does not improve prose quality over clear textual guidance (p = 0.7253) and risks artificial metric gaming — a model can chase a target number while the prose gets worse. The recommended workflow is:

1. Draft or edit with qualitative editorial guidelines.
2. Run docstats as a post-hoc quality gate.
3. Apply targeted edits to resolve any diagnostic flags.
4. Re-run to confirm the fix.

For the evidence behind this design choice, see [Statistics & Evaluation](/docstats/deep-dives/statistics-and-evaluation/).

## Who it is for

- **AI coding assistants** — docstats exposes an MCP tool so agents (Claude Code, Gemini CLI, Cursor, Antigravity) can audit prose they generate or edit.
- **CI/CD pipelines** — gate documentation merges on readability and house-style thresholds.
- **Editors and technical writers** — run a fast, deterministic pre-publish check on drafts, web pages, or PDFs.

## What it is built on

docstats is written in Python (3.10+) using `textstat`, `py-readability-metrics`, `fastapi`, and the official `mcp` SDK. It accepts direct text, public web pages, and PDFs from web URLs or Google Cloud Storage.

## Next steps

- [Getting Started](/docstats/guides/getting-started/) — install and run your first analysis.
- [Interpreting Scores](/docstats/guides/interpreting-scores/) — read the scorecard.
- [MCP & Agent Plugins](/docstats/integrations/mcp/) — wire it into your agent.
