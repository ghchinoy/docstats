# RFC: Asynchronous Task Processing Pipeline

**Status:** Proposed  
**Author:** Engineering Team  

## Problem Statement
High-latency background jobs currently block user-facing APIs. We propose a resilient, scalable, asynchronous task processing pipeline using RabbitMQ.

---

## Proposed Architecture

```
[API Producer] -> (Topic Exchange) -> [Task Queue] -> [Worker Consumers]
                         |                                    |
                    (TTL/Failed)                      (Atomic Redis Lock)
                         v                                    v
                     (DLX) -> [DLQ]                     [Idempotency]
```

### 1. Broker Topology & Dead-Letter Exchanges (DLX)
Producers publish tasks with persistent delivery modes to a primary topic exchange. Transient errors retry with exponential backoff using intermediary delay queues. Upon exceeding maximum attempts (`max_retries = 5`), the broker routes failed messages to a Dead-Letter Exchange (`task.dlx`) bound to a Dead-Letter Queue (`task.dlq`). This isolates poison-pill messages, triggers alerts, and enables manual replay.

### 2. Idempotency Guarantees
To handle RabbitMQ's at-least-once delivery model without side effects, producers must attach an `idempotency_key` (UUIDv4) in the message headers. Consumers enforce deduplication by executing an atomic `SETNX` against Redis with an appropriate TTL before execution:
- **New Key:** Lock acquired, task executed, state updated to `COMPLETED`.
- **Existing Key:** Duplicate detected; message is immediately acknowledged (`basic.ack`) and discarded.

### 3. Consumer Backpressure
To prevent worker node out-of-memory (OOM) crashes during load spikes, consumers operate using manual acknowledgments and a bounded channel prefetch limit (`basic.prefetch = 20`). This ensures workers only pull tasks matching their processing capacity. Horizontal Pod Autoscaling (HPA) via KEDA will scale worker pools based on total queue depth.