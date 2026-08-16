# RFC: Asynchronous Task Processing Pipeline

**Status:** Proposed  
**Author:** Engineering  
**Core Components:** RabbitMQ, Consumer Workers, Redis  

---

### 1. Objective
Decouple compute-heavy background tasks from the synchronous API request-response cycle. This architecture reduces API latency, isolates downstream failures, and establishes a resilient task processing pipeline.

### 2. Architecture & Design

```
[Producer] -> [RabbitMQ Direct Exchange] -> [Work Queue] -> [Consumers]
                                                  | (failure/retry)
                                            [DLX / DLQ]
```

* **Ingestion:** Producers publish task messages to a durable RabbitMQ topic exchange with persistent delivery (`delivery_mode: 2`).
* **Processing:** Stateless worker pools consume tasks using manual acknowledgments (`basic.ack` / `basic.nack`).

### 3. Reliability & Flow Control

#### A. Idempotency Guarantees
Because RabbitMQ provides at-least-once delivery, producers must attach a unique `idempotency_key` (UUID or hash) to the message header. 
* Consumers execute `SET idempotency_key PROCESSING NX EX <ttl>` in Redis before running the task.
* On success, consumers update the key state to `COMPLETED`. When a consumer encounters an existing key, it drops the duplicate and acknowledges the message.

#### B. Dead-Letter Exchanges and Retries
* When a task encounters a transient error, the consumer rejects the message with `requeue=false`. RabbitMQ routes the message through an `x-dead-letter-exchange` to a retry queue configured with a message TTL for exponential backoff.
* When retries exceed the threshold ($N=5$), RabbitMQ routes the message to a permanent dead-letter queue (`tasks.dlq`) to isolate poison pills without blocking active queues.

#### C. Consumer Backpressure
To prevent memory exhaustion during traffic spikes:
* Consumers set a channel prefetch limit via `basic.qos(prefetch_count=N)`.
* Workers fetch new tasks only after acknowledging existing tasks, stabilizing memory usage and distributing load across worker instances.