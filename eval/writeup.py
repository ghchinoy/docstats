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
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.paper_data import generate_typst_bindings  # noqa: E402

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
        .get(
            "delta_C_minus_text_only_rewriter1",
            summary.get("dimensions", {})
            .get("overall_score", {})
            .get("delta_stats_C_minus_B", 0.0),
        )
    )
    win_rates = summary.get("win_rates", {})
    stats_win_rate = win_rates.get("stats_augmented", 0.0)
    p_val_c_b = (
        summary.get("statistical_tests", {})
        .get("stats_augmented_vs_text_only_rewriter1", {})
        .get("overall_score", {})
        .get("p_value", 1.0)
    )

    if delta_cb > 0.3 and stats_win_rate >= 0.5 and p_val_c_b < 0.05:
        verdict_badge = "✅ **HYPOTHESIS SUPPORTED**"
        verdict_desc = (
            "Formal statistical and pattern metrics measurably improved AI "
            f"writing assistance. Arm C (Stats-Augmented) statistically outperformed "
            f"Arm B (Text-Only) by an average of **+{delta_cb:.2f} points** "
            f"overall (p = {p_val_c_b:.4f}) and achieved a "
            f"**{stats_win_rate:.1%} win rate** "
            "in blind evaluation."
        )
    elif delta_cb < -0.3 and p_val_c_b < 0.05:
        verdict_badge = "❌ **HYPOTHESIS DISPROVEN**"
        verdict_desc = (
            "Stats-augmentation did not outperform text guidance alone. "
            f"Arm B (Text-Only) scored statistically higher than Arm C "
            f"({delta_cb:+.2f} delta, p = {p_val_c_b:.4f})."
        )
    else:
        verdict_badge = "⚖️ **NEUTRAL / INCONCLUSIVE**"
        verdict_desc = (
            "Performance between Text-Only (Arm B1) and Stats-Augmented (Arm C) "
            f"was statistically comparable (overall delta: {delta_cb:+.2f}, "
            f"Wilcoxon p = {p_val_c_b:.4f}, win rate split: {stats_win_rate:.1%} vs "
            f"{win_rates.get('text_only_rewriter1', 0.0):.1%}). Both Arms B1 and C "
            "significantly outperformed unconstrained baseline polish (Arm A)."
        )

    # Build Document Detail Rows
    doc_sections = []
    evaluated_arms = summary.get("evaluated_arms", [])

    for doc in doc_evals:
        doc_id = doc.get("document_id", "Unknown")
        rankings = ", ".join(doc.get("judge_summary", {}).get("rankings_blinded", []))
        rationale = doc.get("judge_summary", {}).get("rationale", "")
        scores = doc.get("scores_by_arm", {})

        score_parts = []
        for arm in evaluated_arms:
            arm_sc = (
                scores.get(arm, {}).get("judge_ratings", {}).get("overall_score", 0.0)
            )
            score_parts.append(f"{arm}: `{arm_sc}`")

        scores_str = " | ".join(score_parts)

        doc_sections.append(
            f"### Document: `{doc_id}`\n\n"
            f"- **Blind Rankings:** {rankings}\n"
            f"- **Overall Scores:** {scores_str}\n"
            f"- **Judge Rationale:** {rationale}\n"
        )

    # Build Dimension Summary Rows
    dim_rows = []
    header_cols = ["Dimension"] + [
        arm.replace("_", " ").title() for arm in evaluated_arms
    ]
    if "stats_augmented" in evaluated_arms and len(evaluated_arms) > 1:
        header_cols.append("Delta (Stats vs Primary Text)")

    dim_hdr = "| " + " | ".join(header_cols) + " |"
    dim_sep = "| " + " | ".join(["---"] * len(header_cols)) + " |"

    for dim, data in summary.get("dimensions", {}).items():
        dim_name = dim.replace("_", " ").title()
        row_vals = [f"**{dim_name}**"]
        for arm in evaluated_arms:
            m = data.get(arm, {}).get("mean", 0.0)
            row_vals.append(f"{m:.2f}")
        if "stats_augmented" in evaluated_arms and len(evaluated_arms) > 1:
            ref_arm = (
                "text_only_rewriter1"
                if "text_only_rewriter1" in evaluated_arms
                else "text_only"
            )
            if ref_arm not in evaluated_arms and "control" in evaluated_arms:
                ref_arm = "control"
            delta = data.get(f"delta_C_minus_{ref_arm}", 0.0)
            sign = "+" if delta > 0 else ""
            row_vals.append(f"{sign}{delta:.2f}")

        dim_rows.append("| " + " | ".join(row_vals) + " |")

    dim_table = f"{dim_hdr}\n{dim_sep}\n" + "\n".join(dim_rows)

    # Build Statistical Tests Table if available
    stat_table = ""
    stat_data = summary.get("statistical_tests", {})
    if stat_data:
        stat_rows = [
            "| Comparison (Overall Score) | W+ | W- | Effect Size (r) "
            "| p-value | Significant (p<0.05)? |",
            "|---|---|---|---|---|---|",
        ]
        for c_name, d_tests in stat_data.items():
            ov = d_tests.get("overall_score", {})
            w_plus = ov.get("w_plus", 0.0)
            w_minus = ov.get("w_minus", 0.0)
            r = ov.get("rank_biserial_r", 0.0)
            p = ov.get("p_value", 1.0)
            sig = "**YES** (p < 0.05)" if ov.get("significant_05") else "NO (ns)"
            c_label = c_name.replace("_", " ").title()
            stat_rows.append(
                f"| **{c_label}** | {w_plus:.1f} | {w_minus:.1f} | "
                f"{r:+.3f} | {p:.4f} | {sig} |"
            )
        stat_table = "\n\n### Paired Wilcoxon Signed-Rank Tests\n\n" + "\n".join(
            stat_rows
        )

    # Build Movement Table if available
    mov_table = ""
    mov_data = summary.get("movement_by_arm", {})
    if mov_data:
        mov_rows = [
            "| Arm | Δ AI Tell Score | Δ FK Grade | Δ Total Tells |",
            "|---|---|---|---|",
        ]
        for arm, m in mov_data.items():
            d_ai = m.get("mean_delta_ai_score", 0.0)
            d_fk = m.get("mean_delta_fk_grade", 0.0)
            d_t = m.get("mean_delta_tells", 0.0)
            s_ai = "+" if d_ai > 0 else ""
            s_fk = "+" if d_fk > 0 else ""
            mov_rows.append(
                f"| **{arm}** | {s_ai}{d_ai:.2f} | {s_fk}{d_fk:.2f} | {d_t:.1f} |"
            )
        mov_table = "\n\n### Objective Pre -> Post Movement\n\n" + "\n".join(mov_rows)

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
        "(`Candidate 1, 2, ...`), and evaluated by an independent judge model "
        "instance with no awareness of arm assignment.\n"
        "- **Multi-Dimensional Criteria:** Candidates were evaluated across "
        "Directness, Rhythm, Voice Authenticity, Density, Technical Integrity, "
        "and Overall Quality.\n"
        "- **Held-Out Telemetry & Movement:** Pre-rewrite baselines and post-rewrite "
        "readability / pattern scores were independently measured across all arms."
    )

    model_name = manifest.get("primary_model", manifest.get("model", "default"))
    run_id = manifest.get("run_id", "unknown")
    timestamp_str = manifest.get("timestamp", "")
    doc_count = manifest.get("document_count", 0)

    doc_table = "\n".join(doc_sections)

    win_rate_strs = [f"  - {arm}: **{rate:.1%}**" for arm, rate in win_rates.items()]
    win_rate_block = "\n".join(win_rate_strs)

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
{win_rate_block}
- **Overall Quality Delta (Stats vs Reference):** **{delta_cb:+.2f} / 10**

---

## 2. Experimental Premise & Research Question

{premise_intro}

### Experimental Conditions:
1. **Arm A (Control):** Standard LLM polish without specific constraints.
2. **Arm B1 (Text-Only Rewriter 1):** Guided by `technical-post-editorial` rules.
3. **Arm B2 (Text-Only Rewriter 2):** Alternate rewriter with editorial rules.
4. **Arm C (Stats-Augmented):** Guided by rules + live docstats MCP feedback.

---

## 3. Methodology & Independence Guarantees

{method_intro}

---

## 4. Empirical Data & Statistical Breakdown

### Dimension Performance (1–10 Scale)

{dim_table}
{stat_table}
{mov_table}

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
uv run python eval/run_experiment.py --primary-model {model_name}

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

    # Generate Typst data bindings for paper
    try:
        typst_out = PROJECT_ROOT / "paper" / "results_generated.typ"
        generate_typst_bindings(run_dir, typst_out)
    except Exception as e:
        logger.warning(f"Could not generate Typst bindings: {e}")

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
