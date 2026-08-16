# Indexing High-Volume Event Logs in PostgreSQL: B-Tree vs. BRIN vs. GIN

High-volume event logging demands a strict balance between query latency, storage footprint, and ingestion throughput. Choosing the right PostgreSQL index depends directly on data ordering and query patterns.

---

### 1. BRIN for Monotonic Sequences (`created_at`, `id`)
* **Use Case:** Range queries and filters on append-only sequential data (e.g., `WHERE created_at >= NOW() - INTERVAL '1 hour'`).
* **Mechanism:** BRIN (Block Range Index) stores the minimum and maximum values for physical block ranges on disk rather than indexing every row.
* **Trade-offs:** Offers a negligible storage footprint (<1% of B-Tree) and near-zero write overhead, but requires data to be physically clustered by the indexed column.
```sql
CREATE INDEX idx_events_created_at ON events USING BRIN (created_at);
```

### 2. GIN for Semi-Structured Metadata (`payload`, `tags`)
* **Use Case:** Containment queries on semi-structured attributes (e.g., `WHERE payload @> '{"status_code": 500}'`).
* **Mechanism:** GIN (Generalized Inverted Index) maps individual elements/keys to row locations.
* **Trade-offs:** Enables fast document searches but incurs high write amplification. Use the `jsonb_path_ops` operator class to reduce index size and optimize specifically for the `@>` operator.
```sql
CREATE INDEX idx_events_payload ON events USING GIN (payload jsonb_path_ops);
```

### 3. B-Tree for High-Cardinality Point Lookups (`uuid`, `trace_id`)
* **Use Case:** Exact lookups on unordered, unique identifiers (e.g., `WHERE trace_id = '...'`).
* **Mechanism:** Traditional self-balancing tree ($O(\log N)$ search).
* **Trade-offs:** Fast point reads, but heavy on write I/O and RAM. Minimize B-Tree usage on write-intensive tables.

---

### Decision Matrix

| Column Pattern | Recommended Index | Write Impact | Storage Footprint |
| :--- | :--- | :--- | :--- |
| Chronological Timestamp | **BRIN** | Very Low | Minimal (~KB–MB) |
| Dynamic `JSONB` Payload | **GIN (`jsonb_path_ops`)** | High | Large |
| Random UUID / Trace ID | **B-Tree** | Medium–High | Large |