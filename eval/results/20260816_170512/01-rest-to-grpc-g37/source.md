# Internal Service Migration: JSON REST to Protobuf gRPC

We are migrating internal service-to-service communication from JSON REST (HTTP/1.1) to **Protobuf-powered gRPC (HTTP/2)**. This guide outlines the rationale, latency improvements, and the process for updating your client services.

### Why the Switch?
- **Strict Contracts**: Protobuf replaces loose OpenAPI specs with strict, backwards-compatible, strongly-typed schemas.
- **Multiplexing**: HTTP/2 handles concurrent requests over a single TCP connection, eliminating HTTP/1.1 head-of-line blocking and connection handshake overhead.
- **Efficiency**: Protobuf’s binary serialization dramatically reduces CPU overhead compared to parsing large JSON strings.

### Latency & Throughput Payoffs
In production testing, the transition delivered:
- **60–80% reduction** in payload size via compact binary encoding.
- **5–8x faster** serialization and deserialization speeds.
- **~40% drop in p99 latencies** under high concurrency due to persistent HTTP/2 connection pooling.

---

### How to Update Client Stubs

1. **Add Contract Dependency**:
   Import the target service's schema from our central repository:
   ```bash
   npm install @company/proto-user-service
   ```

2. **Generate Stubs (if building locally)**:
   Use `buf` or `protoc` to generate typed interfaces:
   ```bash
   buf generate buf.build/company/user-service
   ```

3. **Swap the Transport Layer**:
   Replace REST wrappers (e.g., Axios, `fetch`) with the generated gRPC client and a persistent channel:

   ```typescript
   import { credentials } from '@grpc/grpc-js';
   import { UserServiceClient } from '@company/proto-user-service';

   // Initialize a persistent gRPC channel
   const client = new UserServiceClient(
     'user-service.internal:50051',
     credentials.createInsecure()
   );

   // Execute strongly-typed RPC calls
   client.getUser({ userId: '12345' }, (err, response) => {
     if (err) console.error(`gRPC Error [${err.code}]:`, err.message);
     console.log('User:', response);
   });
   ```

For questions or schema change requests, open a PR in the `api-schemas` repo or reach out in `#grpc-migration`.