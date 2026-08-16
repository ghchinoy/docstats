# RFC: Asynchronous Task Processing Pipeline

**Status:** Proposed  
**Author:** Platform Infrastructure  
**Core Components:** RabbitMQ, Stateless Consumer Workers, Redis  

---

### 1. Objective
Decouple compute-heavy execution paths from the synchronous HTTP request-response cycle. This architecture bounds API endpoint latency, isolates downstream subsystem failures, and guarantees predictable throughput under burst conditions.

### 2. Architecture & Topology

```
[Publisher] -> [Direct Exchange] -> [Work Queue] -> [Consumers]
                                           | (nack / retry)
                                     [DLX / DLQ]
```

* **Ingestion:** Publishers route task payloads to a durable RabbitMQ direct exchange using persistent message delivery (`delivery_mode: 2`).
* **Processing:** Independent worker pools pull and process messages using explicit manual acknowledgments (`basic.ack` / `basic.nack`).

### 3. Reliability & Flow Control

#### A. Idempotency Controls
Because RabbitMQ provides at-least-once delivery guarantees, publishers must attach a unique `idempotency_key` (UUIDv4) to message headers.
* Consumers execute an atomic Redis command (`SET <idempotency_key> PROCESSING NX EX <ttl>`) prior to execution.
* Upon task completion, workers update the key state to `COMPLETED`. Workers acknowledge and discard duplicate incoming messages immediately without re-executing business logic.

#### B. Dead-Letter Exchanges (DLX) & Retry Topology
* When transient errors occur, consumers issue `basic.nack(requeue=false)`, diverting messages to an intermediate retry exchange backed by per-message TTL delays.
* When retry counts exceed threshold limits ($N=5$), the retry exchange forwards messages to a dead-letter queue (`tasks.dlq`) to isolate unprocessable poison pills without head-of-line queue blocking.

#### C. Consumer Backpressure
To prevent memory exhaustion during traffic spikes:
* Workers configure explicit channel prefetch limits (`basic.qos(prefetch_count=N)`).
* The broker dispatches unacknowledged messages up to the prefetch ceiling, ensuring stable memory footprints and balanced task distribution across the consumer pool.