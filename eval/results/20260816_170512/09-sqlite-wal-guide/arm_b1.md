# Write-Ahead Logging in SQLite

By default, SQLite uses a rollback journal for atomic commits and rollbacks. In rollback mode, SQLite copies unchanged database pages into a separate journal file before modifying the main database.

### WAL Operation

In WAL mode, SQLite appends changes to a separate WAL file instead of modifying the database file directly. 

SQLite commits a transaction by appending a commit record to the WAL. Because sequential appends do not overwrite existing pages, commits complete without random disk seeks.

### Advantages of WAL Mode

1. **Concurrent access**: Readers do not block writers, and writers do not block readers.
2. **Sequential I/O**: Transactions append sequentially to the WAL instead of writing randomly across the database file.
3. **Fewer sync operations**: SQLite flushes changes to disk during periodic checkpoints rather than on every commit.

### Checkpointing

When the WAL file reaches a configured threshold (1,000 pages by default), SQLite runs a checkpoint to transfer WAL pages back to the main database file. Applications can also invoke checkpoints manually or delegate them to background worker threads.