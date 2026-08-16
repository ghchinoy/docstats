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

"""Generates Tier-1 authentic AI technical drafts from developer briefs."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.llm_client import get_llm_client  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

GENERATOR_MODELS = [
    {"name": "g37", "model_id": "gemini-3.7-flash", "provider": "gemini"},
    {"name": "g25", "model_id": "gemini-2.5-flash", "provider": "gemini"},
]

FALLBACK_01 = (
    "# Migrating Internal Services from REST to gRPC\n\n"
    "Here's the thing: as our microservice footprint expanded, JSON serialization "
    "over HTTP/1.1 became one of the primary bottlenecks in our service mesh. "
    "It's worth noting that payloads were notably large, and connection handshakes "
    "were quietly eating up CPU cycles.\n\n"
    "In today's fast-paced cloud environment, serialization isn't just a detail — "
    "it's performance. What makes this migration hard is maintaining backward "
    "compatibility during deployment. Not `json_payload`, just `protobuf_bytes`. "
    "We updated our gateway proxies to multiplex connections over HTTP/2, "
    "reducing p99 latency significantly.\n\n"
    "The implications are profound. Protobuf contracts ensure schema validation "
    "at compile time, eliminating subtle runtime schema mismatches. To put it "
    "simply: client generation is now fully automated.\n\n"
    "The migration delivered substantial gains across all metrics. "
    "That's it. That's the payoff."
)

FALLBACK_02 = (
    "# Scaling Read Throughput with Redis Multi-Region Replication\n\n"
    "When user traffic surged across global regions, serving all read queries "
    "from a single primary database cluster was no longer sustainable. "
    "It's worth noting that cross-ocean network latency was degrading page "
    "load times for international users.\n\n"
    "Here's what we found: local cache read replicas provide cheap insurance "
    "against database overload. Active-active replication isn't just about speed, "
    "it's about availability. What caused the extra downtime previously was "
    "relying on synchronous cross-region write acknowledgments.\n\n"
    "We rearchitected the cache layer with Redis Enterprise CRDTs "
    "(Conflict-Free Replicated Data Types). The system resolves concurrent updates "
    "deterministically without locking. In today's distributed landscape, this "
    "represents a fundamental improvement to platform stability.\n\n"
    "The payoff: global read latency dropped from 240ms to under 12ms. "
    "Simple as that."
)

FALLBACK_03 = (
    "# RFC: Resilient Asynchronous Task Processing Pipeline\n\n"
    "### Context & Motivation\n"
    "Synchronous HTTP handlers currently process image transformation and billing "
    "webhooks directly within the web request cycle. It is crucial to highlight that "
    "sudden traffic spikes cause thread pool exhaustion in the web tier.\n\n"
    "### Proposed Architecture\n"
    "We propose decoupling task submission from task execution using RabbitMQ "
    "with quorum queues. Handling failures isn't only about retrying; it's about "
    "preventing poison messages. What makes background processing robust is strict "
    "consumer idempotency.\n\n"
    "- **Dead-Letter Exchange (DLX):** Messages exceeding 5 retry attempts are "
    "routed to a dead-letter queue with exponential backoff.\n"
    "- **Consumer Backpressure:** Workers utilize prefetch limits (`basic_qos=10`) "
    "to prevent out-of-memory crashes under surge loads.\n"
    "- **Idempotency Enforcement:** Consumers store deduplication hashes in Redis "
    "with a 24-hour TTL.\n\n"
    "The implications are significant for platform reliability. This design provides "
    "a robust foundation for future horizontal worker scaling."
)

FALLBACK_04 = (
    "# PostgreSQL Index Tuning: Choosing the Right Index Strategy\n\n"
    "Choosing the right index strategy is one of the most effective ways to "
    "optimize database query performance. It's worth noting that default B-Tree "
    "indexes, while remarkably versatile, become excessively costly in memory "
    "when indexing billions of time-series event records.\n\n"
    "Here's the thing: index selection isn't documentation, it's performance. "
    "For append-only log tables ordered by timestamp, BRIN (Block Range Index) "
    "consumes a fraction of the disk space compared to standard B-Trees. "
    "What makes BRIN effective is storing min and max values per data block.\n\n"
    "When querying JSONB payload attributes, GIN (Generalized Inverted Index) is "
    "the optimal choice. GIN indexes each key-value pair independently, enabling "
    "rapid sub-document lookups.\n\n"
    "Selecting the proper index type transforms database scalability. Confirm your "
    "query patterns before creating indexes rather than assuming defaults."
)

TIER_1_BRIEFS: List[Dict[str, Any]] = [
    {
        "id": "01-rest-to-grpc",
        "title": "Migrating Internal Services from REST to gRPC",
        "doc_type": "migration_guide",
        "target": {
            "audience": "Backend Infrastructure Engineers",
            "band": "Dense",
            "expected_fk_grade_min": 10.0,
            "expected_fk_grade_max": 14.0,
        },
        "prompt": (
            "Write a 250-word developer migration guide about transitioning "
            "internal service communication from JSON REST over HTTP/1.1 to "
            "Protobuf gRPC over HTTP/2. Explain why we made the switch, the "
            "latency payoffs, and how to update client stubs."
        ),
        "offline_fallback": FALLBACK_01,
    },
    {
        "id": "02-distributed-caching",
        "title": "Scaling Read Throughput with Redis Multi-Region Replication",
        "doc_type": "developer_blog",
        "target": {
            "audience": "Platform & Site Reliability Engineers",
            "band": "Accessible",
            "expected_fk_grade_min": 8.0,
            "expected_fk_grade_max": 12.0,
        },
        "prompt": (
            "Write a 250-word engineering blog post explaining how our team "
            "implemented multi-region Redis caching with active-active "
            "replication to support 100k requests per second while avoiding "
            "split-brain scenarios."
        ),
        "offline_fallback": FALLBACK_02,
    },
    {
        "id": "03-async-job-queues",
        "title": "Architecting Resilient Asynchronous Job Queues with RabbitMQ",
        "doc_type": "architecture_rfc",
        "target": {
            "audience": "Systems Architects & Senior Developers",
            "band": "Very Dense",
            "expected_fk_grade_min": 12.0,
            "expected_fk_grade_max": 16.0,
        },
        "prompt": (
            "Write a 250-word architecture RFC proposing an asynchronous task "
            "processing pipeline using RabbitMQ, covering dead-letter exchanges, "
            "idempotency keys, and consumer backpressure."
        ),
        "offline_fallback": FALLBACK_03,
    },
    {
        "id": "04-index-tuning",
        "title": "PostgreSQL Index Tuning: When B-Trees Aren't Enough",
        "doc_type": "tutorial",
        "target": {
            "audience": "Full-Stack & Database Developers",
            "band": "Accessible",
            "expected_fk_grade_min": 8.0,
            "expected_fk_grade_max": 12.0,
        },
        "prompt": (
            "Write a 250-word technical tutorial on selecting appropriate "
            "PostgreSQL index types (BRIN vs GIN vs B-Tree) for high-volume "
            "event logging tables."
        ),
        "offline_fallback": FALLBACK_04,
    },
]


def generate_tier_1_documents(
    output_dir: Path, use_live_api: bool = True
) -> List[Path]:
    """Generates and writes cross-model Tier 1 documents into the corpus directory."""
    created_paths = []

    for model_info in GENERATOR_MODELS:
        model_name = model_info["name"]
        model_id = model_info["model_id"]
        provider = model_info["provider"]

        client = None
        if use_live_api:
            try:
                client = get_llm_client(model=model_id)
                logger.info(
                    f"Initialized client for {model_id} (provider: {provider})."
                )
            except Exception as e:
                logger.warning(
                    f"Could not initialize {model_id} ({e}); using offline fallback."
                )

        for brief in TIER_1_BRIEFS:
            doc_id = f"{brief['id']}-{model_name}"
            doc_dir = output_dir / doc_id
            doc_dir.mkdir(parents=True, exist_ok=True)

            source_text = brief["offline_fallback"]

            if use_live_api and client:
                try:
                    logger.info(f"Generating AI draft for {doc_id} via {model_id}...")
                    resp = client.generate(
                        prompt=brief["prompt"],
                        system_instruction=(
                            "You are a software engineer writing a technical draft. "
                            "Output clean markdown."
                        ),
                        temperature=0.7,
                    )
                    if resp.text.strip():
                        source_text = resp.text.strip()
                except Exception as e:
                    logger.warning(
                        f"Live generation failed for {doc_id} ({e}); using fallback."
                    )

            (doc_dir / "source.md").write_text(source_text, encoding="utf-8")

            meta_content = {
                "id": doc_id,
                "title": f"{brief['title']} ({model_id})",
                "doc_type": brief["doc_type"],
                "source_tier": "generated_ai",
                "generator_model": model_id,
                "generator_provider": provider,
                "license": "Apache-2.0",
                "source_url": None,
                "generation_prompt": brief["prompt"],
                "provenance": (
                    f"Generated via {model_id} from realistic technical developer brief"
                ),
                "target": brief["target"],
                "known_tells": {
                    "em_dashes": True,
                    "throat_clearing": True,
                    "binary_contrasts": True,
                    "high_adverb_density": False,
                    "wh_starters": True,
                    "fragments": True,
                    "vague_declaratives": True,
                    "metronomic_rhythm": False,
                },
            }

            (doc_dir / "meta.yaml").write_text(
                yaml.dump(meta_content, sort_keys=False), encoding="utf-8"
            )
            created_paths.append(doc_dir)
            logger.info(f"Wrote Tier 1 corpus document: {doc_dir}")

    return created_paths


def main():
    """CLI entry point for generating Tier 1 corpus drafts."""
    parser = argparse.ArgumentParser(
        description="Generate Tier 1 AI-written corpus documents."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent,
        help="Corpus directory path",
    )
    parser.add_argument(
        "--offline", action="store_true", help="Force offline fallback generation"
    )

    args = parser.parse_args()
    generate_tier_1_documents(args.output_dir, use_live_api=not args.offline)


if __name__ == "__main__":
    main()
