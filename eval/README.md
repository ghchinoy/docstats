# Docstats A/B Evaluation Harness

An empirical evaluation framework to prove or disprove whether **formal statistical and pattern metrics (docstats)** enhance AI writing assistance compared to **text-based editorial guidance alone**.

---

## 1. Premise & Hypothesis

- **Hypothesis:** Augmenting an AI writing assistant with formal, multi-dimensional readability statistics (Axis A) and deterministic AI writing tell metrics (Axis B) via the `analyze_document` MCP tool yields measurably superior technical prose compared to giving the assistant text-based editorial rules alone.
- **Null Hypothesis ($H_0$):** Adding formal stats provides no statistically significant improvement in prose quality, readability targeting, or voice authenticity over standard text-based editorial rules.

---

## 2. Experimental Design (Three-Arm Study)

Every document in the evaluation corpus is processed under three distinct experimental conditions:

```
                      ┌──────────────────────────────────────┐
                      │    Original Document (Corpus Draft)  │
                      └──────────────────┬───────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
 ┌──────────────┐                 ┌──────────────┐                 ┌──────────────┐
 │ Arm A:       │                 │ Arm B:       │                 │ Arm C:       │
 │ Control      │                 │ Text-Only    │                 │ Stats+Guide  │
 │              │                 │              │                 │              │
 │ Base model,  │                 │ Editorial    │                 │ Editorial    │
 │ general text │                 │ rules &      │                 │ rules + MCP  │
 │ polish       │                 │ rubric       │                 │ docstats tool│
 └──────┬───────┘                 └──────┬───────┘                 └──────┬───────┘
        │                                │                                │
        └────────────────────────────────┼────────────────────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │ Blind Judge & Independent Evaluation │
                      │ - De-identified, randomized outputs  │
                      │ - Held-out metrics + LLM Judge       │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │ Formal Report & Statistical Verdict  │
                      └──────────────────────────────────────┘
```

| Arm | Assistant Configuration | Purpose |
|---|---|---|
| **Arm A (Control)** | Base LLM instructed to polish and improve technical prose without specific editorial constraints. | Baseline performance floor. |
| **Arm B (Text-Only)** | Base LLM equipped with the full `technical-post-editorial` skill (10 prose rules, Starkman tension test, manual 5-axis rubric). | Isolates the effect of text-based editorial guidance. |
| **Arm C (Stats-Augmented)** | Base LLM equipped with `technical-post-editorial` guidance **plus** active access to the `readability-docstats` MCP server (`analyze_document` tool). | Tests the primary hypothesis ($C - B$). |

---

## 3. Anti-Circularity & Independence Guarantee

To prevent biased scoring (grading Arm C with its own ruler):
1. **Blind Evaluation:** The judge model evaluates randomized, de-identified revisions without knowing which arm produced which revision.
2. **Independent Held-Out Metrics:** In addition to the blind LLM judge, revisions are scored against independent, held-out statistical metrics and structural edit distances.
3. **Descriptive Tool Telemetry:** While docstats metrics are recorded for all arms, they do not dictate the win/loss verdict.

---

## 4. Setup & Authentication

The evaluation harness uses **Gemini models** (default: `gemini-3.7-flash`).

### Prerequisites
Install the `eval` dependency group:
```bash
uv sync --group dev --group eval
```

### Authentication Modes
`eval/llm_client.py` supports two automatic authentication paths:
1. **Gemini Developer API (Default):**
   ```bash
   export GEMINI_API_KEY="your-api-key"
   ```
2. **Google Cloud Vertex AI (Fallback via ADC):**
   ```bash
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   export GOOGLE_GENAI_USE_VERTEXAI="true"
   # Ensure gcloud ADC is logged in:
   gcloud auth application-default login
   ```

---

## 5. Running the Harness

### Step 1: Run Full Experiment
Executes all corpus documents through Arms A, B, and C:
```bash
uv run python eval/run_experiment.py
```
Outputs are written to timestamped directories under `eval/results/<timestamp>/`.

### Step 2: Run Blind Judge & Analysis
Evaluates the outputs de-identified and computes statistical deltas:
```bash
uv run python eval/judge.py --run-dir eval/results/<timestamp>
uv run python eval/analyze_results.py --run-dir eval/results/<timestamp>
```

### Step 3: Generate Formal Publication Writeup
Renders a comprehensive, publication-ready Markdown report (`report.md`):
```bash
uv run python eval/writeup.py --run-dir eval/results/<timestamp>
```

---

## 6. Directory Structure

```
eval/
├── README.md               # This specification and guide
├── llm_client.py           # Provider-agnostic LLM interface (Gemini first)
├── mcp_client.py           # STDIO client connecting to docstats MCP server
├── run_experiment.py       # Multi-arm experiment runner
├── judge.py                # Blind evaluator and held-out metrics
├── analyze_results.py      # Statistical aggregation and effect sizing
├── writeup.py              # Formal report generator
├── arms/                   # Prompt and context definitions for each arm
│   ├── control.md
│   ├── text_only.md
│   └── stats_augmented.md
├── corpus/                 # Representative evaluation documents
│   └── SCHEMA.md           # Metadata and format requirements
└── results/                # Run logs, JSON scores, and generated reports
```
