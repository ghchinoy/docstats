# Scaling to 100k RPS: Active-Active Multi-Region Redis Without Split-Brain

Routing cross-region traffic back to a centralized cache pushed our global p99 latency past 160ms. To achieve sub-10ms p99 response times at a sustained 100,000 requests per second (RPS), we deployed an active-active Redis architecture across `us-east-1`, `eu-west-1`, and `ap-southeast-1`.

### Local Execution, Asynchronous Replication

Routing clients to the nearest region removes wide-area network (WAN) latency from the critical path. Each regional Redis cluster processes reads and writes locally with sub-millisecond execution, then replicates mutations asynchronously across regions.

### Preventing Split-Brain and Write Conflicts

Concurrent multi-region writes risk split-brain conditions and divergent states during network partitions. We resolved these conflicts through three mechanisms:

1. **CRDT-Based Data Structures:** We implemented Conflict-Free Replicated Data Types (CRDTs). Add-Wins Observed-Removed Sets (AWORSet) handle collection data, while PN-Counters manage numeric metrics. These structures converge deterministically without distributed locks.
2. **Quorum Arbiters:** To prevent split-brain states during WAN isolation, a Raft consensus cluster with an independent arbiter node in a fourth region manages topology. If a partitioned region loses quorum, it enters read-only mode to reject isolated writes.
3. **Hybrid Logical Clocks (HLC):** For Last-Write-Wins (LWW) keys, we paired physical timestamps with monotonic logical counters. This prevents out-of-order writes caused by NTP clock drift across cloud regions.

### Production Results

The architecture sustained our 100k RPS peak load in production:

- Global p99 latency dropped from 165ms to 6ms.
- Local read and write latencies stayed below 1ms.
- Chaos tests simulating cross-Atlantic fiber cuts produced zero data divergence or stale overwrites.