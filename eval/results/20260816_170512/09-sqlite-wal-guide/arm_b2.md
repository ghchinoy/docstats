# Write-Ahead Logging in SQLite

SQLite uses a rollback journal for transaction rollback and atomic commit by default. This mode writes original database content into a separate journal file before modifying the main database file.

### WAL Mechanics

The write-ahead log (WAL) replaces the rollback journal. WAL mode appends changes to a separate WAL file. 

SQLite executes a COMMIT by appending a commit record to the WAL. This sequential write avoids overwriting existing pages. Commit operations execute without seeking across the database file.

### Advantages of WAL Mode

* **Concurrent reads**: Readers and writers do not block each other.
* **Reduced disk I/O**: Operations append to the WAL instead of updating random disk pages.
* **Fewer fsync calls**: Sync operations happen during periodic checkpointing, avoiding per-transaction overhead.

### Checkpointing

SQLite runs a checkpoint to copy WAL pages back into the main database file after the WAL reaches a configured threshold (1000 pages by default). Application code or background worker threads can also trigger this process.