# RFC: Enterprise Distributed Tracing Standards

In today's fast-paced microservice landscape, observability plays a crucial role in maintaining platform reliability. The implications are significant for engineering productivity across all product divisions.

What makes distributed tracing essential is understanding cascading failures across service boundaries. What caused the outage last week was unpropagated trace context headers between asynchronous message queues. What we need now is mandatory OpenTelemetry instrumentation across all network ingress gateways.

This changes everything. Serves as a testament to modern engineering maturity. A myriad of benefits emerge from unified trace propagation.

We establish the standard today. Every service must inject W3C traceparent headers. Every service must export spans to the central collector. Every service must record error status codes. That's it. That's the standard.
