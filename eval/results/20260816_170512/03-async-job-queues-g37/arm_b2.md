# RFC: Asynchronous Task Processing Pipeline

**Status:** Proposed  
**Author:** Engineering  
**Core Components:** RabbitMQ, Consumer Workers, Redis  

---

### 1. Objective
We will decouple compute-heavy background tasks from the synchronous API request-response cycle. Moving these tasks to a dedicated pipeline reduces API latency and isolates downstream failures.

### 2. Architecture & Design

```
[Producer] -> [RabbitMQ Direct Exchange] -> [Work Queue] -> [Consumers]
                                                  | (failure/retry)
                                            [DLX / DLQ]
```

* **Ingestion:** Publishers route task messages to a durable RabbitMQ topic exchange with persistent delivery (`delivery_mode: 2`).
* **Processing:** Stateless worker pools consume tasks using manual acknowledgments (`basic.ack` / `basic.nack`).

### 3. Reliability & Flow Control

#### A. Idempotency Guarantees
RabbitMQ provides at-least-once delivery. Publishers must include a unique `idempotency_key` (UUID/hash) in the message header. 
* Consumers execute an atomic `SET idempotency_key PROCESSING NX EX <ttl>` in Redis before processing.
* Workers transition completed tasks to `COMPLETED`. They short-circuit duplicate incoming messages and acknowledge them.

#### B. Dead-Letter Exchanges (DLX) & Retry Strategy
* Workers reject messages on transient failures with `requeue=false`. RabbitMQ routes these via `x-dead-letter-exchange` to a retry queue configured with message TTL for exponential backoff.
* RabbitMQ directs messages exceeding max retry attempts ($N=5$) to a permanent DLQ (`tasks.dlq`). This isolates poison pills without blocking queues.

#### C. Consumer Backpressure
We prevent worker node starvation during traffic bursts using channel prefetch limits.
* Consumers enforce a channel prefetch limit (`basic.qos(prefetch_count=N)`).
* Workers pull new tasks after acknowledging existing tasks. This ensures memory stability and distributes the workload across worker instances.