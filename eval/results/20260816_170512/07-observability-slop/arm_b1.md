# RFC: Enterprise Distributed Tracing Standards

Last week's outage cascaded across service boundaries because our asynchronous message queues dropped trace context headers, delaying root-cause identification. To isolate cross-service failures quickly, platform engineering is standardizing all distributed tracing on OpenTelemetry.

## Requirements

All production services must implement the following controls:

1. **Context Propagation**: Inject and extract W3C `traceparent` headers across all HTTP endpoints, gRPC calls, and asynchronous queue producers/consumers.
2. **Span Export**: Send span data via OTLP to the internal collector daemon (`otel-collector.internal`) with the default 5% head-based sampling configuration.
3. **Error Recording**: Set the span status to `Error` and attach the exception stack trace whenever a request returns an HTTP 5xx or unhandled gRPC status code.

Engineering teams must integrate the shared telemetry library (`@internal/telemetry-sdk`) into their service boot sequence before the next quarterly release cycle.