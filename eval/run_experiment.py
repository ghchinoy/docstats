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

"""Multi-arm A/B experiment runner.

Orchestrates execution of corpus documents across:
  - Arm A: Control (baseline polish)
  - Arm B: Text-Only (editorial guidance)
  - Arm C: Stats-Augmented (editorial guidance + docstats MCP live metrics)
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from eval.llm_client import GeminiLLMClient, UsageStats
from eval.mcp_client import DocstatsMCPClient

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

EVAL_DIR = Path(__file__).parent
CORPUS_DIR = EVAL_DIR / "corpus"
ARMS_DIR = EVAL_DIR / "arms"
RESULTS_DIR = EVAL_DIR / "results"


def load_arm_prompt(arm_name: str) -> str:
    """Loads markdown prompt instructions for a given experimental arm."""
    prompt_file = ARMS_DIR / f"{arm_name}.md"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Arm prompt file not found: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8")


def load_corpus_documents(corpus_path: Path) -> List[Dict[str, Any]]:
    """Discovers and loads all valid documents in the corpus directory."""
    documents = []
    for item in sorted(corpus_path.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            source_file = item / "source.md"
            meta_file = item / "meta.yaml"
            if source_file.exists() and meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = yaml.safe_load(f)
                source_text = source_file.read_text(encoding="utf-8")
                documents.append(
                    {
                        "id": meta.get("id", item.name),
                        "meta": meta,
                        "source_text": source_text,
                        "dir_path": item,
                    }
                )
    return documents


async def run_arm_a(client: GeminiLLMClient, doc: Dict[str, Any]) -> Dict[str, Any]:
    """Runs Arm A: Control (standard polish)."""
    system_prompt = load_arm_prompt("control")
    user_prompt = (
        "Please review and revise the following technical document:\n\n"
        f"{doc['source_text']}"
    )

    response = client.generate(
        prompt=user_prompt,
        system_instruction=system_prompt,
        temperature=0.2,
    )

    return {
        "arm": "control",
        "revised_text": response.text.strip(),
        "usage": response.usage.__dict__,
        "model": response.model,
    }


async def run_arm_b(client: GeminiLLMClient, doc: Dict[str, Any]) -> Dict[str, Any]:
    """Runs Arm B: Text-Only (editorial rules & rubric)."""
    system_prompt = load_arm_prompt("text_only")
    user_prompt = (
        "Please review and edit the following technical document "
        f"according to the editorial rules:\n\n{doc['source_text']}"
    )

    response = client.generate(
        prompt=user_prompt,
        system_instruction=system_prompt,
        temperature=0.2,
    )

    return {
        "arm": "text_only",
        "revised_text": response.text.strip(),
        "usage": response.usage.__dict__,
        "model": response.model,
    }


async def run_arm_c(
    client: GeminiLLMClient,
    mcp_client: DocstatsMCPClient,
    doc: Dict[str, Any],
) -> Dict[str, Any]:
    """Runs Arm C: Stats-Augmented (editorial guidance + docstats MCP live metrics)."""
    system_prompt = load_arm_prompt("stats_augmented")

    # Step 1: Run baseline analysis via docstats MCP
    logger.info(
        f"[{doc['id']}] Arm C: Calling docstats MCP tool "
        "`analyze_document` on source text..."
    )
    initial_analysis = await mcp_client.analyze_document(text=doc["source_text"])

    stats_summary = json.dumps(initial_analysis, indent=2)
    user_prompt = (
        f"Document Metadata: {json.dumps(doc['meta'])}\n\n"
        f"Initial docstats Analysis:\n```json\n{stats_summary}\n```\n\n"
        f"Source Document:\n\n{doc['source_text']}\n\n"
        "Please revise this document applying the editorial rules "
        "and resolving the flagged issues."
    )

    # Step 2: First pass generation
    resp1 = client.generate(
        prompt=user_prompt,
        system_instruction=system_prompt,
        temperature=0.2,
    )

    candidate_text = resp1.text.strip()
    tool_telemetry = [{"step": "initial_analysis", "output": initial_analysis}]

    total_prompt_tokens = resp1.usage.prompt_tokens
    total_candidate_tokens = resp1.usage.candidate_tokens
    total_tokens = resp1.usage.total_tokens
    total_latency = resp1.usage.latency_seconds

    # Step 3: Second analysis on candidate
    logger.info(
        f"[{doc['id']}] Arm C: Analyzing candidate revision via docstats MCP..."
    )
    candidate_analysis = await mcp_client.analyze_document(text=candidate_text)
    tool_telemetry.append({"step": "candidate_analysis", "output": candidate_analysis})

    final_revised_text = candidate_text

    # Step 4: Iterative refinement if tell score < 7.0
    ai_patterns = candidate_analysis.get("ai_patterns", {})
    tell_score = ai_patterns.get("ai_tell_score", 10.0)

    if tell_score < 7.0 and ai_patterns.get("flags"):
        logger.info(
            f"[{doc['id']}] Arm C: Candidate score ({tell_score}) "
            "below 7.0 floor. Running refinement loop..."
        )
        flags_json = json.dumps(ai_patterns.get("flags", []), indent=2)
        feedback_prompt = (
            f"Your candidate revision scored {tell_score}/10 on Axis B with flags:\n"
            f"{flags_json}\n\n"
            f"Candidate Text:\n\n{candidate_text}\n\n"
            "Please perform a final polish to resolve remaining tells "
            "and exceed the 7.0 floor."
        )

        resp2 = client.generate(
            prompt=feedback_prompt,
            system_instruction=system_prompt,
            temperature=0.2,
        )

        final_revised_text = resp2.text.strip()
        total_prompt_tokens += resp2.usage.prompt_tokens
        total_candidate_tokens += resp2.usage.candidate_tokens
        total_tokens += resp2.usage.total_tokens
        total_latency += resp2.usage.latency_seconds

        final_analysis = await mcp_client.analyze_document(text=final_revised_text)
        tool_telemetry.append({"step": "final_analysis", "output": final_analysis})

    usage = UsageStats(
        prompt_tokens=total_prompt_tokens,
        candidate_tokens=total_candidate_tokens,
        total_tokens=total_tokens,
        latency_seconds=round(total_latency, 3),
    )

    return {
        "arm": "stats_augmented",
        "revised_text": final_revised_text,
        "usage": usage.__dict__,
        "model": resp1.model,
        "mcp_telemetry": tool_telemetry,
    }


async def run_experiment(
    corpus_path: Path = CORPUS_DIR,
    output_base_dir: Path = RESULTS_DIR,
    model: Optional[str] = None,
    target_doc: Optional[str] = None,
) -> Path:
    """Executes the full experiment across all documents and arms."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = output_base_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    llm_client = GeminiLLMClient(model=model or "gemini-3.7-flash")
    mcp_client = DocstatsMCPClient()

    documents = load_corpus_documents(corpus_path)
    if target_doc:
        documents = [d for d in documents if d["id"] == target_doc]

    if not documents:
        logger.warning(
            f"No documents in corpus {corpus_path}. Creating placeholder run."
        )

    logger.info(
        f"Starting experiment {timestamp} with {len(documents)} document(s) "
        f"using model {llm_client.model}..."
    )

    manifest = {
        "run_id": timestamp,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": llm_client.model,
        "auth_mode": llm_client.auth_mode,
        "document_count": len(documents),
        "documents": [],
    }

    for doc in documents:
        doc_id = doc["id"]
        logger.info(f"Processing document '{doc_id}'...")
        doc_out_dir = run_dir / doc_id
        doc_out_dir.mkdir(parents=True, exist_ok=True)

        (doc_out_dir / "source.md").write_text(doc["source_text"], encoding="utf-8")
        (doc_out_dir / "meta.yaml").write_text(yaml.dump(doc["meta"]), encoding="utf-8")

        # Arm A
        logger.info(f"[{doc_id}] Executing Arm A (Control)...")
        res_a = await run_arm_a(llm_client, doc)
        (doc_out_dir / "arm_a.md").write_text(res_a["revised_text"], encoding="utf-8")

        # Arm B
        logger.info(f"[{doc_id}] Executing Arm B (Text-Only)...")
        res_b = await run_arm_b(llm_client, doc)
        (doc_out_dir / "arm_b.md").write_text(res_b["revised_text"], encoding="utf-8")

        # Arm C
        logger.info(f"[{doc_id}] Executing Arm C (Stats-Augmented)...")
        res_c = await run_arm_c(llm_client, mcp_client, doc)
        (doc_out_dir / "arm_c.md").write_text(res_c["revised_text"], encoding="utf-8")

        telemetry = {
            "document_id": doc_id,
            "arms": {
                "control": {k: v for k, v in res_a.items() if k != "revised_text"},
                "text_only": {k: v for k, v in res_b.items() if k != "revised_text"},
                "stats_augmented": {
                    k: v for k, v in res_c.items() if k != "revised_text"
                },
            },
        }

        (doc_out_dir / "telemetry.json").write_text(
            json.dumps(telemetry, indent=2), encoding="utf-8"
        )
        manifest["documents"].append(doc_id)

    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    logger.info(f"Experiment completed successfully. Results saved to: {run_dir}")
    return run_dir


def main():
    """CLI entry point for running evaluation experiments."""
    parser = argparse.ArgumentParser(
        description="Run Docstats Multi-Arm A/B Experiment."
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=CORPUS_DIR,
        help="Path to corpus directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RESULTS_DIR,
        help="Path to results directory",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-3.7-flash",
        help="Model ID to evaluate",
    )
    parser.add_argument(
        "--doc", type=str, default=None, help="Target specific document ID"
    )

    args = parser.parse_args()
    asyncio.run(
        run_experiment(
            corpus_path=args.corpus_dir,
            output_base_dir=args.output_dir,
            model=args.model,
            target_doc=args.doc,
        )
    )


if __name__ == "__main__":
    main()
