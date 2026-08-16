# Indexing High-Volume Event Logs in PostgreSQL: B-Tree vs. BRIN vs. GIN

High-volume event logging requires balancing write throughput against query performance and disk usage. Select index types based on physical disk layout and access patterns.

---

### 1. BRIN for Monotonic Sequences (`created_at`, `id`)
* **Use Case:** Range queries and filters on append-only sequential data (e.g., `WHERE created_at >= NOW() - INTERVAL '1 hour'`).
* **Mechanism:** BRIN (Block Range Index) stores minimum and maximum values for physical page ranges on disk rather than indexing individual rows.
* **Trade-offs:** Consumes less than 1% of the storage required by a B-Tree and adds minimal write overhead, but query efficiency drops if data is not physically clustered by the indexed column.
```sql
CREATE INDEX idx_events_created_at ON events USING BRIN (created_at);
```

### 2. GIN for Semi-Structured Metadata (`payload`, `tags`)
* **Use Case:** Containment queries on semi-structured attributes (e.g., `WHERE payload @> '{"status_code": 500}'`).
* **Mechanism:** GIN (Generalized Inverted Index) maps keys and nested values to heap tuple locations.
* **Trade-offs:** Enables fast document searches but incurs substantial write amplification. Use the `jsonb_path_ops` operator class to reduce index size and optimize for the `@>` operator.
```sql
CREATE INDEX idx_events_payload ON events USING GIN (payload jsonb_path_ops);
```

### 3. B-Tree for High-Cardinality Point Lookups (`uuid`, `trace_id`)
* **Use Case:** Exact lookups on unordered, unique identifiers (e.g., `WHERE trace_id = '...'`).
* **Mechanism:** Self-balancing search tree ($O(\log N)$ point lookups).
* **Trade-offs:** Delivers low-latency point reads, but imposes significant write I/O and buffer cache overhead on high-ingestion tables.

---

### Decision Matrix

| Column Pattern | Recommended Index | Write Impact | Storage Footprint |
| :--- | :--- | :--- | :--- |
| Chronological Timestamp | **BRIN** | Very Low | Minimal (~KB–MB) |
| Dynamic `JSONB` Payload | **GIN (`jsonb_path_ops`)** | High | Large |
| Random UUID / Trace ID | **B-Tree** | Medium–High | Large |