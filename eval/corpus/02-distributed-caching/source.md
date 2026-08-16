# Scaling to 100k RPS: Active-Active Multi-Region Redis Without Split-Brain

As our global traffic surged past 100k requests per second (RPS), cross-region database queries created unacceptable latency bottlenecks. To deliver sub-5ms response times globally, we implemented a multi-region, active-active Redis caching layer across `us-east`, `us-west`, and `eu-central`. 

Here is how we designed the system to scale writes locally while eliminating split-brain risks during network partitions.

### The Architecture: Local Writes, Global Sync
Using GeoDNS and Anycast routing, client requests hit their geographically closest Redis cluster. Each regional cluster handles local reads and writes concurrently, replicating state asynchronously across regions via a bi-directional streaming mesh. 

### Mitigating Split-Brain and Write Conflicts
Active-active topologies risk split-brain states when inter-region links sever and isolated clusters accept divergent writes. We solved this with a two-pronged strategy:

1. **Conflict-Free Replicated Data Types (CRDTs):**  
   We utilized CRDT-based data structures for counters and sets. For key-value updates, we implemented deterministic Last-Write-Wins (LWW) resolution backed by Hybrid Logical Clocks (HLCs) to eliminate clock-skew discrepancies across data centers.
2. **Quorum Fencing via a Witness Node:**  
   For operations requiring strong consistency, we deployed a lightweight arbiter node in a neutral fourth region. During a network partition, only the partition with a strict majority (>50% quorum) retains write leases. The isolated minority region automatically fails over to read-only mode, preventing split-brain writes.

### Results
Our multi-region Redis deployment comfortably absorbs **100k+ RPS** with p99 latencies under **6ms**. Chaos engineering tests simulating complete transatlantic fiber cuts confirmed zero data corruption, with full eventual consistency achieved within 250ms of network healing.