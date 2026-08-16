# RFC: Asynchronous Task Processing Pipeline

**Status:** Proposed  
**Author:** Engineering  
**Core Components:** RabbitMQ, Consumer Workers, Redis  

---

### 1. Objective
Decouple compute-intensive background tasks from the synchronous API request-response lifecycle. This architecture reduces API latency, isolates downstream failures, and establishes a resilient, horizontally scalable processing pipeline.

### 2. Architecture & Design

```
[Producer] -> [RabbitMQ Direct Exchange] -> [Work Queue] -> [Consumers]
                                                  | (failure/retry)
                                            [DLX / DLQ]
```

* **Ingestion:** Producers publish task messages to a durable RabbitMQ topic exchange using persistent delivery mode (`delivery_mode: 2`).
* **Processing:** Stateless worker pools consume tasks from work queues using explicit manual acknowledgments (`basic.ack` / `basic.nack`).

### 3. Reliability & Flow Control

#### A. Idempotency Guarantees
To handle RabbitMQ's at-least-once delivery semantics, every task message must include a unique `idempotency_key` (UUID or deterministic hash) in its headers.
* Before processing, consumers execute an atomic Redis operation: `SET idempotency_key PROCESSING NX EX <ttl>`.
* Once processing finishes successfully, the status is updated to `COMPLETED`. Duplicate incoming messages are short-circuited, skipped, and acknowledged immediately.

#### B. Dead-Letter Exchanges (DLX) & Retry Strategy
* When a transient failure occurs, the consumer rejects the message with `requeue=false`. RabbitMQ routes the message via `x-dead-letter-exchange` to a retry queue configured with a message TTL for exponential backoff.
* Messages exceeding the maximum retry threshold ($N=5$) are routed to a permanent dead-letter queue (`tasks.dlq`) to isolate poison-pill messages without stalling active queues.

#### C. Consumer Backpressure
To prevent worker node saturation and out-of-memory errors during traffic spikes:
* Consumers enforce a strict channel prefetch limit via `basic.qos(prefetch_count=N)`.
* Workers only receive new tasks as existing tasks are acknowledged, ensuring memory stability and equitable load distribution across worker instances.