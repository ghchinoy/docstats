# Indexing High-Volume Event Logs in PostgreSQL: B-Tree vs. BRIN vs. GIN

High-volume event logging requires balancing write throughput, disk consumption, and query latency. Because default B-Tree indexes carry heavy write overhead on append-only workloads, selecting the right index structure depends directly on table access patterns and physical data layout.

---

### 1. BRIN for Monotonic Sequences (`created_at`, `id`)
* **Use Case:** Time-range queries and date filters on append-only data (for example, `WHERE created_at >= NOW() - INTERVAL '1 hour'`).
* **Mechanism:** Block Range Indexes (BRIN) store summary metadata—the minimum and maximum values—for physical disk block ranges rather than indexing individual rows.
* **Trade-offs:** Consumes less than 1% of the space of a standard B-Tree with negligible write overhead. It requires data to remain physically sorted by the indexed column on disk.
```sql
CREATE INDEX idx_events_created_at ON events USING BRIN (created_at);
```

### 2. GIN for Semi-Structured Metadata (`payload`, `tags`)
* **Use Case:** Containment and key-existence queries on `JSONB` columns (for example, `WHERE payload @> '{"status_code": 500}'`).
* **Mechanism:** Generalized Inverted Indexes (GIN) map individual internal keys and values to row pointers.
* **Trade-offs:** Accelerates document filtering, but increases write amplification and disk usage. Use the `jsonb_path_ops` operator class to reduce index size when querying strictly with the `@>` operator.
```sql
CREATE INDEX idx_events_payload ON events USING GIN (payload jsonb_path_ops);
```

### 3. B-Tree for High-Cardinality Point Lookups (`uuid`, `trace_id`)
* **Use Case:** Exact-match queries on unique, non-sequential identifiers (for example, `WHERE trace_id = '...'`).
* **Mechanism:** Self-balancing search trees provide $O(\log N)$ lookup performance across arbitrary value distributions.
* **Trade-offs:** Delivers fast point lookups, but incurs substantial memory pressure and disk I/O during heavy ingestion. Reserve B-Trees only for columns requiring strict uniqueness or high-cardinality point queries.

---

### Decision Matrix

| Column Pattern | Recommended Index | Ingestion Overhead | Storage Footprint |
| :--- | :--- | :--- | :--- |
| Chronological Timestamp | **BRIN** | Very Low | Minimal (~KB to MB) |
| Dynamic `JSONB` Payload | **GIN (`jsonb_path_ops`)** | High | Large |
| Random UUID / Trace ID | **B-Tree** | Medium–High | Large |