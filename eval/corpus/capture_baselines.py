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

"""Computes and captures baseline docstats metrics for all corpus drafts."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from metrics import analyze_document_logic  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

CORPUS_DIR = Path(__file__).resolve().parent


async def capture_corpus_baselines(
    corpus_dir: Path = CORPUS_DIR,
) -> List[Dict[str, Any]]:
    """Runs analyze_document across all corpus folders and writes baseline.json."""
    results = []

    print("\n" + "=" * 90)
    print("                    CORPUS BASELINE DIAGNOSTIC SUMMARY")
    print("=" * 90)
    hdr = (
        f"{'Document ID':<22} | {'Tier':<16} | {'FK Grade':<9} "
        f"| {'AI Score':<9} | {'Tells':<6} | {'Status':<8}"
    )
    print(hdr)
    print("-" * 90)

    for item in sorted(corpus_dir.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            source_file = item / "source.md"
            meta_file = item / "meta.yaml"

            if source_file.exists() and meta_file.exists():
                source_text = source_file.read_text(encoding="utf-8")
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = yaml.safe_load(f)

                analysis = await analyze_document_logic(
                    source_text, src_desc=f"corpus/{item.name}"
                )
                analysis_dict = analysis.model_dump()

                # Save baseline.json
                baseline_file = item / "baseline.json"
                baseline_file.write_text(
                    json.dumps(analysis_dict, indent=2), encoding="utf-8"
                )

                readability = analysis_dict["readability"]
                ai_patterns = analysis_dict["ai_patterns"]

                fk_grade = readability.get("flesch_kincaid_grade", 0.0)
                ai_score = ai_patterns.get("ai_tell_score", 10.0)
                total_tells = ai_patterns.get("total_tells", 0)
                tier = meta.get("source_tier", "unknown")

                status = "PASS" if ai_score >= 7.0 else "FLAGGED"

                row = (
                    f"{item.name:<22} | {tier:<16} | {fk_grade:<9.1f} "
                    f"| {ai_score:<9.2f} | {total_tells:<6} | {status:<8}"
                )
                print(row)

                results.append(
                    {
                        "id": item.name,
                        "tier": tier,
                        "meta": meta,
                        "analysis": analysis_dict,
                    }
                )

    print("=" * 90 + "\n")
    logger.info(f"Captured baselines for {len(results)} corpus document(s).")
    return results


def main():
    """CLI entry point for capturing corpus baselines."""
    parser = argparse.ArgumentParser(
        description="Compute and capture baseline metrics for all corpus drafts."
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=CORPUS_DIR,
        help="Corpus directory path",
    )
    args = parser.parse_args()
    asyncio.run(capture_corpus_baselines(args.corpus_dir))


if __name__ == "__main__":
    main()
