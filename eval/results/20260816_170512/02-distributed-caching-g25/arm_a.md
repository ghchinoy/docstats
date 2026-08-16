## Scaling Global Caching: Our Active-Active Multi-Region Redis Architecture

Scaling a global application to 100,000 requests per second (RPS) demands a resilient, high-performance caching layer. For our distributed services, a single-region Redis deployment quickly became a bottleneck, introducing significant cross-region latency and degrading user experience.

To solve this, we engineered a multi-region, active-active Redis caching architecture. Unlike a traditional primary-replica topology, each region hosts an independent, fully writable Redis cluster that serves local traffic with sub-millisecond overhead. Inbound traffic is dynamically routed to the nearest regional cache, maximizing throughput and minimizing latency.

The primary engineering challenge in active-active topologies is maintaining consistency across distributed writes. To address this, we developed a custom asynchronous replication layer paired with a Last-Write-Wins (LWW) conflict-resolution strategy. Each cache entry is stamped with a synchronized, high-precision timestamp. When concurrent writes occur across regions, the replication layer applies the write with the most recent timestamp. This approach guarantees eventual consistency across all regions without the latency overhead of distributed consensus protocols like Raft or Paxos.

This architecture has significantly improved system performance and reliability:
- **Throughput & Latency:** We comfortably handle over 100,000 RPS globally while maintaining sub-10ms cache access latency for the vast majority of requests.
- **Fault Tolerance:** Regional failures are fully isolated. If an outage occurs, unaffected regions continue operating independently, with the replication pipeline queueing and applying pending writes once the failed region recovers.

This active-active caching foundation provides the performance and operational resilience necessary to support our continued global growth.