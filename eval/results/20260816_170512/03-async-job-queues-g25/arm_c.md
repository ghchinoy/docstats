# RFC: Asynchronous Task Processing Pipeline with RabbitMQ

## 1. Context and Problem Statement
Synchronous execution of long-running operations blocks HTTP request threads, causing connection pool exhaustion, elevated latency, and gateway timeouts under burst traffic. Decoupling task ingestion from execution requires an asynchronous message broker that guarantees fault isolation, bounded resource consumption, and deterministic failure handling.

## 2. Queue Topology and Message Routing
Producers publish task payloads to durable RabbitMQ topic exchanges. RabbitMQ routes messages to dedicated consumer work queues with disk-backed message persistence (`delivery_mode=2`). Worker pools consume messages asynchronously, returning explicit acknowledgments (`basic.ack`) only upon successful completion of downstream side effects.

## 3. Resilience Mechanisms

### 3.1 Dead-Letter Exchanges and Retry Strategy
Unrecoverable task failures and malformed payloads trigger negative acknowledgments (`basic.nack(requeue=false)`). RabbitMQ re-routes rejected messages through a Dead-Letter Exchange (DLX) to an intermediate retry queue with exponential Time-To-Live (TTL) expiration. When message retry counts exceed the configured threshold, the DLX routes the payload into a dead-letter quarantine queue for manual inspection and replay, preventing poison messages from cyclically blocking worker threads.

### 3.2 Idempotency Guarantees
Because RabbitMQ guarantees at-least-once delivery, consumers must guard against duplicate executions caused by network partitions or worker crash-restarts. Producers attach a deterministic `idempotency_key` (UUIDv4) to message headers. Consumers verify and claim this key via an atomic cache write (`SET key NX EX 86400`) or database unique constraint before executing side effects, ensuring deduplication.

### 3.3 Consumer Backpressure and Flow Control
Consumers configure explicit prefetch limits via `basic.qos(prefetch_count=N)`. This restricts unacknowledged in-flight messages per worker process, preventing unmanaged memory allocation during ingestion spikes and distributing tasks evenly across available consumer nodes.