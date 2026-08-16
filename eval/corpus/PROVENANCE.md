# Evaluation Corpus Provenance & Characterization

This document records the origin, licensing, target audience, and baseline characteristics for all 14 documents in `eval/corpus/`.

---

## Corpus Composition Matrix (14 Documents across 3 Tiers)

| ID | Title | Doc Type | Source Tier | Generator | License | Target Band | Baseline FK Grade | Baseline AI Score | Tell Profile |
|---|---|---|---|---|---|---|---|---|---|
| `01-rest-to-grpc-g37` | REST to gRPC Migration (Gemini 3.7) | `migration_guide` | `generated_ai` | `gemini-3.7-flash` | Apache-2.0 | Dense (10–14) | 13.5 | 10.00 | Clean schema migration |
| `01-rest-to-grpc-g25` | REST to gRPC Migration (Gemini 2.5) | `migration_guide` | `generated_ai` | `gemini-2.5-flash` | Apache-2.0 | Dense (10–14) | 13.5 | 10.00 | Clean schema migration |
| `02-distributed-caching-g37` | Multi-Region Redis Caching (Gemini 3.7) | `developer_blog` | `generated_ai` | `gemini-3.7-flash` | Apache-2.0 | Accessible (8–12) | 15.9 | 9.98 | High-throughput caching |
| `02-distributed-caching-g25` | Multi-Region Redis Caching (Gemini 2.5) | `developer_blog` | `generated_ai` | `gemini-2.5-flash` | Apache-2.0 | Accessible (8–12) | 16.1 | 8.96 | High-throughput caching |
| `03-async-job-queues-g37` | Resilient Task Processing (Gemini 3.7) | `architecture_rfc` | `generated_ai` | `gemini-3.7-flash` | Apache-2.0 | Very Dense (12–16) | 15.5 | 10.00 | Dead-letter queues & backpressure |
| `03-async-job-queues-g25` | Resilient Task Processing (Gemini 2.5) | `architecture_rfc` | `generated_ai` | `gemini-2.5-flash` | Apache-2.0 | Very Dense (12–16) | 15.3 | 9.24 | Dead-letter queues & backpressure |
| `04-index-tuning-g37` | PostgreSQL Index Tuning (Gemini 3.7) | `tutorial` | `generated_ai` | `gemini-3.7-flash` | Apache-2.0 | Accessible (8–12) | 11.8 | 9.73 | BRIN vs GIN vs B-Tree |
| `04-index-tuning-g25` | PostgreSQL Index Tuning (Gemini 2.5) | `tutorial` | `generated_ai` | `gemini-2.5-flash` | Apache-2.0 | Accessible (8–12) | 12.2 | 8.25 | BRIN vs GIN vs B-Tree |
| `05-sample-migration` | Engine Migration: Transitioning to Server Mode | `migration_guide` | `synthetic_curated` | Human Author | Apache-2.0 | Dense (10–14) | 11.3 | 3.20 | Throat-clearing, binary contrast |
| `06-sdk-pagination` | Handling Infinite Pagination in Developer SDKs | `developer_blog` | `synthetic_curated` | Human Author | Apache-2.0 | Accessible (8–12) | 15.6 | 0.00 | Excessive em dashes, -ly adverbs |
| `07-observability-slop` | RFC: Enterprise Distributed Tracing Standards | `architecture_rfc` | `synthetic_curated` | Human Author | Apache-2.0 | Very Dense (12–16) | 12.4 | 7.28 | Vague declaratives, Wh- starts |
| `08-fastapi-clean` | Dependencies in FastAPI | `tutorial` | `public_licensed` | Tiangolo | MIT | Accessible (7–11) | 10.4 | 10.00 | Official FastAPI docs (Sebastián Ramírez) |
| `09-sqlite-wal-guide` | Write-Ahead Logging in SQLite | `developer_blog` | `public_licensed` | SQLite Team | Public Domain | Dense (10–14) | 10.9 | 10.00 | Official SQLite Consortium docs |
| `10-standard-readme` | Standard Readme Specification | `readme` | `public_licensed` | R. Littauer | CC0-1.0 | Accessible (7–11) | 12.4 | 10.00 | Standard Readme open specification |
