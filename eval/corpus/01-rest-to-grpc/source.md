# Migration Guide: Upgrading to gRPC & Protobuf

We are migrating internal service-to-service communication from JSON REST over HTTP/1.1 to Protobuf gRPC over HTTP/2. 

### Why the Switch?
HTTP/1.1 and JSON introduce significant CPU and network overhead at scale. By adopting gRPC and Protocol Buffers, we achieve:
- **Strict Contracts**: Centralized `.proto` definitions provide type safety, code generation, and backward compatibility.
- **HTTP/2 Multiplexing**: Multiple concurrent requests share a single TCP connection, eliminating head-of-line blocking and connection churn.
- **Efficient Serialization**: Compact binary encoding eliminates the CPU overhead of repetitive JSON parsing.

### Latency Payoffs
Internal benchmarks show a **30% to 50% reduction in p99 latency** and up to a **6x reduction in payload sizes**. Persistent HTTP/2 connections also eliminate the latency tax of continuous TCP/TLS handshakes.

---

### Updating Client Stubs

Follow these steps to migrate your consumer services:

1. **Pull the Schema**: Add the upstream `.proto` dependency from our shared schema repository or package manager.
2. **Generate Stubs**: Compile the stubs using `protoc` or our standard `buf` CLI:
   ```bash
   buf generate buf.build/internal-apis/user-service
   ```
3. **Initialize the Channel**: Replace HTTP clients (e.g., Axios, `fetch`, or `http.Client`) with a long-lived gRPC channel and client stub:
   ```go
   // Go Example
   conn, _ := grpc.Dial("user-service:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
   client := pb.NewUserServiceClient(conn)
   ```
4. **Update Call Sites & Errors**: Replace URL path calls with typed RPC methods (e.g., `client.GetUser(ctx, req)`). Update error parsing to read gRPC status codes (e.g., `codes.NotFound`) rather than HTTP `404` status numbers.