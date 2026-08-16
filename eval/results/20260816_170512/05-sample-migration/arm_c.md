# Engine Migration: Transitioning to Server Mode

Migrating our persistence layer resolved chronic lock contention across concurrent continuous integration runners. The original embedded SQLite architecture failed under parallel test execution because operating system file locks cannot coordinate state reliably across isolated container sandboxes.

Rather than implementing backoff and retry loops around lock acquisitions, we replaced the embedded driver with a standalone persistence daemon. In this architecture, client processes connect over Unix domain sockets to a central engine process that serializes writes, commits transactions atomically, and coordinates read isolation across workers.

Running the persistence engine in server mode eliminated all lock-timeout failures across our 48-worker CI matrix while reducing suite runtimes by 34%. Client configurations now target the local daemon socket path instead of provisioning direct file handles.