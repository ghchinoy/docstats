# Indexing High-Volume Event Logs in PostgreSQL: B-Tree vs. BRIN vs. GIN

High-volume event logging requires balancing query latency, storage overhead, and ingestion throughput. Selecting the optimal PostgreSQL index type depends primarily on data ordering and your dominant query patterns.

---

### 1. BRIN for Monotonic Sequences (`created_at`, `id`)
* **Use Case:** Range scans and time-window filters on append-only data (e.g., `WHERE created_at >= NOW() - INTERVAL '1 hour'`).
* **Mechanism:** A Block Range Index (BRIN) records the minimum and maximum values for physical block ranges on disk rather than indexing each individual row.
* **Trade-offs:** Provides an extremely small storage footprint (<1% the size of a standard B-Tree) and near-zero write overhead, but requires data to correlate closely with physical disk order.

```sql
CREATE INDEX idx_events_created_at ON events USING BRIN (created_at);
```

### 2. GIN for Semi-Structured Metadata (`payload`, `tags`)
* **Use Case:** Containment and key-value lookups on semi-structured attributes (e.g., `WHERE payload @> '{"status_code": 500}'`).
* **Mechanism:** A Generalized Inverted Index (GIN) maps individual internal keys and elements to their matching row locations.
* **Trade-offs:** Delivers fast document searches at the expense of significant write amplification and maintenance overhead. Using the `jsonb_path_ops` operator class reduces index size and optimizes performance specifically for `@>` containment queries.

```sql
CREATE INDEX idx_events_payload ON events USING GIN (payload jsonb_path_ops);
```

### 3. B-Tree for High-Cardinality Point Lookups (`uuid`, `trace_id`)
* **Use Case:** Exact-match lookups on unordered, unique identifiers (e.g., `WHERE trace_id = '...'`).
* **Mechanism:** A standard self-balancing search tree providing $O(\log N)$ lookup performance.
* **Trade-offs:** Delivers predictable, sub-millisecond point reads, but incurs high write I/O, memory usage, and storage overhead. B-Tree index creation should be limited on high-throughput write paths.

```sql
CREATE INDEX idx_events_trace_id ON events USING BTREE (trace_id);
```

---

### Decision Matrix

| Column Pattern | Recommended Index | Write Overhead | Storage Footprint | Primary Query Pattern |
| :--- | :--- | :--- | :--- | :--- |
| Chronological / Monotonic Timestamp | **BRIN** | Very Low | Minimal (~KB–MB) | Range scans (`>`, `<`, `BETWEEN`) |
| Dynamic `JSONB` Payload | **GIN (`jsonb_path_ops`)** | High | Large | JSON containment (`@>`) |
| Random UUID / Trace ID | **B-Tree** | Medium–High | Large | Exact point lookup (`=`) |