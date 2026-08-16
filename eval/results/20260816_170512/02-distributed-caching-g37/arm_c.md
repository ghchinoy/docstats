# Scaling to 100k RPS: Active-Active Multi-Region Redis Without Split-Brain

As our global user base expanded, routing cross-region traffic back to a single centralized cache introduced intolerable latency. To achieve sub-10ms p99 response times at a sustained 100,000 requests per second (RPS), we migrated to a multi-region, active-active Redis architecture across `us-east-1`, `eu-west-1`, and `ap-southeast-1`.

### Local Execution, Global Convergence

Directing traffic to the nearest geographic region eliminated wide-area network (WAN) latency from our critical path. Each regional Redis cluster handles reads and writes locally with sub-millisecond execution, synchronizing state asynchronously across the global topology.

### Eliminating Split-Brain and Write Conflicts

Running concurrent writes across multiple regions introduces significant risks of split-brain anomalies and divergent data during network partitions. We mitigated these risks using a three-tier strategy:

1. **CRDT-Based Data Layer:** We adopted Conflict-Free Replicated Data Types (CRDTs). Sets use Add-Wins Observed-Removed Sets (AWORSet), and numeric metrics use PN-Counters, ensuring mathematically deterministic state convergence without distributed locks.
2. **Quorum Arbiters:** To prevent split-brain during WAN isolation, topology management uses a lightweight Raft consensus group with an independent tie-breaker node in a fourth region. If a partitioned cluster loses quorum, it fails over to a degraded read-only mode to prevent uncommitted writes.
3. **Hybrid Logical Clocks (HLC):** For Last-Write-Wins (LWW) key-value records, we combined physical time with logical counters to prevent data overwrites caused by NTP clock drift across cloud providers.

### The Impact

This architecture comfortably absorbed our 100k RPS peak load. Global p99 latency dropped from 165ms to 6ms, and chaos testing validated zero data divergence during simulated transatlantic network cuts.