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

"""Generates machine-verified Typst data bindings from evaluation results.

Eliminates manual reporting drift by generating `paper/results_generated.typ`
directly from `summary.json` and evaluated document telemetry.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def generate_typst_bindings(run_dir: Path, output_file: Path) -> Path:
    """Generates `results_generated.typ` from the experiment run artifacts."""
    summary_file = run_dir / "summary.json"
    manifest_file = run_dir / "manifest.json"

    if not summary_file.exists():
        raise FileNotFoundError(f"Missing summary.json in {run_dir}")

    summary: Dict[str, Any] = json.loads(summary_file.read_text(encoding="utf-8"))
    manifest: Dict[str, Any] = (
        json.loads(manifest_file.read_text(encoding="utf-8"))
        if manifest_file.exists()
        else {}
    )

    # Compute exact corpus words
    doc_dirs = sorted(
        [d for d in run_dir.iterdir() if (d / "eval_scores.json").exists()]
    )
    total_words = 0
    for d in doc_dirs:
        src = d / "source.md"
        if src.exists():
            total_words += len(src.read_text(encoding="utf-8").split())

    doc_count = len(doc_dirs)
    avg_words = round(total_words / doc_count, 1) if doc_count > 0 else 0.0

    win_rates = summary.get("win_rates", {})
    win_counts = summary.get("win_counts", {})
    dims = summary.get("dimensions", {})
    movement = summary.get("movement_by_arm", {})
    stat_tests = summary.get("statistical_tests", {})

    ctrl_wr = win_rates.get("control", 0.0)
    b1_wr = win_rates.get("text_only_rewriter1", 0.0)
    b2_wr = win_rates.get("text_only_rewriter2", 0.0)
    c_wr = win_rates.get("stats_augmented", 0.0)

    ctrl_wc = win_counts.get("control", 0)
    b1_wc = win_counts.get("text_only_rewriter1", 0)
    b2_wc = win_counts.get("text_only_rewriter2", 0)
    c_wc = win_counts.get("stats_augmented", 0)

    # Extract dimension means and deltas
    dim_names_map = [
        ("directness", "Directness"),
        ("rhythm", "Rhythm & Cadence"),
        ("authenticity", "Voice Authenticity"),
        ("density", "Information Density"),
        ("technical_integrity", "Technical Integrity"),
        ("overall_score", "Overall Score"),
    ]

    judge_rows = []
    for dim_key, dim_label in dim_names_map:
        d = dims.get(dim_key, {})
        m_a = d.get("control", {}).get("mean", 0.0)
        m_b1 = d.get("text_only_rewriter1", {}).get("mean", 0.0)
        m_b2 = d.get("text_only_rewriter2", {}).get("mean", 0.0)
        m_c = d.get("stats_augmented", {}).get("mean", 0.0)
        delta_c_b1 = d.get("delta_C_minus_text_only_rewriter1", 0.0)
        sign = "+" if delta_c_b1 > 0 else ""

        is_bold = "overall" in dim_key
        lbl = f"[*{dim_label}*]" if is_bold else f"[{dim_label}]"
        c_fmt = f"[*{m_c:.2f}*]" if m_c >= max(m_a, m_b1, m_b2) else f"[{m_c:.2f}]"
        b1_fmt = (
            f"[*{m_b1:.2f}*]"
            if m_b1 > m_c and m_b1 >= max(m_a, m_b2)
            else f"[{m_b1:.2f}]"
        )

        judge_rows.append(
            f"    {lbl}, [{m_a:.2f}], {b1_fmt}, [{m_b2:.2f}], {c_fmt}, [{sign}{delta_c_b1:.2f}],"
        )

    judge_table_typst = "\n".join(judge_rows)

    # Extract movement rows
    mov_rows = []
    arm_labels = [
        ("control", "Arm A (Control)"),
        ("text_only_rewriter1", "Arm B1 (Text-1)"),
        ("text_only_rewriter2", "Arm B2 (Text-2)"),
        ("stats_augmented", "Arm C (Stats-Augmented)"),
    ]
    for arm_k, arm_lbl in arm_labels:
        m_data = movement.get(arm_k, {})
        d_ai = m_data.get("mean_delta_ai_score", 0.0)
        d_fk = m_data.get("mean_delta_fk_grade", 0.0)
        d_tells = m_data.get("mean_delta_tells", 0.0)
        s_ai = "+" if d_ai > 0 else ""
        s_fk = "+" if d_fk > 0 else ""
        mov_rows.append(
            f"    [{arm_lbl}], [{s_ai}{d_ai:.2f}], [{s_fk}{d_fk:.2f}], [{d_tells:.1f}],"
        )
    mov_table_typst = "\n".join(mov_rows)

    # Extract statistical tests rows
    stat_rows = []
    contrast_map = [
        ("stats_augmented_vs_control", "Arm C vs Arm A (Control)"),
        ("stats_augmented_vs_text_only_rewriter1", "Arm C vs Arm B1 (Primary Text)"),
        ("stats_augmented_vs_text_only_rewriter2", "Arm C vs Arm B2 (Alt Text)"),
        ("text_only_rewriter1_vs_control", "Arm B1 vs Arm A (Control)"),
    ]
    for c_key, c_label in contrast_map:
        test = stat_tests.get(c_key, {}).get("overall_score", {})
        w_stat = test.get("w_stat", 0.0)
        r_eff = test.get("rank_biserial_r", 0.0)
        p_val = test.get("p_value", 1.0)
        sig_str = (
            "Yes ($p < 0.01$)"
            if p_val < 0.01
            else ("Yes ($p < 0.05$)" if p_val < 0.05 else "No ($p \\ge 0.05$)")
        )
        stat_rows.append(
            f"    [{c_label}], [{w_stat:.1f}], [{r_eff:+.3f}], [{p_val:.4f}], [{sig_str}],"
        )
    stat_table_typst = "\n".join(stat_rows)

    content = f"""// AUTO-GENERATED FILE. DO NOT EDIT DIRECTLY.
// Generated by eval/paper_data.py from {run_dir.name}/summary.json

#let exp-doc-count = {doc_count}
#let exp-total-words = {total_words}
#let exp-avg-words = {avg_words}
#let exp-primary-model = "{manifest.get("primary_model", "gemini-3.7-flash")}"
#let exp-judge-model = "gemini-3.1-pro-preview"

#let win-rate-control = "{ctrl_wr:.1%}"
#let win-rate-b1 = "{b1_wr:.1%}"
#let win-rate-b2 = "{b2_wr:.1%}"
#let win-rate-c = "{c_wr:.1%}"

#let win-count-control = {ctrl_wc}
#let win-count-b1 = {b1_wc}
#let win-count-b2 = {b2_wc}
#let win-count-c = {c_wc}

#let delta-overall-c-b1 = "{dims.get("overall_score", {}).get("delta_C_minus_text_only_rewriter1", 0.0):+.2f}"
#let delta-overall-c-ctrl = "{dims.get("overall_score", {}).get("delta_C_minus_control", 0.0):+.2f}"

#let judge-results-table = figure(
  table(
    columns: (1.8fr, 1.1fr, 1.1fr, 1.1fr, 1.1fr, 1.3fr),
    align: (left, center, center, center, center, center),
    stroke: (x, y) => if y == 0 {{ (bottom: 1pt + black) }} else if y == 1 {{ (bottom: 0.5pt + black) }} else {{ none }},
    table.header([*Dimension*], [*Arm A (Control)*], [*Arm B1 (Text-1)*], [*Arm B2 (Text-2)*], [*Arm C (Stats)*], [*Delta ($C - B_1$)*]),
{judge_table_typst}
  ),
  caption: [Blind LLM judge evaluations across {doc_count} corpus documents (1–10 scale; mean scores).]
)

#let statistical-tests-table = figure(
  table(
    columns: (2.2fr, 1.0fr, 1.2fr, 1.2fr, 1.4fr),
    align: (left, center, center, center, center),
    stroke: (x, y) => if y == 0 {{ (bottom: 1pt + black) }} else if y == 1 {{ (bottom: 0.5pt + black) }} else {{ none }},
    table.header([*Comparison (Overall Score)*], [*$W$ Stat*], [*Rank-Biserial $r$*], [*$p$-value*], [*Significant?*]),
{stat_table_typst}
  ),
  caption: [Paired Wilcoxon signed-rank tests across experimental arms with exact permutation $p$-values.]
)

#let movement-table = figure(
  table(
    columns: (2.0fr, 1.2fr, 1.2fr, 1.2fr),
    align: (left, center, center, center),
    stroke: (x, y) => if y == 0 {{ (bottom: 1pt + black) }} else if y == 1 {{ (bottom: 0.5pt + black) }} else {{ none }},
    table.header([*Experimental Arm*], [$Delta S_"AI"$], [$Delta "FKG"$], [$Delta N_"tells"$]),
{mov_table_typst}
  ),
  caption: [Objective pre-to-post docstats movement deltas across experimental arms.]
)
"""

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(content, encoding="utf-8")
    logger.info(f"Generated Typst bindings: {output_file}")
    return output_file
