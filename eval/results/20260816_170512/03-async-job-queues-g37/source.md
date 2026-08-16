# RFC: Asynchronous Task Processing Pipeline

**Status:** Proposed  
**Author:** Engineering  
**Core Components:** RabbitMQ, Consumer Workers, Redis  

---

### 1. Objective
Decouple compute-heavy background tasks from the synchronous API request-response cycle. This architecture improves API latency, isolates downstream failures, and establishes a resilient, scalable processing pipeline.

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
Due to "at-least-once" delivery semantics, every task must include a unique `idempotency_key` (UUID/hash) in the message header. 
* Consumers execute an atomic `SET idempotency_key PROCESSING NX EX <ttl>` in Redis before processing.
* Completed tasks transition to `COMPLETED`. Duplicate incoming messages are short-circuited and acknowledged immediately.

#### B. Dead-Letter Exchanges (DLX) & Retry Strategy
* Transient failures reject messages with `requeue=false`, routing them via `x-dead-letter-exchange` to a retry queue configured with message TTL for exponential backoff.
* Messages exceeding max retry attempts ($N=5$) are directed to a permanent DLQ (`tasks.dlq`) to isolate poison pills without blocking queues.

#### C. Consumer Backpressure
To prevent worker node starvation during traffic bursts:
* Consumers enforce a strict channel prefetch limit (`basic.qos(prefetch_count=N)`).
* Workers only pull new tasks when existing tasks are acknowledged, ensuring memory stability and equitable workload distribution across worker instances.