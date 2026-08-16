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

"""Statistical aggregation and effect sizing for A/B experiment runs.

Computes aggregate mean, standard deviation, pairwise deltas (C - B, B - A),
win rates across experimental arms, and dependency-free paired Wilcoxon signed-rank
tests with exact permutation p-values and effect sizes.
"""

import argparse
import json
import logging
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

SCORE_DIMENSIONS = [
    "overall_score",
    "directness",
    "rhythm",
    "authenticity",
    "density",
    "technical_integrity",
]


def wilcoxon_signed_rank_test(x: List[float], y: List[float]) -> Dict[str, Any]:
    """Calculates a paired Wilcoxon signed-rank test without external dependencies.

    Uses exact permutation distribution for N <= 20 non-zero differences and
    normal approximation with continuity correction for larger samples.
    """
    diffs = [a - b for a, b in zip(x, y)]
    non_zero = [d for d in diffs if abs(d) > 1e-9]
    n = len(non_zero)
    if n == 0:
        return {
            "n_nonzero": 0,
            "p_value": 1.0,
            "rank_biserial_r": 0.0,
            "w_stat": 0.0,
            "w_plus": 0.0,
            "w_minus": 0.0,
            "significant_05": False,
        }

    abs_diffs = sorted([(abs(d), i, d) for i, d in enumerate(non_zero)])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and abs(abs_diffs[j][0] - abs_diffs[i][0]) < 1e-9:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j

    w_plus = sum(r for (ad, idx, d), r in zip(abs_diffs, ranks) if d > 0)
    w_minus = sum(r for (ad, idx, d), r in zip(abs_diffs, ranks) if d < 0)
    w_stat = min(w_plus, w_minus)
    total_w = w_plus + w_minus
    r_biserial = (w_plus - w_minus) / total_w if total_w > 0 else 0.0

    if n <= 20:
        rank_vals = [r for (ad, idx, d), r in zip(abs_diffs, ranks)]
        count = 0
        total_perms = 1 << n
        target = w_stat
        for mask in range(total_perms):
            s = 0.0
            for bit in range(n):
                if (mask >> bit) & 1:
                    s += rank_vals[bit]
            if s <= target + 1e-9:
                count += 1
        p_val = min(1.0, 2.0 * count / total_perms)
    else:
        mu = n * (n + 1) / 4.0
        sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
        z = (abs(w_stat - mu) - 0.5) / sigma if sigma > 0 else 0.0
        p_val = math.erfc(abs(z) / math.sqrt(2.0))

    return {
        "n_nonzero": n,
        "w_plus": round(w_plus, 2),
        "w_minus": round(w_minus, 2),
        "w_stat": round(w_stat, 2),
        "rank_biserial_r": round(r_biserial, 3),
        "p_value": round(p_val, 4),
        "significant_05": p_val < 0.05,
    }


def analyze_run_results(run_dir: Path) -> Dict[str, Any]:
    """Parses scores from run directory and calculates aggregate statistics."""
    doc_scores = []
    telemetry_records = []

    for item in sorted(run_dir.iterdir()):
        eval_file = item / "eval_scores.json"
        if eval_file.exists():
            with open(eval_file, "r", encoding="utf-8") as f:
                doc_scores.append(json.load(f))
        telemetry_file = item / "telemetry.json"
        if telemetry_file.exists():
            with open(telemetry_file, "r", encoding="utf-8") as f:
                telemetry_records.append(json.load(f))

    if not doc_scores:
        logger.warning(f"No eval_scores.json files found in {run_dir}")
        return {}

    n_docs = len(doc_scores)

    # Discover all evaluated arms
    all_arms = set()
    for record in doc_scores:
        all_arms.update(record.get("scores_by_arm", {}).keys())

    arm_names = sorted(list(all_arms))
    arm_metrics: Dict[str, Dict[str, List[float]]] = {
        arm: {d: [] for d in SCORE_DIMENSIONS} for arm in arm_names
    }
    win_counts: Dict[str, int] = {arm: 0 for arm in arm_names}

    for record in doc_scores:
        scores_by_arm = record.get("scores_by_arm", {})
        highest_overall = -1.0
        winner = "tie"

        for arm_name in arm_names:
            arm_data = scores_by_arm.get(arm_name, {})
            ratings = arm_data.get("judge_ratings", {})

            for dim in SCORE_DIMENSIONS:
                val = ratings.get(dim)
                if isinstance(val, (int, float)):
                    arm_metrics[arm_name][dim].append(float(val))

            overall = ratings.get("overall_score")
            if isinstance(overall, (int, float)):
                if overall > highest_overall:
                    highest_overall = overall
                    winner = arm_name

        if winner in win_counts:
            win_counts[winner] += 1

    summary_stats: Dict[str, Any] = {
        "document_count": n_docs,
        "evaluated_arms": arm_names,
        "win_counts": win_counts,
        "win_rates": {k: round(v / n_docs, 3) for k, v in win_counts.items()},
        "dimensions": {},
        "statistical_tests": {},
        "movement_by_arm": {},
    }

    # Aggregate Blind Judge Dimensions
    for dim in SCORE_DIMENSIONS:
        dim_summary = {}
        for arm_name in arm_names:
            vals = arm_metrics[arm_name][dim]
            if vals:
                mean_val = round(statistics.mean(vals), 2)
                stdev_val = round(statistics.stdev(vals), 2) if len(vals) > 1 else 0.0
                dim_summary[arm_name] = {"mean": mean_val, "stdev": stdev_val}
            else:
                dim_summary[arm_name] = {"mean": 0.0, "stdev": 0.0}

        # Pairwise deltas relative to stats_augmented if present
        if "stats_augmented" in dim_summary:
            mean_c = dim_summary["stats_augmented"]["mean"]
            for arm_name in arm_names:
                if arm_name != "stats_augmented":
                    m_other = dim_summary[arm_name]["mean"]
                    dim_summary[f"delta_C_minus_{arm_name}"] = round(
                        mean_c - m_other, 2
                    )

        summary_stats["dimensions"][dim] = dim_summary

    # Paired Wilcoxon Signed-Rank Significance Tests
    if "stats_augmented" in arm_names:
        c_scores = arm_metrics["stats_augmented"]
        for arm_name in arm_names:
            if arm_name == "stats_augmented":
                continue
            contrast_key = f"stats_augmented_vs_{arm_name}"
            summary_stats["statistical_tests"][contrast_key] = {}
            for dim in SCORE_DIMENSIONS:
                c_vals = c_scores[dim]
                other_vals = arm_metrics[arm_name][dim]
                if len(c_vals) == len(other_vals) and len(c_vals) > 0:
                    test_res = wilcoxon_signed_rank_test(c_vals, other_vals)
                    summary_stats["statistical_tests"][contrast_key][dim] = test_res

    # Text-only 1 vs Control contrast
    if "text_only_rewriter1" in arm_names and "control" in arm_names:
        b1_scores = arm_metrics["text_only_rewriter1"]
        contrast_key = "text_only_rewriter1_vs_control"
        summary_stats["statistical_tests"][contrast_key] = {}
        for dim in SCORE_DIMENSIONS:
            b1_vals = b1_scores[dim]
            ctrl_vals = arm_metrics["control"][dim]
            if len(b1_vals) == len(ctrl_vals) and len(b1_vals) > 0:
                test_res = wilcoxon_signed_rank_test(b1_vals, ctrl_vals)
                summary_stats["statistical_tests"][contrast_key][dim] = test_res

    # Aggregate Pre -> Post docstats Movement
    if telemetry_records:
        movement_accum: Dict[str, Dict[str, List[float]]] = {
            arm: {"delta_ai_score": [], "delta_fk_grade": [], "delta_tells": []}
            for arm in arm_names
        }
        for telem in telemetry_records:
            arms_data = telem.get("arms", {})
            for arm_name in arm_names:
                arm_entry = arms_data.get(arm_name, {})
                mov = arm_entry.get("movement", {})
                if mov:
                    if "delta_ai_tell_score" in mov:
                        movement_accum[arm_name]["delta_ai_score"].append(
                            mov["delta_ai_tell_score"]
                        )
                    if "delta_fk_grade" in mov:
                        movement_accum[arm_name]["delta_fk_grade"].append(
                            mov["delta_fk_grade"]
                        )
                    if "delta_total_tells" in mov:
                        movement_accum[arm_name]["delta_tells"].append(
                            mov["delta_total_tells"]
                        )

        for arm_name in arm_names:
            acc = movement_accum[arm_name]
            summary_stats["movement_by_arm"][arm_name] = {
                "mean_delta_ai_score": (
                    round(statistics.mean(acc["delta_ai_score"]), 2)
                    if acc["delta_ai_score"]
                    else 0.0
                ),
                "mean_delta_fk_grade": (
                    round(statistics.mean(acc["delta_fk_grade"]), 2)
                    if acc["delta_fk_grade"]
                    else 0.0
                ),
                "mean_delta_tells": (
                    round(statistics.mean(acc["delta_tells"]), 2)
                    if acc["delta_tells"]
                    else 0.0
                ),
            }

    (run_dir / "summary.json").write_text(
        json.dumps(summary_stats, indent=2), encoding="utf-8"
    )

    print_summary_table(summary_stats)
    return summary_stats


def print_summary_table(summary: Dict[str, Any]):
    """Prints a formatted terminal table of summary results."""
    print("\n" + "=" * 90)
    print("                A/B EXPERIMENT STATISTICAL SUMMARY")
    print("=" * 90)
    print(f"Total Documents: {summary.get('document_count', 0)}")
    win_rates = summary.get("win_rates", {})
    rate_strs = [f"{arm}: {rate:.1%}" for arm, rate in win_rates.items()]
    print("Win Rates: " + " | ".join(rate_strs))
    print("-" * 90)

    evaluated_arms = summary.get("evaluated_arms", [])
    hdr = f"{'Dimension':<22} | " + " | ".join(f"{arm:<14}" for arm in evaluated_arms)
    print(hdr)
    print("-" * 90)

    for dim, data in summary.get("dimensions", {}).items():
        row_vals = []
        for arm in evaluated_arms:
            m = data.get(arm, {}).get("mean", 0.0)
            row_vals.append(f"{m:<14.2f}")
        print(f"{dim:<22} | " + " | ".join(row_vals))

    # Print Statistical Significance Tests
    stat_tests = summary.get("statistical_tests", {})
    if stat_tests:
        print("-" * 90)
        print("Paired Wilcoxon Signed-Rank Significance Tests (overall_score):")
        header = (
            f"{'Comparison':<36} | {'W+':<6} | {'W-':<6} | "
            f"{'Effect (r)':<10} | {'p-value':<9} | {'Sig (p<0.05)':<12}"
        )
        print(header)
        print("-" * 90)
        for contrast, dims in stat_tests.items():
            ov = dims.get("overall_score", {})
            w_plus = ov.get("w_plus", 0.0)
            w_minus = ov.get("w_minus", 0.0)
            r = ov.get("rank_biserial_r", 0.0)
            p = ov.get("p_value", 1.0)
            sig = "YES (*)" if ov.get("significant_05") else "NO (ns)"
            row = (
                f"{contrast:<36} | {w_plus:<6.1f} | {w_minus:<6.1f} | "
                f"{r:<10.3f} | {p:<9.4f} | {sig:<12}"
            )
            print(row)

    # Print Movement Section if available
    mov = summary.get("movement_by_arm", {})
    if mov:
        print("-" * 90)
        print("Pre -> Post Docstats Objective Movement:")
        print(
            f"{'Arm':<24} | {'Δ AI Score':<12} | {'Δ FK Grade':<12} | {'Δ Tells':<10}"
        )
        print("-" * 90)
        for arm, m_data in mov.items():
            d_ai = m_data.get("mean_delta_ai_score", 0.0)
            d_fk = m_data.get("mean_delta_fk_grade", 0.0)
            d_tells = m_data.get("mean_delta_tells", 0.0)
            sign_ai = "+" if d_ai > 0 else ""
            sign_fk = "+" if d_fk > 0 else ""
            row_str = (
                f"{arm:<24} | {sign_ai}{d_ai:<11.2f} "
                f"| {sign_fk}{d_fk:<11.2f} | {d_tells:<10.1f}"
            )
            print(row_str)
    print("=" * 90 + "\n")


def main():
    """CLI entry point for analyzing results."""
    parser = argparse.ArgumentParser(
        description="Aggregate and analyze experiment scores."
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Path to specific run directory in eval/results/<timestamp>",
    )
    args = parser.parse_args()
    analyze_run_results(args.run_dir)


if __name__ == "__main__":
    main()
