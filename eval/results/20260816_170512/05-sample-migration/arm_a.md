# Engine Migration: Transitioning to Server Mode

Migrating our persistence layer was one of the most critical infrastructure updates this quarter. While the original embedded architecture was simple to deploy, it suffered from severe lock contention during concurrent CI runs.

SQLite file locks cannot be safely shared across parallel worker sandboxes. Rather than relying on retry loops, we migrated the backing store from `embedded_engine` to a dedicated `server_daemon`. 

In server mode, the daemon commits transactions atomically and synchronizes state across client processes. This architectural shift eliminated 100% of lock-timeout failures in our automated test suite.