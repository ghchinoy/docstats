## Scaling Global Caching: Our Active-Active Multi-Region Redis Architecture

At 100,000 requests per second (RPS), our single-region Redis deployment added cross-region network hops for international traffic, driving read latencies above acceptable thresholds. 

To eliminate cross-region round trips, we deployed an active-active Redis caching topology across our target regions. Each region hosts an independent, writable Redis cluster. Edge routing directs client traffic to the nearest regional cluster, keeping both reads and writes local.

Active-active caching requires consistent state across regions without introducing blocking operations. We built a replication service that captures local write streams and propagates mutations asynchronously to remote regions. 

To resolve concurrent write conflicts, we use a Last-Write-Wins (LWW) strategy backed by synchronized timestamps attached to each cache key's metadata. When the replication service detects identical keys with divergent values, the payload with the newer timestamp overwrites the existing entry. This approach achieves eventual consistency without introducing consensus protocol overhead like Raft or Paxos on the hot write path.

This architecture handles over 100,000 RPS globally while maintaining sub-10ms cache latency. Regional failures remain isolated: if a region goes offline, the remaining clusters continue serving local traffic independently. Once the offline region recovers, the replication queue replays backlogged mutations until all regional caches reconverge.