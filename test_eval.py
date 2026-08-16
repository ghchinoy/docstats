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

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

from eval.analyze_results import analyze_run_results
from eval.corpus.capture_baselines import capture_corpus_baselines
from eval.corpus.generate_drafts import generate_tier_1_documents
from eval.judge import compute_held_out_metrics, evaluate_document_blind
from eval.llm_client import (
    ClaudeVertexLLMClient,
    GeminiLLMClient,
    LLMResponse,
    UsageStats,
    get_llm_client,
)
from eval.mcp_client import DocstatsMCPClient
from eval.run_experiment import (
    compute_docstats_movement,
    load_arm_prompt,
    load_corpus_documents,
    run_arm_a,
    run_arm_b1,
    run_arm_b2,
    run_arm_c,
)
from eval.writeup import generate_formal_writeup


def test_llm_client_factory():
    """Verifies provider-agnostic factory routing for Gemini and Claude."""
    client_gemini = get_llm_client("gemini-3.7-flash")
    assert isinstance(client_gemini, GeminiLLMClient)

    client_claude = get_llm_client("claude-3-7-sonnet@20250219")
    assert isinstance(client_claude, ClaudeVertexLLMClient)


def test_compute_docstats_movement():
    """Verifies pre -> post docstats movement calculations."""
    pre = {
        "readability": {"flesch_kincaid_grade": 14.0},
        "ai_patterns": {"ai_tell_score": 4.0, "total_tells": 10},
    }
    post = {
        "readability": {"flesch_kincaid_grade": 10.5},
        "ai_patterns": {"ai_tell_score": 8.5, "total_tells": 2},
    }
    mov = compute_docstats_movement(pre, post)
    assert mov["delta_ai_tell_score"] == 4.5
    assert mov["delta_fk_grade"] == -3.5
    assert mov["delta_total_tells"] == -8


def test_load_arm_prompts():
    """Verifies that all three arm prompt definitions load successfully."""
    for arm in ["control", "text_only", "stats_augmented"]:
        prompt = load_arm_prompt(arm)
        assert len(prompt) > 50
        assert "technical" in prompt.lower()


def test_load_corpus_documents():
    """Verifies that corpus loader discovers valid documents."""
    corpus_dir = Path(__file__).parent / "eval" / "corpus"
    docs = load_corpus_documents(corpus_dir)
    assert len(docs) == 14
    sample_doc = docs[0]
    assert "id" in sample_doc
    assert "source_text" in sample_doc
    assert "meta" in sample_doc


def test_compute_held_out_metrics():
    """Verifies held-out text metrics calculation."""
    src = "One two three four five."
    rev = "One two three."
    metrics = compute_held_out_metrics(src, rev)
    assert metrics["word_count"] == 3
    assert metrics["compression_ratio"] == 0.6
    assert isinstance(metrics["similarity_ratio"], float)


@pytest.mark.asyncio
async def test_run_arms_with_mocked_llm(mocker):
    """Verifies execution of Arms A, B1, B2, and C with mocked LLM and MCP."""
    mock_llm = MagicMock(spec=GeminiLLMClient)
    mock_llm.model = "mock-gemini"
    mock_llm.generate.return_value = LLMResponse(
        text="Revised clean technical prose.",
        model="mock-gemini",
        usage=UsageStats(prompt_tokens=10, candidate_tokens=5, total_tokens=15),
    )

    doc = {
        "id": "test-doc",
        "meta": {"title": "Test"},
        "source_text": "Here's the thing: bad text.",
    }

    # Test Arm A
    res_a = await run_arm_a(mock_llm, doc)
    assert res_a["arm"] == "control"
    assert "Revised" in res_a["revised_text"]

    # Test Arm B1
    res_b1 = await run_arm_b1(mock_llm, doc)
    assert res_b1["arm"] == "text_only_rewriter1"
    assert "Revised" in res_b1["revised_text"]

    # Test Arm B2
    res_b2 = await run_arm_b2(mock_llm, doc)
    assert res_b2["arm"] == "text_only_rewriter2"
    assert "Revised" in res_b2["revised_text"]

    # Test Arm C
    mock_mcp = MagicMock(spec=DocstatsMCPClient)
    mock_mcp.analyze_document = AsyncMock(
        return_value={
            "readability": {"flesch_reading_ease": 55.0},
            "ai_patterns": {"ai_tell_score": 8.5, "flags": []},
        }
    )

    res_c = await run_arm_c(mock_llm, mock_mcp, doc)
    assert res_c["arm"] == "stats_augmented"
    assert len(res_c["mcp_telemetry"]) >= 2


def test_evaluate_and_writeup_pipeline(tmp_path):
    """Verifies full analysis and writeup generation on a synthetic run directory."""
    run_dir = tmp_path / "test_run"
    doc_dir = run_dir / "sample-doc"
    doc_dir.mkdir(parents=True)

    # 1. Create source & arm outputs
    (doc_dir / "source.md").write_text("Source draft text.", encoding="utf-8")
    (doc_dir / "meta.yaml").write_text(
        "id: sample-doc\ntitle: Sample Doc\n", encoding="utf-8"
    )
    (doc_dir / "arm_a.md").write_text("Arm A revision.", encoding="utf-8")
    (doc_dir / "arm_b1.md").write_text("Arm B1 revision.", encoding="utf-8")
    (doc_dir / "arm_b2.md").write_text("Arm B2 revision.", encoding="utf-8")
    (doc_dir / "arm_c.md").write_text("Arm C revision.", encoding="utf-8")

    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": "test_run",
                "model": "gemini-3.7-flash",
                "timestamp": "2026-08-16T12:00:00Z",
                "document_count": 1,
            }
        ),
        encoding="utf-8",
    )

    # 2. Mock Blind Judge evaluation
    mock_llm = MagicMock(spec=GeminiLLMClient)
    judge_json_response = json.dumps(
        {
            "rankings": ["Candidate 1", "Candidate 2", "Candidate 3", "Candidate 4"],
            "candidates": {
                "Candidate 1": {
                    "overall_score": 9.0,
                    "directness": 9.0,
                    "rhythm": 8.5,
                    "authenticity": 9.0,
                    "density": 9.0,
                    "technical_integrity": 9.5,
                    "critique": "Strong output",
                },
                "Candidate 2": {
                    "overall_score": 8.0,
                    "directness": 8.0,
                    "rhythm": 7.5,
                    "authenticity": 8.0,
                    "density": 8.0,
                    "technical_integrity": 8.5,
                    "critique": "Good",
                },
                "Candidate 3": {
                    "overall_score": 7.0,
                    "directness": 7.0,
                    "rhythm": 7.0,
                    "authenticity": 7.0,
                    "density": 7.0,
                    "technical_integrity": 7.5,
                    "critique": "Adequate",
                },
                "Candidate 4": {
                    "overall_score": 6.0,
                    "directness": 6.0,
                    "rhythm": 6.0,
                    "authenticity": 6.0,
                    "density": 6.0,
                    "technical_integrity": 6.5,
                    "critique": "Basic",
                },
            },
            "rationale": "Candidate 1 was most direct and natural.",
        }
    )

    mock_llm.generate.return_value = LLMResponse(
        text=judge_json_response,
        model="gemini-3.7-flash",
        usage=UsageStats(prompt_tokens=50, candidate_tokens=25, total_tokens=75),
    )

    eval_record = evaluate_document_blind(mock_llm, doc_dir)
    assert (doc_dir / "eval_scores.json").exists()
    assert "scores_by_arm" in eval_record

    # 3. Analyze results
    summary = analyze_run_results(run_dir)
    assert (run_dir / "summary.json").exists()
    assert "dimensions" in summary
    assert "overall_score" in summary["dimensions"]

    # 4. Generate writeup report
    report_path = generate_formal_writeup(run_dir)
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert "Empirical Evaluation Report" in report_text
    assert "Executive Summary & Verdict" in report_text
    assert "Replication Guide" in report_text


def test_corpus_extended_schema_and_integrity():
    """Verifies that all corpus documents meet extended schema requirements."""
    corpus_dir = Path(__file__).parent / "eval" / "corpus"
    docs = load_corpus_documents(corpus_dir)
    assert len(docs) == 14

    valid_tiers = {"generated_ai", "synthetic_curated", "public_licensed"}

    for doc in docs:
        meta = doc["meta"]
        assert "id" in meta
        assert "title" in meta
        assert "doc_type" in meta
        assert meta.get("source_tier") in valid_tiers
        assert "license" in meta
        assert "target" in meta
        assert "band" in meta["target"]
        assert "known_tells" in meta

        # Verify source text content
        assert len(doc["source_text"].strip()) > 100

        # Verify baseline.json exists and is valid
        baseline_file = doc["dir_path"] / "baseline.json"
        assert baseline_file.exists()
        baseline_data = json.loads(baseline_file.read_text(encoding="utf-8"))
        assert "readability" in baseline_data
        assert "ai_patterns" in baseline_data


def test_generate_drafts_offline_fallback(tmp_path):
    """Verifies offline generation of Tier 1 corpus documents."""
    out_dir = tmp_path / "corpus_gen"
    paths = generate_tier_1_documents(out_dir, use_live_api=False)
    assert len(paths) == 8
    for p in paths:
        assert (p / "source.md").exists()
        assert (p / "meta.yaml").exists()
        with open(p / "meta.yaml", "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f)
        assert meta["source_tier"] == "generated_ai"


@pytest.mark.asyncio
async def test_capture_corpus_baselines_runner(tmp_path):
    """Verifies baseline capture across a corpus directory."""
    doc_dir = tmp_path / "sample-test-doc"
    doc_dir.mkdir()
    (doc_dir / "source.md").write_text(
        "Here's the thing: this is a test paragraph designed to verify that "
        "baseline capture correctly analyzes text and saves the result to "
        "baseline.json without errors. We ensure that calculations proceed "
        "smoothly across all documents in the corpus.",
        encoding="utf-8",
    )
    (doc_dir / "meta.yaml").write_text(
        "id: sample-test-doc\ntitle: Test\nsource_tier: synthetic_curated\n",
        encoding="utf-8",
    )

    results = await capture_corpus_baselines(tmp_path)
    assert len(results) == 1
    assert (doc_dir / "baseline.json").exists()
    assert results[0]["id"] == "sample-test-doc"
