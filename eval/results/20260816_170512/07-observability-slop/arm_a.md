# RFC: Enterprise Distributed Tracing Standards

## Overview
Observability is critical for maintaining platform reliability and engineering productivity across all product divisions. 

Distributed tracing is essential for diagnosing cascading failures across service boundaries. For example, a recent outage was traced to unpropagated context headers across asynchronous message queues. To prevent similar issues and establish end-to-end visibility, we are mandating standardized OpenTelemetry instrumentation across all network ingress gateways and internal services.

## Requirements
To ensure consistent trace propagation and telemetry collection, all services must adhere to the following standards:

1. **Header Propagation:** Inject and propagate W3C `traceparent` headers across all synchronous HTTP/gRPC requests and asynchronous message queues.
2. **Telemetry Export:** Export all generated spans directly to the centralized OpenTelemetry Collector.
3. **Error Reporting:** Explicitly record error status codes and relevant exception metadata on failed spans.