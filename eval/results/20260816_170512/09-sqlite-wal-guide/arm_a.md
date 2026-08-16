# Write-Ahead Logging in SQLite

By default, SQLite uses a rollback journal to implement atomic commits and rollbacks. In this default mode, SQLite copies the original, unmodified database content into a separate rollback journal file before applying changes to the main database file.

### How WAL Works

Write-Ahead Logging (WAL) is an alternative to the traditional rollback journal. In WAL mode, SQLite does not write modifications directly to the database file; instead, it appends changes to a separate WAL file.

A `COMMIT` occurs as soon as a special commit record is appended to the WAL. Because WAL writes are sequential and do not overwrite existing pages, commit operations are fast and avoid expensive disk seeks across the database file.

### Advantages of WAL Mode

1. **Improved concurrency**: Readers do not block writers, and writers do not block readers. Read and write operations can proceed concurrently.
2. **Reduced disk I/O**: Most operations are sequential appends to the WAL rather than random writes across database pages.
3. **Fewer `fsync` operations**: Sync operations typically occur during periodic checkpoints rather than on every individual transaction commit.

### Checkpointing

When the WAL file reaches a configured threshold (1,000 pages by default), SQLite automatically executes a checkpoint to copy the modified pages back into the main database file. Checkpointing can also be invoked manually via the SQLite API or scheduled through background worker threads.