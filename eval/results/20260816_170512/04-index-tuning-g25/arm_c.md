```markdown
# PostgreSQL Index Tuning: B-Tree, BRIN, and GIN

High-volume event logging requires balancing query speed against storage footprint and write throughput. PostgreSQL provides distinct index types tailored to specific storage structures and access patterns.

### B-Tree: Precision Lookups and High Cardinality
B-Tree is the default PostgreSQL index. It excels at point lookups, unique constraints, and exact matches on high-cardinality columns (such as `user_id` or `event_uuid`):

```sql
SELECT * FROM event_logs WHERE event_uuid = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
```

However, B-Trees grow linearly with row count. On tables with billions of rows, a single B-Tree index often consumes hundreds of gigabytes, which strains memory and degrades ingestion rates.

### BRIN: Append-Only Timestamps
Block Range Indexes (BRIN) target columns naturally sorted on physical disk, such as sequential IDs or `created_at` timestamps in append-only log tables. Instead of indexing individual rows, BRIN stores the minimum and maximum values across blocks of pages (defaulting to 128 disk pages).

```sql
CREATE INDEX idx_logs_created_at_brin ON event_logs USING BRIN (created_at);
```

When executing range queries like `WHERE created_at >= NOW() - INTERVAL '7 days'`, the engine skips irrelevant disk blocks. A BRIN index often consumes less than 1% of the storage space required by a B-Tree, dramatically reducing write overhead.

### GIN: Semi-Structured JSONB and Arrays
Generalized Inverted Indexes (GIN) unpack complex structures and map internal elements back to row locations. Use GIN for array columns and JSONB documents:

```sql
SELECT * FROM event_logs WHERE metadata @> '{"status": "failure"}';
SELECT * FROM event_logs WHERE tags @> ARRAY['critical'];
```

GIN enables fast containment queries (`@>`), but it carries higher write latency during heavy insert bursts.

### Summary Rule
- **B-Tree**: Use for unique IDs and exact point lookups.
- **BRIN**: Use for append-only timestamp ranges.
- **GIN**: Use for internal keys in JSONB objects and array tags.
```