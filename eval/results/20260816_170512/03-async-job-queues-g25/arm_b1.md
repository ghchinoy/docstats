# Architecture RFC: Asynchronous Task Processing Pipeline

## 1. Context

Our API services currently execute long-running tasks inside synchronous HTTP request handlers. When downstream dependencies stall or request volumes spike, worker threads block until clients hit gateway timeouts.

## 2. Proposed Architecture

We will route background operations through RabbitMQ work queues. Producers publish task payloads to a direct exchange, which routes messages to dedicated queues. Consumer processes pull tasks from these queues, execute the work, and acknowledge completion.

## 3. Implementation Details

### Dead-Letter Exchanges (DLX)
When a consumer encounters an unrecoverable error or exhausts its retry budget, it rejects (NACKs) the message without requeueing. RabbitMQ routes these failed messages to a Dead-Letter Exchange, which deposits them into a quarantine queue. Engineers can inspect failed payloads, debug the failure, and republish them.

### Idempotency Keys
Producers generate an `idempotency_key` UUID for each task payload. Before executing, consumers check this key against a distributed cache. If the key exists, the worker acknowledges the message and drops execution. If the key is new, the consumer records it with a TTL upon completing the task.

### Consumer Backpressure
Consumers set `basic.qos(prefetch_count=N)` to limit unacknowledged messages per worker. This bounds worker memory consumption and allows RabbitMQ to route incoming tasks to idle consumers rather than queueing them behind saturated ones.

## 4. Operational Impact

Moving execution to background queues removes blocking operations from API request paths, bounds client-facing latency, and isolates batch workloads from user traffic.