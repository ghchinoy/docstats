---
title: Research Program
description: Overview of the E1–E5 experiment portfolio, shared engine architecture, and empirical study designs.
sidebar:
  order: 5
---

docstats provides the measurement infrastructure for experimental studies evaluating whether deterministic statistical metrics improve AI-assisted technical writing.

## Program Architecture

The research program decouples execution engine code, shared assets, and individual study configurations:

| Layer | Location | Shared? | Purpose |
|---|---|---|---|
| **Engine** | `engine/` | Yes (code) | Provider-agnostic execution, blind judging, non-parametric statistics, and automated reporting. |
| **Shared Assets** | `shared/` | Yes (data) | Evaluation corpus documents, canonical arm prompt templates, and skill registries. |
| **Experiments** | `experiments/<id>/` | No (owned) | Study definitions containing `config.yaml`, `README.md`, timestamped `results/`, and `report.md`. |
| **Reports** | `reports/` | No (owned) | Preprints and technical reports compiling findings across study runs. |

## Repository Layout

```
├── engine/                     # Reusable evaluation and analysis engine
│   ├── run_experiment.py       #   Multi-arm study execution
│   ├── judge.py                #   Blind holistic and per-rule judging
│   ├── analyze_results.py      #   Wilcoxon signed-rank significance testing
│   ├── writeup.py              #   Automated markdown report generator
│   ├── llm_client.py           #   Model client (Gemini / Vertex / Claude)
│   └── mcp_client.py           #   docstats MCP client wrapper
│
├── shared/                     # Shared study assets
│   ├── corpus/                 #   Standardized evaluation documents
│   ├── arms/                   #   Canonical prompt templates
│   └── skills/registry/        #   Vendored editorial skills
│
├── experiments/                # Individual experiment definitions
│   ├── e1-primary-stats-impact/
│   ├── e2-skill-vs-skill/
│   ├── e3-cross-model/
│   ├── e4-per-rule-ablation/
│   └── e5-corpus-provenance/
│
└── reports/                    # Formal technical reports and preprints
```

## Experiment Portfolio

The program centers on an initial flagship study (E1) alongside targeted follow-on investigations:

| ID | Title | Research Question | Status |
|---|---|---|---|
| **E1** | Primary: Stats Impact | Does augmenting an AI rewriter with live docstats metrics improve technical prose over text-only editorial guidance? | Completed. Both editorial arms outperformed unguided control ($p < 0.01$). Live metrics vs text-only was inconclusive ($p = 0.73$). |
| **E2** | Skill-vs-Skill Benchmark | Which editorial skill produces the highest-rated technical prose across shared benchmarks? | Infrastructure complete; execution pending. |
| **E3** | Cross-Model Sensitivity | Does the effect of editorial guidance generalize across model families (Gemini, Claude)? | Study design complete; reuses E1 corpus and arms. |
| **E4** | Per-Rule Ablation | What is the marginal contribution of each individual editorial rule to overall quality gains? | Judging infrastructure complete; ablation arm prompts in development. |
| **E5** | Corpus Provenance Sensitivity | How does rewriting efficacy vary across human-authored, AI-generated, and mixed text? | Analysis design complete; re-slices E1 run data. |

## Study Dependency Graph

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

E5 requires pure re-analysis of E1 data. E3 and E2 reuse the E1 corpus while varying the model and skill dimensions. E4 introduces leave-one-out arm prompt templates.

## Connection to docstats Architecture

The post-hoc acceptance gate architecture ([Overview](/docstats/guides/what-is-docstats/)) and non-circular evaluation methodology ([Statistics & Evaluation](/docstats/deep-dives/statistics-and-evaluation/)) derive directly from findings in E1 and benchmark evaluations. The research program provides empirical grounding for the tool's design and operating guidelines.
