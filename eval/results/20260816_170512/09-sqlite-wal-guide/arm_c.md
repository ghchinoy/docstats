# Write-Ahead Logging in SQLite

By default, SQLite uses a rollback journal for transaction rollback and atomic commit. In rollback mode, SQLite writes unchanged database pages into a separate journal file before modifying the primary database file directly.

### How WAL Works

Write-ahead logging (WAL) reverses this relationship. In WAL mode, SQLite appends modified pages to a dedicated WAL file rather than overwriting pages in the main database file.

A transaction commits when SQLite appends a commit record to the log. Because SQLite writes to the WAL sequentially, commits avoid random disk seeks and complete faster than traditional journal commits.

### Advantages of WAL Mode

1. **Non-blocking concurrency**: Readers do not block writers, and writers do not block readers. Read and write transactions proceed concurrently across separate connections.
2. **Sequential disk I/O**: SQLite processes transaction writes as sequential log appends rather than random page updates across the storage volume.
3. **Fewer fsync operations**: SQLite defers disk synchronization to periodic checkpoints instead of issuing an `fsync` call on every commit.

### Checkpointing

When the log file reaches a defined threshold (1,000 pages by default), SQLite executes a checkpoint operation. During a checkpoint, SQLite copies modified pages from the WAL back into the main database file. Applications can also invoke checkpoints manually or delegate them to background worker threads via `sqlite3_wal_checkpoint_v2`.