# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Formal experiment report and publication writeup generator.

Generates a comprehensive Markdown evaluation writeup from run telemetry,
blind judge scores, and statistical analysis.
"""

import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def generate_formal_writeup(run_dir: Path) -> Path:
    """Generates `report.md` in the target run directory."""
    manifest_file = run_dir / "manifest.json"
    summary_file = run_dir / "summary.json"

    if not manifest_file.exists():
        raise FileNotFoundError(f"Missing manifest.json in {run_dir}")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    summary = (
        json.loads(summary_file.read_text(encoding="utf-8"))
        if summary_file.exists()
        else {}
    )

    doc_evals = []
    for item in sorted(run_dir.iterdir()):
        eval_file = item / "eval_scores.json"
        if eval_file.exists():
            doc_evals.append(json.loads(eval_file.read_text(encoding="utf-8")))

    # Determine Verdict
    delta_cb = (
        summary.get("dimensions", {})
        .get("overall_score", {})
        .get("delta_stats_C_minus_B", 0.0)
    )
    win_rates = summary.get("win_rates", {})
    stats_win_rate = win_rates.get("stats_augmented", 0.0)

    if delta_cb > 0.3 and stats_win_rate >= 0.5:
        verdict_badge = "✅ **HYPOTHESIS SUPPORTED**"
        verdict_desc = (
            "Formal statistical and pattern metrics measurably improved AI "
            f"writing assistance. Arm C (Stats-Augmented) outperformed "
            f"Arm B (Text-Only) by an average of **+{delta_cb:.2f} points** "
            f"overall and achieved a **{stats_win_rate:.1%} win rate** "
            "in blind evaluation."
        )
    elif delta_cb < -0.2:
        verdict_badge = "❌ **HYPOTHESIS DISPROVEN**"
        verdict_desc = (
            "Stats-augmentation did not outperform text guidance alone. "
            f"Arm B (Text-Only) scored higher or comparable to Arm C "
            f"({delta_cb:+.2f} delta)."
        )
    else:
        verdict_badge = "⚖️ **NEUTRAL / INCONCLUSIVE**"
        verdict_desc = (
            "Performance between Text-Only (Arm B) and Stats-Augmented "
            f"(Arm C) was statistically comparable (overall delta: {delta_cb:+.2f})."
        )

    # Build Document Detail Rows
    doc_sections = []
    for doc in doc_evals:
        doc_id = doc.get("document_id", "Unknown")
        rankings = ", ".join(doc.get("judge_summary", {}).get("rankings_blinded", []))
        rationale = doc.get("judge_summary", {}).get("rationale", "")
        scores = doc.get("scores_by_arm", {})

        s_a = (
            scores.get("control", {}).get("judge_ratings", {}).get("overall_score", 0.0)
        )
        s_b = (
            scores.get("text_only", {})
            .get("judge_ratings", {})
            .get("overall_score", 0.0)
        )
        s_c = (
            scores.get("stats_augmented", {})
            .get("judge_ratings", {})
            .get("overall_score", 0.0)
        )

        doc_sections.append(
            f"### Document: `{doc_id}`\n\n"
            f"- **Blind Rankings:** {rankings}\n"
            f"- **Overall Scores:** Control: `{s_a}` | Text-Only: `{s_b}` | "
            f"Stats-Augmented: `{s_c}`\n"
            f"- **Judge Rationale:** {rationale}\n"
        )

    # Build Dimension Summary Rows
    dim_rows = []
    for dim, data in summary.get("dimensions", {}).items():
        m_a = data.get("control", {}).get("mean", 0.0)
        m_b = data.get("text_only", {}).get("mean", 0.0)
        m_c = data.get("stats_augmented", {}).get("mean", 0.0)
        d_cb = data.get("delta_stats_C_minus_B", 0.0)
        sign = "+" if d_cb > 0 else ""
        dim_name = dim.replace("_", " ").title()
        dim_rows.append(
            f"| **{dim_name}** | {m_a:.2f} | {m_b:.2f} | {m_c:.2f} | {sign}{d_cb:.2f} |"
        )

    premise_intro = (
        "Technical writing produced or revised by Large Language Models often "
        "exhibits synthetic stylistic tropes: throat-clearing openers, binary "
        'contrast frames ("not X, it\'s Y"), metronomic sentence structures, '
        "and unearned rhetorical markers.\n\n"
        "The `technical-post-editorial` framework establishes rule-based "
        "guidance to counteract these patterns. This experiment evaluates whether "
        "**coupling this guidance with live, multi-protocol statistical "
        "feedback (docstats MCP `analyze_document`)** yields superior outcomes "
        "compared to providing text rules alone."
    )

    method_intro = (
        "- **Blind LLM Judge:** Candidate revisions were anonymized, randomized "
        "(`Candidate 1, 2, 3`), and evaluated by an independent judge model "
        "instance with no awareness of arm assignment.\n"
        "- **Multi-Dimensional Criteria:** Candidates were evaluated across "
        "Directness, Rhythm, Voice Authenticity, Density, Technical Integrity, "
        "and Overall Quality.\n"
        "- **Held-Out Telemetry:** Tool execution, token cost, latency, and "
        "compression ratios were independently logged."
    )

    model_name = manifest.get("model", "default")
    run_id = manifest.get("run_id", "unknown")
    timestamp_str = manifest.get("timestamp", "")
    doc_count = manifest.get("document_count", 0)

    dim_table = "\n".join(dim_rows)
    doc_table = "\n".join(doc_sections)

    report_content = f"""# Empirical Evaluation Report: Formal Stats vs Text Guidance

**Run Identifier:** `{run_id}`
**Model:** `{model_name}`
**Evaluation Date:** `{timestamp_str}`
**Corpus Size:** {doc_count} document(s)

---

## 1. Executive Summary & Verdict

{verdict_badge}

{verdict_desc}

### Key Aggregate Metrics:
- **Win Rates:**
  - Arm C (Stats-Augmented): **{win_rates.get("stats_augmented", 0.0):.1%}**
  - Arm B (Text-Only): **{win_rates.get("text_only", 0.0):.1%}**
  - Arm A (Control): **{win_rates.get("control", 0.0):.1%}**
- **Overall Quality Delta (C - B):** **{delta_cb:+.2f} / 10**

---

## 2. Experimental Premise & Research Question

{premise_intro}

### Experimental Conditions:
1. **Arm A (Control):** Standard LLM polish without specific constraints.
2. **Arm B (Text-Only):** LLM guided by `technical-post-editorial` rules.
3. **Arm C (Stats-Augmented):** Guided by rules + docstats MCP (`analyze_document`).

---

## 3. Methodology & Independence Guarantees

{method_intro}

---

## 4. Empirical Data & Statistical Breakdown

### Dimension Performance (1–10 Scale)

| Dimension | Control (A) | Text-Only (B) | Stats-Augmented (C) | Delta (C - B) |
|---|---|---|---|---|
{dim_table}

---

## 5. Document-by-Document Evaluations

{doc_table}

---

## 6. Replication Guide

To independently reproduce this evaluation run:

```bash
# 1. Sync evaluation dependencies
uv sync --group dev --group eval

# 2. Configure model credentials (Gemini Developer API or Vertex AI)
export GEMINI_API_KEY="<your-key>"

# 3. Execute experiment across corpus
uv run python eval/run_experiment.py --model {model_name}

# 4. Evaluate with blind judge and generate report
uv run python eval/judge.py --run-dir {run_dir}
uv run python eval/analyze_results.py --run-dir {run_dir}
uv run python eval/writeup.py --run-dir {run_dir}
```

---
*Report automatically generated by `eval/writeup.py`.*
"""

    report_path = run_dir / "report.md"
    report_path.write_text(report_content, encoding="utf-8")
    logger.info(f"Formal write-up generated: {report_path}")
    return report_path


def main():
    """CLI entry point for generating formal write-up."""
    parser = argparse.ArgumentParser(
        description="Generate formal markdown experiment write-up."
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Path to specific run directory in eval/results/<timestamp>",
    )
    args = parser.parse_args()
    generate_formal_writeup(args.run_dir)


if __name__ == "__main__":
    main()
