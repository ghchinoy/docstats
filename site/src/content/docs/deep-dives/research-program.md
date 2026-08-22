---
title: Research Program
description: The multi-experiment research program behind docstats — the E1–E5 portfolio, the engine/shared/experiments layout, and the dependency graph between studies.
sidebar:
  order: 5
---

docstats is the instrument for a research program studying whether deterministic statistical metrics help AI rewriters produce better technical prose. This page maps the portfolio of experiments and how the repository is organized to support them.

## Organizing principle

The program separates three concerns so many experiments can share one well-tested foundation:

| Layer | Location | Reused? | Description |
|---|---|---|---|
| **Engine** | `engine/` | Yes (code) | Provider-agnostic execution, blind judging, statistics, and reporting. Experiments call into it; they do not fork it. |
| **Shared assets** | `shared/` | Yes (data) | The evaluation corpus, canonical arm prompt templates, and the vendored skill registry. |
| **Experiments** | `experiments/<id>/` | No (owned) | Each research question is one self-contained directory: a `config.yaml`, a `README.md`, its own `results/`, and a `report.md`. |
| **Reports** | `reports/` | No (owned) | The flagship preprint (E1) plus short technical reports for secondary experiments. |

**Rule of thumb:** if two experiments need the same code or corpus, it belongs in `engine/` or `shared/`. If it is a decision about a specific study, it belongs in that experiment's `config.yaml`.

## Directory layout

```
├── engine/                     # Shared reusable evaluation library
│   ├── run_experiment.py       #   Arm execution (standard + multi-skill)
│   ├── judge.py                #   Blind holistic + per-rule judging
│   ├── analyze_results.py      #   Wilcoxon signed-rank + per-rule aggregation
│   ├── writeup.py              #   Markdown report generator
│   ├── llm_client.py           #   Gemini / Vertex / Claude client
│   └── mcp_client.py           #   docstats MCP client (analyze_document)
│
├── shared/                     # Assets reused across experiments
│   ├── corpus/                 #   Evaluation documents
│   ├── arms/                   #   Canonical arm prompt templates
│   └── skills/registry/        #   Vendored skills + manifest.yaml
│
├── experiments/                # One directory per research question
│   ├── e1-primary-stats-impact/
│   ├── e2-skill-vs-skill/
│   ├── e3-cross-model/
│   ├── e4-per-rule-ablation/
│   └── e5-corpus-provenance/
│
└── reports/                    # Preprints & technical reports
```

## The experiment portfolio

The program is anchored by one flagship study (E1) and secondary studies that extend, stress-test, or re-slice it.

| ID | Title | Research question | Status |
|---|---|---|---|
| **E1** | Primary: Stats Impact | Does augmenting an AI rewriter with deterministic docstats metrics improve prose over text-only editorial guidance? | Data collected. Both editorial arms beat control (p < 0.01); stats-vs-text-only inconclusive (p = 0.73). Flagship paper. |
| **E2** | Skill-vs-Skill Benchmark | Among editorial skills of shared lineage, which produces the best technical prose? | Infra ready; awaiting run. |
| **E3** | Cross-Model Sensitivity | Does the stats-augmentation effect generalize across models and families? | Design; reuses E1 corpus/arms. |
| **E4** | Per-Rule Ablation | Which individual editorial rules drive the observed wins? | Judge infra ready; awaiting ablation arms. |
| **E5** | Corpus Provenance Sensitivity | Does the effect differ by document provenance (human vs AI-slop vs mixed)? | Design; re-slices E1 results. |

## Dependency graph

```
                 E1 (primary corpus, arms, canonical run)
                  │
     ┌────────────┼─────────────┬───────────────┐
     ▼            ▼             ▼               ▼
    E3           E4            E5              E2
 (swap        (add          (re-slice      (swap the
  models)     ablation       existing        editorial
              arms)          run by tier)    skill)
```

E5 is the cheapest — pure re-analysis of E1's run. E3 and E2 reuse E1's corpus and change one axis each. E4 requires generating leave-one-out arm prompts.

## Why this matters for docstats users

The [gate-not-a-dial](/docstats/guides/what-is-docstats/) design and the [non-circular evaluation standards](/docstats/deep-dives/statistics-and-evaluation/) are not stylistic preferences — they are conclusions from E1 and the detection benchmarks. The research program is what keeps docstats honest about what its numbers can and cannot tell you.
