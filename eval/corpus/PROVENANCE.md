# Evaluation Corpus Provenance & Characterization

This document records the origin, licensing, target audience, and baseline characteristics for all documents in `eval/corpus/`.

---

## Corpus Composition Matrix (10 Documents)

| ID | Title | Doc Type | Source Tier | License | Target Band | Baseline FK Grade | Baseline AI Score | Tell Profile |
|---|---|---|---|---|---|---|---|---|
| `01-rest-to-grpc` | Migrating Internal Services from REST to gRPC | `migration_guide` | `generated_ai` | Apache-2.0 | Dense (10–14) | 12.1 | 10.00 | Clean schema migration |
| `02-distributed-caching` | Scaling Read Throughput with Redis Multi-Region Replication | `developer_blog` | `generated_ai` | Apache-2.0 | Accessible (8–12) | 15.2 | 9.34 | High-throughput caching |
| `03-async-job-queues` | Resilient Asynchronous Task Processing Pipeline | `architecture_rfc` | `generated_ai` | Apache-2.0 | Very Dense (12–16) | 14.3 | 10.00 | Dead-letter queues & backpressure |
| `04-index-tuning` | PostgreSQL Index Tuning: When B-Trees Aren't Enough | `tutorial` | `generated_ai` | Apache-2.0 | Accessible (8–12) | 11.8 | 9.73 | BRIN vs GIN vs B-Tree |
| `05-sample-migration` | Engine Migration: Transitioning to Server Mode | `migration_guide` | `synthetic_curated` | Apache-2.0 | Dense (10–14) | 11.3 | 3.20 | Throat-clearing, binary contrast, fragments |
| `06-sdk-pagination` | Handling Infinite Pagination in Developer SDKs | `developer_blog` | `synthetic_curated` | Apache-2.0 | Accessible (8–12) | 15.6 | 0.00 | Excessive em dashes, -ly adverbs, throat-clearing |
| `07-observability-slop` | RFC: Enterprise Distributed Tracing Standards | `architecture_rfc` | `synthetic_curated` | Apache-2.0 | Very Dense (12–16) | 12.4 | 7.28 | Vague declaratives, Wh- assertions, fragments |
| `08-fastapi-clean` | Dependencies in FastAPI | `tutorial` | `public_licensed` | MIT | Accessible (7–11) | 10.4 | 10.00 | Official FastAPI docs (Sebastián Ramírez) |
| `09-sqlite-wal-guide` | Write-Ahead Logging in SQLite | `developer_blog` | `public_licensed` | Public Domain | Dense (10–14) | 10.9 | 10.00 | Official SQLite Consortium documentation |
| `10-standard-readme` | Standard Readme Specification | `readme` | `public_licensed` | CC0-1.0 | Accessible (7–11) | 12.4 | 10.00 | Standard Readme open specification |

---

## Detailed Document Records

### 1. `01-rest-to-grpc`
- **Source Tier:** `generated_ai`
- **Generator Model:** Gemini 3.7 Flash (`eval/corpus/generate_drafts.py`)
- **Brief:** Transitioning internal services from JSON REST over HTTP/1.1 to Protobuf gRPC over HTTP/2, highlighting latency reduction and schema validation.
- **License:** Apache-2.0

### 2. `02-distributed-caching`
- **Source Tier:** `generated_ai`
- **Generator Model:** Gemini 3.7 Flash (`eval/corpus/generate_drafts.py`)
- **Brief:** Active-active multi-region Redis caching with Conflict-Free Replicated Data Types (CRDTs) to support 100k rps without split-brain anomalies.
- **License:** Apache-2.0

### 3. `03-async-job-queues`
- **Source Tier:** `generated_ai`
- **Generator Model:** Gemini 3.7 Flash (`eval/corpus/generate_drafts.py`)
- **Brief:** Architecture RFC decoupling web request cycles from task processing via RabbitMQ quorum queues, dead-letter exchanges, and consumer backpressure.
- **License:** Apache-2.0

### 4. `04-index-tuning`
- **Source Tier:** `generated_ai`
- **Generator Model:** Gemini 3.7 Flash (`eval/corpus/generate_drafts.py`)
- **Brief:** Database tutorial comparing PostgreSQL index types (BRIN for time-series logs, GIN for JSONB payloads, B-Tree for standard lookups).
- **License:** Apache-2.0

### 5. `05-sample-migration`
- **Source Tier:** `synthetic_curated`
- **Provenance:** Hand-authored synthetic draft intentionally saturated with multiple AI writing tells: throat-clearing openers ("Here's the thing:", "It's worth noting that"), binary contrast frames ("Not embedded_engine, just server_daemon"), and staccato fragments ("That's it. That's the thing.").
- **License:** Apache-2.0

### 6. `06-sdk-pagination`
- **Source Tier:** `synthetic_curated`
- **Provenance:** Hand-authored synthetic draft embedding heavy em dash clustering in prose, high-offender adverbs ("fundamentally", "genuinely", "quietly", "deeply"), and throat-clearing labels ("The payoff:").
- **License:** Apache-2.0

### 7. `07-observability-slop`
- **Source Tier:** `synthetic_curated`
- **Provenance:** Hand-authored architecture draft embedding hollow significance phrases ("In today's fast-paced landscape", "The implications are significant", "Serves as a testament to"), Wh- declarative assertions ("What makes...", "What caused..."), and metronomic sentence structures.
- **License:** Apache-2.0

### 8. `08-fastapi-clean`
- **Source Tier:** `public_licensed`
- **Origin / Source URL:** https://fastapi.tiangolo.com/tutorial/dependencies/
- **Author:** Sebastián Ramírez (tiangolo)
- **License:** MIT License
- **Purpose:** High-quality, human-authored technical tutorial serving as an over-correction control.

### 9. `09-sqlite-wal-guide`
- **Source Tier:** `public_licensed`
- **Origin / Source URL:** https://www.sqlite.org/wal.html
- **Author:** SQLite Consortium (D. Richard Hipp et al.)
- **License:** Public Domain
- **Purpose:** Authoritative systems documentation serving as a Dense technical baseline.

### 10. `10-standard-readme`
- **Source Tier:** `public_licensed`
- **Origin / Source URL:** https://github.com/RichardLitt/standard-readme
- **Author:** Richard Littauer
- **License:** CC0 1.0 Universal / Public Domain
- **Purpose:** Open standard README specification serving as a structural baseline.
