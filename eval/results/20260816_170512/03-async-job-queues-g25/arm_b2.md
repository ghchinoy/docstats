# Architecture RFC: Asynchronous Task Processing Pipeline

## 1. Introduction

We will build an asynchronous task processing pipeline to decouple long-running operations from user requests. Our current synchronous processing causes timeouts and resource contention during complex operations.

## 2. Proposed Solution: RabbitMQ-based Pipeline

We will use RabbitMQ as the message broker. Producers enqueue tasks as messages into dedicated work queues. Consumers process these tasks in the background.

## 3. Key Architectural Considerations

1.  **Dead-Letter Exchanges (DLX):**
    Consumers NACK messages that fail processing due to application errors or validation failures. RabbitMQ routes these messages to a Dead-Letter Exchange (DLX) after a configured number of retries. The DLX forwards them to a parking lot queue. Engineers can then inspect, re-queue, or archive these persistent failures.

2.  **Idempotency Keys:**
    Each task message includes a unique, client-generated `idempotency_key`. Consumers use this key to process tasks exactly once, handling redeliveries from transient failures, network partitions, or consumer restarts. Consumers store the `idempotency_key` in the database or cache upon completion to prevent duplicate work.

3.  **Consumer Backpressure:**
    Consumers implement `basic.qos` (prefetch count) to limit the number of unacknowledged messages they receive from RabbitMQ. This ensures consumers fetch only the messages they have capacity to process. RabbitMQ can then distribute remaining messages to other available consumers, preventing memory exhaustion.

## 4. Expected Outcomes

This architecture handles failures through dead-lettering, prevents duplicate processing via idempotency keys, and stabilizes resource utilization across our services.