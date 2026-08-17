# Copyright 2025 Google LLC
# baseline_analysis.py - Baseline scores for Golden Set & Fixtures.

"""Baseline analysis and regression verification for docstats."""

import argparse
import asyncio
import json
import os
import sys
from typing import Tuple

from metrics import analyze_document_logic, calculate_readability_metrics_logic

GOLDEN_SAMPLES = [
    "level_primary.txt",
    "level_middle.txt",
    "level_academic.txt",
    "level_legal.txt",
]

FIXTURE_SAMPLES = [
    "fixture_clean.txt",
    "fixture_slop.txt",
]


async def verify_golden_set(update: bool = False) -> Tuple[bool, dict]:
    """Computes scores for golden set samples and compares against baseline.

    Args:
        update: If True, writes computed scores to samples/baseline_results.json.

    Returns:
        Tuple of (all_match boolean, results dictionary).
    """
    results = {}
    baseline_path = os.path.join("samples", "baseline_results.json")
    expected = {}
    if os.path.exists(baseline_path):
        with open(baseline_path, "r", encoding="utf-8") as f:
            expected = json.load(f)

    all_match = True
    print(
        f"\n{'Golden Set Sample':<20} | {'Standard':<9} | "
        f"{'FK Grade':<9} | {'Reading Ease':<13} | {'Status':<8}"
    )
    print("-" * 70)

    for filename in GOLDEN_SAMPLES:
        path = os.path.join("samples", filename)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        scores = await calculate_readability_metrics_logic(text, filename)
        scores_dict = scores.model_dump()
        results[filename] = scores_dict

        status = "NEW"
        if filename in expected:
            exp = expected[filename]
            matches = True
            for k in ["text_standard", "word_count", "sentence_count"]:
                if scores_dict.get(k) != exp.get(k):
                    matches = False
            for k in ["flesch_reading_ease", "flesch_kincaid_grade"]:
                if abs(scores_dict.get(k, 0.0) - exp.get(k, 0.0)) > 0.01:
                    matches = False
            status = "PASS" if matches else "DRIFT"
            if not matches:
                all_match = False

        print(
            f"{filename:<20} | {scores.text_standard:<9} | "
            f"{scores.flesch_kincaid_grade:<9.2f} | "
            f"{scores.flesch_reading_ease:<13.2f} | {status:<8}"
        )

    if update:
        with open(baseline_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nBaseline results updated in {baseline_path}")

    return all_match, results


async def verify_fixtures(update: bool = False) -> Tuple[bool, dict]:
    """Computes scores for paired fixtures and compares against expected findings.

    Args:
        update: If True, writes computed results to samples/expected_findings.json.

    Returns:
        Tuple of (all_match boolean, results dictionary).
    """
    results = {}
    expected_path = os.path.join("samples", "expected_findings.json")
    expected = {}
    if os.path.exists(expected_path):
        with open(expected_path, "r", encoding="utf-8") as f:
            expected = json.load(f)

    all_match = True
    print(
        f"\n{'Fixture Sample':<20} | {'AI Score':<9} | "
        f"{'Tells':<6} | {'Flags':<6} | {'Verdict':<18} | {'Status':<8}"
    )
    print("-" * 78)

    for filename in FIXTURE_SAMPLES:
        path = os.path.join("samples", filename)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        analysis = await analyze_document_logic(text, filename)
        is_clean = (
            analysis.ai_patterns.ai_tell_score >= 7.0
            and len(analysis.ai_patterns.flags) == 0
        )
        verdict = "Ship" if is_clean else "Revise for Voice"
        results[filename] = {
            "readability": analysis.readability.model_dump(),
            "ai_patterns": analysis.ai_patterns.model_dump(),
            "expected_verdict": verdict,
        }

        status = "NEW"
        if filename in expected:
            exp_p = expected[filename].get("ai_patterns", {})
            diff = abs(
                analysis.ai_patterns.ai_tell_score - exp_p.get("ai_tell_score", 0.0)
            )
            matches = (
                diff <= 0.05
                and analysis.ai_patterns.total_tells == exp_p.get("total_tells")
                and analysis.ai_patterns.flags == exp_p.get("flags")
            )
            status = "PASS" if matches else "DRIFT"
            if not matches:
                all_match = False

        print(
            f"{filename:<20} | {analysis.ai_patterns.ai_tell_score:<9.2f} | "
            f"{analysis.ai_patterns.total_tells:<6} | "
            f"{len(analysis.ai_patterns.flags):<6} | "
            f"{verdict:<18} | {status:<8}"
        )

    if update:
        with open(expected_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nFixture expected findings updated in {expected_path}")

    return all_match, results


async def main():
    """Main CLI entrypoint for baseline regression checks."""
    parser = argparse.ArgumentParser(
        description="Baseline & regression analysis for docstats"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update baseline files with current results",
    )
    args = parser.parse_args()

    print("Running Docstats Baseline & Regression Analysis...")
    golden_ok, _ = await verify_golden_set(update=args.update)
    fixture_ok, _ = await verify_fixtures(update=args.update)

    if golden_ok and fixture_ok:
        print("\nAll baseline regression checks PASSED (zero drift).")
        sys.exit(0)
    else:
        print("\nDRIFT DETECTED in baseline scores! Run with --update if intentional.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
