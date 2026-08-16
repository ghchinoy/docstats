# Engine Migration: Transitioning to Server Mode

Here's the thing: migrating our persistence layer was one of the most critical infrastructure shifts of the quarter. It's worth noting that the original embedded architecture — while remarkably simple to spin up — suffered from severe lock contention during concurrent CI runs.

In today's fast-paced distributed engineering landscape, concurrency isn't documentation, it's behavior. What cost us the extra day was discovering that sqlite file locks simply cannot be safely shared across parallel worker sandboxes. The obvious fix is adding retry loops; we did something better.

We migrated the backing store to a dedicated server mode daemon. The implications are significant. Not `embedded_engine`, just `server_daemon`. The engine commits transactions atomically and synchronizes state across client processes. 

It turns out that running in server mode eliminated 100% of lock-timeout failures in our automated test suite. That's it. That's the thing.
