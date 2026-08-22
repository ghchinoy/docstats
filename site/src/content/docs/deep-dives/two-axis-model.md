---
title: The Two-Axis Model
description: Why docstats keeps readability and house-style conformity orthogonal, how the audience bands are calibrated against the golden set, and the combined verdict matrix.
sidebar:
  order: 3
---

docstats reports a **two-axis scorecard with no blended headline number**. This page explains why that design is deliberate and how the two axes combine into a verdict.

## Two independent requirements

A good technical document must satisfy two requirements that do not depend on each other:

- **Readability (Axis A)** — is the prose pitched at the right reading level for its target audience? Formulaic and objective; computed by standard formulas.
- **House-style conformity (Axis B)** — does the prose stay crisp and direct, free of throat-clearing, binary-contrast framing, filler adverbs, and rhetorical punctuation?

These axes are orthogonal. Text can be easy to read and still violate house style. Text can be lint-clean and pitched at the wrong grade level. Collapsing them into one number would hide exactly the information an editor needs.

## No blended headline number

Because the axes measure different things, a single score would be uninterpretable — a "7/10" could mean "perfect readability, poor style" or "poor readability, perfect style," and the fix for each is opposite. docstats keeps them separate and requires **both to pass** before a draft ships.

## Calibrating the bands against the golden set

The audience-fit bands are tuned so each golden-set reference sample lands in a distinct band:

| Golden set sample | Reading ease | FK grade | Consensus `text_standard` |
|---|---|---|---|
| level_primary | 106.9 | -0.08 | -1.0 |
| level_middle | 35.3 | 12.56 | 15.0 |
| level_academic | -29.8 | 22.38 | 23.0 |
| level_legal | 13.95 | 20.34 | 25.0 |

Note that `level_middle` already scores at grade ~12–15, so the sample names describe *relative* complexity, not literal U.S. school grades.

| Band | FK grade | Reading ease | Golden-set anchor | Intended use |
|---|---|---|---|---|
| Very accessible | < 6 | > 70 | level_primary | Onboarding, beginner tutorials |
| Accessible | 6–10 | 50–70 | (target zone for dev blogs) | General developer posts |
| Dense | 10–16 | 30–50 | level_middle | Advanced / architecture write-ups |
| Very dense | 16–22 | 10–30 | level_legal | Specs, reference, legal |
| Impenetrable | > 22 | < 10 | level_academic | Flag for revision unless intentional |

### Axis A verdict

- **Pass** — the consensus grade falls inside the target band for the declared document type.
- **Warn** — one band away from target.
- **Fail** — two or more bands away, or "Impenetrable" for a type that should be accessible.

Guardrail: under 100 words the formulas lose reliability and `spache` can be uncomputable, so Axis A is reported as **low-confidence** rather than pass/fail.

## The combined verdict matrix

The recommendation surface reports both axes and a combined verdict, adapted by provenance:

| Axis A (audience fit) | Axis B (style score) | Verdict | Provenance-aware action |
|---|---|---|---|
| **Pass** | **Pass** | **Ship** | Ready to publish. |
| **Pass** | **Warn / Fail** | **Revise for Voice** | Raw AI draft: aggressively restructure to remove synthetic tropes. Human text: light-touch linting on specific flags; preserve voice. |
| **Warn / Fail** | **Pass** | **Revise for Complexity** | Adjust sentence length / vocabulary for the target audience without altering voice. |
| **Fail** | **Fail** | **Full Rewrite** | Raw AI draft: overhaul complexity and style. Human text: refactor dense sections; address style lints. |

A draft ships only when both axes pass. No blended headline number is emitted.

## Where the axes come from

- Axis A: see [Readability Formulas](/docstats/deep-dives/readability-formulas/).
- Axis B: see [House-Style Linting](/docstats/deep-dives/house-style-linting/).
- The evidence for the gate-not-a-dial stance: see [Statistics & Evaluation](/docstats/deep-dives/statistics-and-evaluation/).
