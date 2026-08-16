# Indexing High-Volume Event Logs in PostgreSQL: B-Tree vs. BRIN vs. GIN

High-volume event logging forces trade-offs. You must balance query speed against storage size and write throughput. Match your PostgreSQL index to your data ordering and query patterns.

---

### 1. BRIN for Monotonic Sequences (`created_at`, `id`)
* **Use Case:** Range queries and filters on append-only sequential data (e.g., `WHERE created_at >= NOW() - INTERVAL '1 hour'`).
* **Mechanism:** BRIN (Block Range Index) stores minimum and maximum values for physical block ranges on disk.
* **Trade-offs:** BRIN consumes <1% of the storage of a B-Tree and adds minimal write overhead. The indexed column must dictate the physical clustering of data on disk.
```sql
CREATE INDEX idx_events_created_at ON events USING BRIN (created_at);
```

### 2. GIN for Semi-Structured Metadata (`payload`, `tags`)
* **Use Case:** Containment queries on semi-structured attributes (e.g., `WHERE payload @> '{"status_code": 500}'`).
* **Mechanism:** GIN (Generalized Inverted Index) maps individual elements to row locations.
* **Trade-offs:** GIN accelerates document searches but causes high write amplification. Specify the `jsonb_path_ops` operator class to reduce index size and optimize for the `@>` operator.
```sql
CREATE INDEX idx_events_payload ON events USING GIN (payload jsonb_path_ops);
```

### 3. B-Tree for High-Cardinality Point Lookups (`uuid`, `trace_id`)
* **Use Case:** Exact lookups on unordered, unique identifiers (e.g., `WHERE trace_id = '...'`).
* **Mechanism:** Traditional self-balancing tree ($O(\log N)$ search).
* **Trade-offs:** B-Trees provide fast point reads but consume significant write I/O and memory. Restrict B-Tree usage on write-intensive tables.

---

### Decision Matrix

| Column Pattern | Recommended Index | Write Impact | Storage Footprint |
| :--- | :--- | :--- | :--- |
| Chronological Timestamp | **BRIN** | Very Low | Minimal (~KB–MB) |
| Dynamic `JSONB` Payload | **GIN (`jsonb_path_ops`)** | High | Large |
| Random UUID / Trace ID | **B-Tree** | Medium–High | Large |