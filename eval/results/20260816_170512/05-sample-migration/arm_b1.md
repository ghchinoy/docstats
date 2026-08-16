# Engine Migration: Transitioning to Server Mode

We migrated our persistence layer this quarter to eliminate lock contention during concurrent CI runs. The original embedded SQLite architecture failed because file locks cannot be shared across parallel worker sandboxes. 

Rather than patching the issue with retry loops, we replaced `embedded_engine` with a dedicated `server_daemon`. The server daemon commits transactions atomically and synchronizes state across client processes, eliminating all lock-timeout failures in our automated test suite.