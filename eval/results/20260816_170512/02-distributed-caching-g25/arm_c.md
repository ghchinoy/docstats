## Scaling Read Throughput with Multi-Region Redis

When our global traffic reached 100,000 requests per second (RPS), cross-region round trips turned our single-region Redis cache into a major bottleneck. Remote clients faced elevated read latency and degraded response times.

To resolve this, we deployed an active-active Redis architecture across three regions. Every region hosts an independent, writable Redis cluster that answers local traffic directly. Geo-DNS routes incoming user traffic to the nearest regional instance, dropping cache read latencies below 10 milliseconds.

The main challenge with active-active caching is avoiding split-brain divergence. We addressed this by building an asynchronous replication layer paired with a Last-Write-Wins (LWW) conflict strategy. Every write embeds a synchronized millisecond timestamp sourced from the cloud provider's NTP service. When replication events collide, the receiving cluster compares timestamps and applies the most recent update. This design guarantees eventual consistency without the operational overhead of distributed consensus protocols like Raft or Paxos.

The architecture currently serves over 100,000 RPS across all regions while providing full fault isolation. If one region suffers an outage, the remaining regions continue operating without interruption. Once the failed region recovers, the replication queue replays missed updates to restore state across the fleet.