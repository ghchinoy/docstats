# Internal Service Migration: JSON REST to Protobuf gRPC

We are migrating internal service-to-service communication from JSON REST (HTTP/1.1) to **Protobuf-powered gRPC (HTTP/2)**. This guide outlines the rationale, performance improvements, and step-by-step instructions for updating client services.

### Why We Are Migrating
- **Strict Contracts**: Protobuf replaces loosely enforced OpenAPI specs with strongly typed, backward-compatible schemas.
- **Multiplexing**: HTTP/2 multiplexes concurrent requests over a single TCP connection, eliminating HTTP/1.1 head-of-line blocking and connection handshake overhead.
- **Efficiency**: Protobuf’s compact binary serialization significantly reduces CPU overhead compared to parsing large JSON strings.

### Latency and Throughput Improvements
Production benchmarks demonstrated the following performance gains:
- **60–80% smaller** payload sizes from binary encoding.
- **5–8x faster** serialization and deserialization.
- **~40% lower p99 latency** under heavy load due to persistent HTTP/2 connection pooling.

---

### Updating Client Stubs

1. **Add Contract Dependency**:
   Install the target service's schema package from our internal registry:
   ```bash
   npm install @company/proto-user-service
   ```

2. **Generate Stubs (Local Builds Only)**:
   Use `buf` or `protoc` to generate typed interfaces:
   ```bash
   buf generate buf.build/company/user-service
   ```

3. **Swap the Transport Layer**:
   Replace REST HTTP clients (such as Axios or `fetch`) with the generated gRPC client and a persistent channel:

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

For questions or schema change requests, open a pull request in the `api-schemas` repository or contact the team in `#grpc-migration`.