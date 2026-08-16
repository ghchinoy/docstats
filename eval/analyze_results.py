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
and win rates across experimental arms.
"""

import argparse
import json
import logging
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
