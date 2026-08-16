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
from pathlib import Path
from typing import Any, Dict, List

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

    for item in sorted(run_dir.iterdir()):
        eval_file = item / "eval_scores.json"
        if eval_file.exists():
            with open(eval_file, "r", encoding="utf-8") as f:
                doc_scores.append(json.load(f))

    if not doc_scores:
        logger.warning(f"No eval_scores.json files found in {run_dir}")
        return {}

    n_docs = len(doc_scores)
    arm_metrics: Dict[str, Dict[str, List[float]]] = {
        "control": {d: [] for d in SCORE_DIMENSIONS},
        "text_only": {d: [] for d in SCORE_DIMENSIONS},
        "stats_augmented": {d: [] for d in SCORE_DIMENSIONS},
    }

    win_counts: Dict[str, int] = {"control": 0, "text_only": 0, "stats_augmented": 0}

    for record in doc_scores:
        scores_by_arm = record.get("scores_by_arm", {})
        highest_overall = -1.0
        winner = "tie"

        for arm_name in ["control", "text_only", "stats_augmented"]:
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
        "win_counts": win_counts,
        "win_rates": {k: round(v / n_docs, 3) for k, v in win_counts.items()},
        "dimensions": {},
    }

    for dim in SCORE_DIMENSIONS:
        dim_summary = {}
        for arm_name in ["control", "text_only", "stats_augmented"]:
            vals = arm_metrics[arm_name][dim]
            if vals:
                mean_val = round(statistics.mean(vals), 2)
                stdev_val = round(statistics.stdev(vals), 2) if len(vals) > 1 else 0.0
                dim_summary[arm_name] = {"mean": mean_val, "stdev": stdev_val}
            else:
                dim_summary[arm_name] = {"mean": 0.0, "stdev": 0.0}

        # Compute Deltas: C - B (Stats delta) and B - A (Guidance delta)
        mean_a = dim_summary.get("control", {}).get("mean", 0.0)
        mean_b = dim_summary.get("text_only", {}).get("mean", 0.0)
        mean_c = dim_summary.get("stats_augmented", {}).get("mean", 0.0)

        dim_summary["delta_guidance_B_minus_A"] = round(mean_b - mean_a, 2)
        dim_summary["delta_stats_C_minus_B"] = round(mean_c - mean_b, 2)
        dim_summary["delta_total_C_minus_A"] = round(mean_c - mean_a, 2)

        summary_stats["dimensions"][dim] = dim_summary

    (run_dir / "summary.json").write_text(
        json.dumps(summary_stats, indent=2), encoding="utf-8"
    )

    print_summary_table(summary_stats)
    return summary_stats


def print_summary_table(summary: Dict[str, Any]):
    """Prints a formatted terminal table of summary results."""
    print("\n" + "=" * 78)
    print("                A/B EXPERIMENT STATISTICAL SUMMARY")
    print("=" * 78)
    print(f"Total Documents: {summary.get('document_count', 0)}")
    win_rates = summary.get("win_rates", {})
    print(
        f"Win Rates: Control: {win_rates.get('control', 0.0):.1%} | "
        f"Text-Only: {win_rates.get('text_only', 0.0):.1%} | "
        f"Stats-Augmented: {win_rates.get('stats_augmented', 0.0):.1%}"
    )
    print("-" * 78)
    hdr = (
        f"{'Dimension':<20} | {'Control (A)':<11} | {'Text-Only (B)':<13} "
        f"| {'Stats (C)':<10} | {'C - B (Stats)':<12}"
    )
    print(hdr)
    print("-" * 78)

    for dim, data in summary.get("dimensions", {}).items():
        m_a = data.get("control", {}).get("mean", 0.0)
        m_b = data.get("text_only", {}).get("mean", 0.0)
        m_c = data.get("stats_augmented", {}).get("mean", 0.0)
        delta_cb = data.get("delta_stats_C_minus_B", 0.0)

        sign = "+" if delta_cb > 0 else ""
        row = (
            f"{dim:<20} | {m_a:<11.2f} | {m_b:<13.2f} "
            f"| {m_c:<10.2f} | {sign}{delta_cb:<11.2f}"
        )
        print(row)
    print("=" * 78 + "\n")


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
