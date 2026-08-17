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

"""Automated regression testing against Golden Set anchors and AI-pattern fixtures.

Ensures zero-drift across metric formulas and deterministic house-style linting.
"""

import json
import os

import pytest

from metrics import analyze_document_logic, calculate_readability_metrics_logic

GOLDEN_SET_FILES = [
    "level_primary.txt",
    "level_middle.txt",
    "level_academic.txt",
    "level_legal.txt",
]

FIXTURE_FILES = [
    "fixture_clean.txt",
    "fixture_slop.txt",
]


@pytest.mark.asyncio
async def test_golden_set_axis_a_regression():
    """Validates that Golden Set texts produce exact expected metrics (zero drift)."""
    baseline_path = os.path.join("samples", "baseline_results.json")
    assert os.path.exists(baseline_path), "samples/baseline_results.json not found."

    with open(baseline_path, "r", encoding="utf-8") as f:
        expected_baselines = json.load(f)

    for filename in GOLDEN_SET_FILES:
        sample_path = os.path.join("samples", filename)
        assert os.path.exists(sample_path), f"Sample file {sample_path} not found."

        with open(sample_path, "r", encoding="utf-8") as f:
            text = f.read()

        scores = await calculate_readability_metrics_logic(text, filename)
        actual = scores.model_dump()
        expected = expected_baselines.get(filename)

        assert expected is not None, f"No baseline entry for {filename}"

        # Assert key readability metrics match exactly
        for key, expected_val in expected.items():
            actual_val = actual.get(key)
            if isinstance(expected_val, float):
                assert actual_val == pytest.approx(expected_val, abs=1e-3), (
                    f"Drift detected in {filename} for {key}: "
                    f"expected {expected_val}, got {actual_val}"
                )
            else:
                assert actual_val == expected_val, (
                    f"Drift detected in {filename} for {key}: "
                    f"expected {expected_val}, got {actual_val}"
                )


@pytest.mark.asyncio
async def test_ai_pattern_fixture_regression():
    """Validates that paired fixtures match findings on Axis A and Axis B."""
    expected_path = os.path.join("samples", "expected_findings.json")
    assert os.path.exists(expected_path), "samples/expected_findings.json not found."

    with open(expected_path, "r", encoding="utf-8") as f:
        expected_findings = json.load(f)

    for filename in FIXTURE_FILES:
        sample_path = os.path.join("samples", filename)
        assert os.path.exists(sample_path), f"Fixture file {sample_path} not found."

        with open(sample_path, "r", encoding="utf-8") as f:
            text = f.read()

        analysis = await analyze_document_logic(text, filename)
        actual_r = analysis.readability.model_dump()
        actual_p = analysis.ai_patterns.model_dump()

        expected = expected_findings.get(filename)
        assert expected is not None, f"No expected findings for {filename}"

        # Validate Axis A readability
        expected_r = expected["readability"]
        for key in ["word_count", "sentence_count", "text_standard"]:
            assert actual_r[key] == expected_r[key], (
                f"Mismatch in {filename} Axis A {key}"
            )

        # Validate Axis B house-style linting
        expected_p = expected["ai_patterns"]
        exp_score = expected_p["ai_tell_score"]
        assert actual_p["ai_tell_score"] == pytest.approx(exp_score, abs=0.05), (
            f"AI score mismatch in {filename}: "
            f"expected {exp_score}, got {actual_p['ai_tell_score']}"
        )
        assert actual_p["total_tells"] == expected_p["total_tells"], (
            f"Total tells mismatch in {filename}: "
            f"expected {expected_p['total_tells']}, got {actual_p['total_tells']}"
        )
        assert actual_p["flags"] == expected_p["flags"], (
            f"Flags mismatch in {filename}: "
            f"expected {expected_p['flags']}, got {actual_p['flags']}"
        )

        # Validate passing status
        if filename == "fixture_clean.txt":
            assert actual_p["ai_tell_score"] >= 7.0
            assert len(actual_p["flags"]) == 0
        elif filename == "fixture_slop.txt":
            assert actual_p["ai_tell_score"] < 7.0
            assert len(actual_p["flags"]) > 0
