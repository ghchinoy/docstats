# Migrating Internal Services from REST to gRPC

Our internal microservice traffic has outgrown JSON REST over HTTP/1.1. To reduce inter-service latency and optimize CPU utilization across our clusters, we are migrating all internal service-to-service communication to Protocol Buffers (Protobuf) over gRPC (HTTP/2).

## Why We Switched

JSON serialization and deserialization consume measurable CPU overhead at scale, while text-based payloads inflate network bandwidth. Furthermore, HTTP/1.1 incurs head-of-line blocking because each TCP connection processes only one outstanding request-response pair at a time.

gRPC and Protobuf resolve these bottlenecks through three mechanisms:
- **Binary serialization:** Protobuf encodes typed data into compact binary payloads, bypassing expensive JSON string parsing.
- **HTTP/2 multiplexing:** A single TCP connection handles concurrent bidirectional streams, eliminating connection churn and head-of-line blocking.
- **HPACK header compression:** Repeated request metadata compresses across streams to reduce per-RPC network overhead.

Internal benchmarks show a 40–50% reduction in median latency and tighter P99 tail latency distributions across deep service call graphs.

## Updating Client Stubs

To migrate consuming services:

1. **Obtain the `.proto` definition:** Pull the target service schema from the central schema registry (`proto/services/<service_name>/v1/`).
2. **Compile client stubs:** Run `protoc` with the target language plugin (such as `protoc-gen-go` or `grpc_tools_node_protoc_plugin`) to generate typed client bindings and message structs.
3. **Initialize the transport channel:** Configure a long-lived gRPC channel with keepalive parameters and service discovery endpoints.
4. **Invoke typed RPCs:** Replace HTTP client calls with generated stub methods. Construct typed Protobuf message objects directly instead of serializing ad-hoc payloads.
5. **Handle gRPC status codes:** Parse explicit `grpc.Status` errors (such as `UNAVAILABLE`, `DEADLINE_EXCEEDED`, or `NOT_FOUND`) rather than generic HTTP status integers.