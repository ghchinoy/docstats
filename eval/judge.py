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

"""Independent blind LLM judge and held-out metric evaluator.

Evaluates randomized, de-identified revisions across:
  - Directness
  - Rhythm & Flow
  - Voice Authenticity
  - Clarity & Density
  - Technical Integrity
  - Overall Quality
"""

import argparse
import difflib
import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from eval.llm_client import get_llm_client

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

JUDGE_SYSTEM_PROMPT = """You are an elite, impartial technical writing judge.
Evaluate blinded, randomized revisions of technical engineering documents.
Assess each candidate on key editorial criteria with numerical ratings (1–10).

Evaluation Dimensions (1–10 scale, 10 being best):
1. directness: Direct statements rather than announcements or throat-clearing.
2. rhythm: Varied sentence structure and natural cadence vs metronomic pacing.
3. authenticity: Sounds like an engineer who built the system; no AI tropes.
4. density: High information density; fluff and filler pruned.
5. technical_integrity: Accuracy, precision, and preservation of code/specs.
6. overall_score: Holistic technical writing quality.

Respond strictly in valid JSON matching this schema:
{
  "rankings": ["Candidate X", "Candidate Y", "Candidate Z"],
  "candidates": {
    "Candidate 1": {
      "directness": 8.5,
      "rhythm": 8.0,
      "authenticity": 9.0,
      "density": 8.5,
      "technical_integrity": 9.5,
      "overall_score": 8.7,
      "critique": "Concise summary of strengths and weaknesses"
    }
  },
  "rationale": "High-level summary of why the winner was chosen."
}
"""


def compute_held_out_metrics(source_text: str, revised_text: str) -> Dict[str, Any]:
    """Computes independent, tool-agnostic metrics on text differences."""
    src_words = source_text.split()
    rev_words = revised_text.split()

    src_len = max(1, len(src_words))
    rev_len = len(rev_words)

    compression_ratio = round(rev_len / src_len, 3)

    matcher = difflib.SequenceMatcher(None, source_text, revised_text)
    similarity_ratio = round(matcher.ratio(), 3)

    return {
        "word_count": rev_len,
        "compression_ratio": compression_ratio,
        "similarity_ratio": similarity_ratio,
    }


def evaluate_document_blind(
    client,
    doc_dir: Path,
    seed: int = 42,
) -> Dict[str, Any]:
    """Blinds, randomizes, and evaluates candidate revisions for a document."""
    source_file = doc_dir / "source.md"
    meta_file = doc_dir / "meta.yaml"

    if not source_file.exists() or not meta_file.exists():
        raise FileNotFoundError(f"Missing source or meta in {doc_dir}")

    source_text = source_file.read_text(encoding="utf-8")
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f)

    # Discover present arm files
    arms: Dict[str, str] = {}
    for arm_candidate in [
        ("control", "arm_a.md"),
        ("text_only", "arm_b.md"),
        ("text_only_rewriter1", "arm_b1.md"),
        ("text_only_rewriter2", "arm_b2.md"),
        ("stats_augmented", "arm_c.md"),
    ]:
        key, filename = arm_candidate
        p = doc_dir / filename
        if p.exists():
            arms[key] = p.read_text(encoding="utf-8")

    if not arms:
        raise FileNotFoundError(f"No arm output files found in {doc_dir}")

    # Deterministic randomization keyed on seed + doc name
    rng = random.Random(f"{seed}_{doc_dir.name}")
    arm_keys = list(arms.keys())
    rng.shuffle(arm_keys)

    blinded_map = {f"Candidate {i + 1}": k for i, k in enumerate(arm_keys)}
    reverse_map = {k: f"Candidate {i + 1}" for i, k in enumerate(arm_keys)}

    candidate_prompts = []
    for label, arm_key in blinded_map.items():
        candidate_prompts.append(f"### {label}\n\n```markdown\n{arms[arm_key]}\n```")

    aud = meta.get("target", {}).get("audience", "General Developers")
    judge_user_prompt = (
        f"Document Metadata:\n- Title: {meta.get('title', 'Unknown')}\n"
        f"- Target Audience: {aud}\n"
        f"- Doc Type: {meta.get('doc_type', 'technical')}\n\n"
        f"Original Draft:\n```markdown\n{source_text}\n```\n\n"
        f"Candidate Revisions:\n\n" + "\n\n".join(candidate_prompts)
    )

    logger.info(f"[{doc_dir.name}] Invoking Blind LLM Judge...")
    response = client.generate(
        prompt=judge_user_prompt,
        system_instruction=JUDGE_SYSTEM_PROMPT,
        temperature=0.1,
    )

    try:
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        judge_json = json.loads(raw_text.strip())
    except Exception as e:
        logger.error(
            f"Failed to parse JSON response from judge: {e}\n"
            f"Raw output:\n{response.text}"
        )
        judge_json = {"error": str(e), "raw_output": response.text}

    # De-anonymize results and attach held-out metrics
    scores_by_arm: Dict[str, Any] = {}
    candidate_ratings = judge_json.get("candidates", {})

    for arm_name, rev_text in arms.items():
        cand_label = reverse_map[arm_name]
        ratings = candidate_ratings.get(cand_label, {})
        held_out = compute_held_out_metrics(source_text, rev_text)

        scores_by_arm[arm_name] = {
            "blinded_label": cand_label,
            "judge_ratings": ratings,
            "held_out_metrics": held_out,
        }

    evaluation_record = {
        "document_id": doc_dir.name,
        "blinded_map": blinded_map,
        "judge_summary": {
            "rankings_blinded": judge_json.get("rankings", []),
            "rationale": judge_json.get("rationale", ""),
        },
        "scores_by_arm": scores_by_arm,
        "judge_usage": response.usage.__dict__,
    }

    (doc_dir / "eval_scores.json").write_text(
        json.dumps(evaluation_record, indent=2), encoding="utf-8"
    )
    return evaluation_record


def evaluate_run(run_dir: Path, model: Optional[str] = None) -> List[Dict[str, Any]]:
    """Evaluates all document subdirectories within a results run directory."""
    manifest_file = run_dir / "manifest.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest not found in {run_dir}")

    client = get_llm_client(model=model or "gemini-3.7-flash")
    results = []

    for item in sorted(run_dir.iterdir()):
        if item.is_dir() and (item / "meta.yaml").exists():
            res = evaluate_document_blind(client, item)
            results.append(res)

    logger.info(f"Evaluated {len(results)} document(s) in run {run_dir.name}.")
    return results


def main():
    """CLI entry point for running the blind judge on an experiment run."""
    parser = argparse.ArgumentParser(description="Run Blind LLM Judge on Results.")
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Path to specific run directory in eval/results/<timestamp>",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-3.7-flash",
        help="Model to use for Judge",
    )

    args = parser.parse_args()
    evaluate_run(run_dir=args.run_dir, model=args.model)


if __name__ == "__main__":
    main()
