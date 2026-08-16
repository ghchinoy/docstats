## Scaling Global Caching: Our Active-Active Multi-Region Redis Architecture

We scaled our global application to 100,000 requests per second (RPS). At this volume, our single-region Redis setup bottlenecked cross-region users and increased latency.

We engineered a multi-region, active-active Redis caching solution. Each region hosts an independent, writable Redis cluster to serve local traffic. Our routing layer directs user requests to the nearest regional cache.

We implemented a custom replication layer to propagate writes asynchronously between regions. We resolve conflicts using a Last-Write-Wins (LWW) strategy based on a globally synchronized timestamp attached to each cache entry. If the replication layer detects a conflict, it keeps the entry with the most recent timestamp. This approach guarantees eventual consistency without consensus protocols.

We now handle over 100,000 RPS globally and maintain sub-10ms cache access times for most users. A regional outage leaves other regions unaffected. Each cluster operates independently and catches up on replication after the offline region recovers.