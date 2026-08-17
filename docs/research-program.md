# Research Program: Statistical Metrics Impact on AI Rewriters

This document defines the multi-experiment research program hosted in this
repository, the organizing principles of the directory layout, and the current
portfolio of research questions (experiments).

It is the entry point for understanding **why** the repository is structured the
way it is and **how** to add a new experiment.

---

## 1. Organizing Principle

The repository separates three concerns so that many experiments can share a
single, well-tested foundation:

| Layer | Location | Reused across experiments? | Description |
|---|---|---|---|
| **Engine** | `engine/` | Yes (code) | Provider-agnostic execution, blind judging, statistics, and reporting library. Experiments call into it; they do not fork it. |
| **Shared assets** | `shared/` | Yes (data) | The evaluation corpus, canonical arm prompt templates, and the vendored skill registry. |
| **Experiments** | `experiments/<id>/` | No (owned) | Each research question is one self-contained directory: a `config.yaml`, a `README.md` (RQ + hypotheses + design), its own `results/`, and a `report.md` of findings. |
| **Reports** | `reports/` | No (owned) | The flagship preprint (E1) plus short technical reports for secondary experiments that may graduate to standalone papers. |

**Rule of thumb:** if two experiments would need the same code or the same
corpus, it belongs in `engine/` or `shared/`. If it is a decision *about a
specific study* (which arms, which models, which corpus slice, which judge
mode), it belongs in that experiment's `config.yaml`.

---

## 2. Directory Layout

```
stats-impact-on-ai-rewriters/
├── engine/                     # Shared reusable evaluation library
│   ├── run_experiment.py       #   Arm execution (standard + multi-skill modes)
│   ├── judge.py                #   Blind holistic + per-rule judging
│   ├── analyze_results.py      #   Wilcoxon signed-rank + per-rule aggregation
│   ├── writeup.py              #   Markdown report generator
│   ├── paper_data.py           #   Typst data-binding generator
│   ├── llm_client.py           #   Gemini / Vertex / Claude client
│   ├── mcp_client.py           #   docstats MCP client (analyze_document)
│   └── README.md               #   Engine CLI & API reference
│
├── shared/                     # Assets reused across experiments
│   ├── corpus/                 #   Evaluation documents (+ PROVENANCE, SCHEMA)
│   ├── arms/                   #   Canonical arm prompt templates
│   └── skills/registry/        #   Vendored skills + manifest.yaml
│
├── experiments/                # One directory per research question
│   ├── registry.yaml           #   Index of all experiments + status
│   ├── SCHEMA.md               #   config.yaml schema documentation
│   ├── e1-primary-stats-impact/
│   ├── e2-skill-vs-skill/
│   ├── e3-cross-model/
│   ├── e4-per-rule-ablation/
│   └── e5-corpus-provenance/
│
├── reports/                    # Preprints & technical reports
│   └── flagship/               #   E1 primary preprint (Typst)
│
└── docs/                       # Program-level documentation
    ├── research-program.md     #   This file
    ├── related-work.md
    └── references-verification.md
```

### Anatomy of an experiment directory

```
experiments/<id>/
├── config.yaml     # Machine-readable experiment definition (see experiments/SCHEMA.md)
├── README.md       # RQ, hypothesis, H0, design rationale, how to run
├── results/        # Timestamped runs produced by the engine for THIS experiment
│   └── <timestamp>/
└── report.md       # Human-readable findings summary (links to reports/ if promoted)
```

---

## 3. Experiment Portfolio

The program is anchored by one flagship study (E1) and a set of secondary
studies that extend, stress-test, or re-slice it. Secondary studies begin as
short technical reports and may graduate to standalone preprints.

| ID | Title | Research Question | Primary Contrast | Status |
|---|---|---|---|---|
| **E1** | Primary: Stats Impact | Does augmenting an AI rewriter with deterministic docstats metrics improve technical prose over text-only editorial guidance? | Stats-augmented (C) vs Text-only (B1) | **Data collected.** Both editorial arms beat Control (p<0.01); C vs B1 inconclusive (p=0.73). Flagship paper. |
| **E2** | Skill-vs-Skill Benchmark | Among editorial skills of shared lineage, which produces the best technical prose? | plain-writing vs stop-slop vs technical-post-editorial | Infra ready (multi-skill mode). Awaiting run. |
| **E3** | Cross-Model Sensitivity | Does the stats-augmentation effect generalize across models and model families? | C − B1 within each of {Gemini 3.7, 3.1 Pro, 2.5, Claude†} | Design. Reuses E1 corpus/arms; sweeps `primary_model`. |
| **E4** | Per-Rule Ablation | Which individual editorial rules drive the observed wins (marginal contribution)? | Per-rule win vectors; leave-one-rule-out arms | Judge infra ready (per-rule mode). Awaiting ablation arms. |
| **E5** | Corpus Provenance Sensitivity | Does the effect differ by document provenance tier (human-authored vs AI-slop vs mixed)? | C − B1 stratified by corpus tier | Design. Re-slices E1 results by provenance; no new generation required. |

† Claude on Vertex is currently unavailable (404); E3 runs Gemini-only until the
dormant `ClaudeVertexLLMClient` path is reachable.

### Dependency graph

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

E5 is the cheapest (pure re-analysis of E1's run). E3 and E2 reuse E1's corpus
and only change one axis. E4 requires generating leave-one-out arm prompts.

---

## 4. Adding a New Experiment

1. Choose an id: `eN-short-slug` (kebab-case, unique).
2. Copy an existing experiment directory as a template.
3. Edit `config.yaml` to define arms, corpus (or corpus slice), models, and
   judge mode. See `experiments/SCHEMA.md`.
4. Write `README.md`: the research question, hypothesis, null hypothesis, and
   design rationale. State explicitly what is held constant vs varied relative
   to E1.
5. Register it in `experiments/registry.yaml`.
6. Run via the engine, pointing outputs at the experiment's `results/`:
   ```bash
   uv run python engine/run_experiment.py \
     --corpus shared/corpus \
     --output experiments/<id>/results \
     <experiment-specific flags>
   ```
7. Judge, analyze, and write up:
   ```bash
   uv run python engine/judge.py          --run-dir experiments/<id>/results/<ts>
   uv run python engine/analyze_results.py --run-dir experiments/<id>/results/<ts>
   uv run python engine/writeup.py        --run-dir experiments/<id>/results/<ts>
   ```
8. Summarize findings in the experiment's `report.md`. If the result warrants a
   standalone paper, add a subdirectory under `reports/`.

---

## 5. Reproducibility Guarantees (program-wide)

These hold for every experiment:

- **Blind judging:** outputs are de-identified and randomized before scoring.
- **Independent held-out metrics:** docstats telemetry is recorded for all arms
  but never dictates the win/loss verdict (anti-circularity).
- **Distribution-free statistics:** dependency-free Wilcoxon signed-rank tests
  (exact for small n, normal approximation with continuity correction for large
  n); a p<0.05 gate governs any "significant" claim.
- **Machine-generated tables:** every number in a report/paper is generated from
  the run's `summary.json`; no hand-typed statistics.
- **Golden-set zero-drift:** docstats metric changes are validated against the
  Golden Set before being relied upon.
