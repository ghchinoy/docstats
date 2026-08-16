# Engine Migration: Transitioning to Server Mode

We transitioned our persistence layer this quarter to resolve severe lock contention during concurrent CI runs. The original embedded architecture was simple to spin up, but we lost a day discovering that parallel worker sandboxes cannot share sqlite file locks.

Instead of adding retry loops, we migrated the backing store from the `embedded_engine` to a dedicated `server_daemon`. The engine commits transactions atomically and synchronizes state across client processes, eliminating 100% of lock-timeout failures in our automated test suite.