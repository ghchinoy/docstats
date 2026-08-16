# RFC: Enterprise Distributed Tracing Standards

Unpropagated trace context headers between asynchronous message queues caused last week's outage. To debug cascading failures across service boundaries, we require mandatory OpenTelemetry instrumentation across all network ingress gateways. 

Unified trace propagation eliminates these blind spots. Engineering teams must configure all services to meet these requirements:

* Inject W3C `traceparent` headers into all outbound requests.
* Export spans to the central collector.
* Record error status codes on failed operations.