# Write-Ahead Logging in SQLite

By default, SQLite uses a rollback journal for transaction rollback and atomic commit. The default journal mode writes the original unchanged database content into a separate rollback journal file before making modifications to the database file.

### How WAL Works

An alternative to the rollback journal is the write-ahead log (WAL). In WAL mode, changes are not written directly to the database file. Instead, changes are appended to a separate WAL file.

A COMMIT occurs when a special commit record is appended to the WAL. Because writing to the WAL file is sequential and does not overwrite existing pages, commit operations are fast and do not require seeking across the database file.

### Advantages of WAL Mode

1. **Significantly faster concurrent reads**: Readers do not block writers, and writers do not block readers. Reading and writing can proceed concurrently.
2. **Reduced disk I/O**: Most operations are sequential appends to the WAL rather than random disk page updates.
3. **Fewer fsync operations**: Sync operations occur during periodic checkpointing rather than on every single transaction commit.

### Checkpointing

When the WAL file reaches a configured threshold (by default 1000 pages), SQLite automatically runs a checkpoint to copy WAL pages back into the main database file. Checkpointing can also be invoked manually or scheduled by background worker threads.
