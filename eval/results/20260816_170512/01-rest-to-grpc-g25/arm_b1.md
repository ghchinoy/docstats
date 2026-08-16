### Migration Guide: From JSON REST to Protobuf gRPC for Internal Services

We are migrating all internal service-to-service communication from JSON REST over HTTP/1.1 to Protobuf gRPC over HTTP/2 to reduce network latency and CPU utilization.

### Performance Profile

Parsing text-based JSON over HTTP/1.1 introduces serialization overhead and head-of-line blocking across our internal call graphs. Protobuf serializes data into compact binary payloads, which reduces both marshaling time and network bandwidth.

gRPC over HTTP/2 adds:
- Multiplexed requests over persistent TCP connections.
- HPACK header compression.
- Native bi-directional streaming.

Internal benchmarks show up to a 50% reduction in median latency and lower P99 tail latencies on deep service call graphs.

### Client Migration Steps

To migrate a service client:

1. **Define Service Contracts:** Write message types and RPC methods in `.proto` schema files.
2. **Generate Stubs:** Run the `protoc` compiler with the target language plugin (`protoc-gen-go`, `grpc_tools_node_protoc_plugin`, etc.) to generate typed client code.
3. **Update Application Code:**
   - Import the generated package.
   - Create a long-lived gRPC channel targeting the service address.
   - Instantiate the generated client stub with the channel.
   - Replace HTTP request builders and JSON marshaling with typed RPC calls.
   - Handle gRPC status codes (such as `UNAVAILABLE` or `DEADLINE_EXCEEDED`) instead of HTTP status codes.

Refer to the official gRPC documentation for language-specific channel tuning, keepalives, and middleware interceptors.