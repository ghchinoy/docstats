# Scaling to 100k RPS: Active-Active Multi-Region Redis Without Split-Brain

Routing cross-region traffic to a single centralized cache caused high latency. We migrated to a multi-region, active-active Redis architecture across `us-east-1`, `eu-west-1`, and `ap-southeast-1` to achieve sub-10ms p99 response times at a sustained 100,000 requests per second (RPS).

### Regional Routing and Synchronization

We directed traffic to the nearest geographic region to remove wide-area network (WAN) latency from the critical path. Each regional Redis cluster handles reads and writes with sub-millisecond execution and synchronizes state asynchronously across the global topology.

### Eliminating Split-Brain and Write Conflicts

Concurrent writes across multiple regions risk split-brain anomalies and divergent data during network partitions. We mitigated these risks by combining CRDTs, quorum arbiters, and hybrid logical clocks:

* **CRDT-Based Data Layer:** We adopted Conflict-Free Replicated Data Types (CRDTs). Sets use Add-Wins Observed-Removed Sets (AWORSet) and numeric metrics use PN-Counters to guarantee deterministic state convergence without distributed locks.
* **Quorum Arbiters:** Topology management uses a Raft consensus group with an independent tie-breaker node in a fourth region to prevent split-brain during WAN isolation. A partitioned cluster losing quorum fails over to a read-only mode to prevent uncommitted writes.
* **Hybrid Logical Clocks (HLC):** We combined physical time with logical counters for Last-Write-Wins (LWW) key-value records to prevent data overwrites caused by NTP clock drift across cloud providers.

### Results

The architecture absorbed the 100k RPS peak load. Global p99 latency dropped from 165ms to 6ms. Chaos testing validated zero data divergence during simulated transatlantic network cuts.