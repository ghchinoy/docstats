# Internal Service Migration: JSON REST to Protobuf gRPC

We are migrating internal service-to-service communication from JSON REST (HTTP/1.1) to Protobuf gRPC (HTTP/2). This guide covers performance benchmarks and the migration steps for client services.

### Technical Rationale

- **Typed contracts**: Protobuf enforces backwards-compatible, strongly typed schemas across service boundaries.
- **Multiplexing**: HTTP/2 multiplexes concurrent requests over a single TCP connection, eliminating HTTP/1.1 head-of-line blocking and per-request handshake overhead.
- **Serialization efficiency**: Protobuf binary encoding reduces CPU consumption compared to parsing JSON strings.

### Production Benchmarks

Production testing measured:
- **60–80% reduction** in payload size from binary encoding.
- **5–8x faster** serialization and deserialization speeds.
- **~40% decrease in p99 latencies** under high concurrency via HTTP/2 connection pooling.

---

### Client Migration Steps

1. **Install contract dependency**:
   Import the target service's schema from our central registry:
   ```bash
   npm install @company/proto-user-service
   ```

2. **Generate stubs (local builds)**:
   Use `buf` or `protoc` to generate typed interfaces:
   ```bash
   buf generate buf.build/company/user-service
   ```

3. **Replace the transport layer**:
   Replace HTTP clients (`fetch`, Axios) with the generated gRPC client and a persistent channel:

   ```typescript
   import { credentials } from '@grpc/grpc-js';
   import { UserServiceClient } from '@company/proto-user-service';

   // Initialize a persistent gRPC channel
   const client = new UserServiceClient(
     'user-service.internal:50051',
     credentials.createInsecure()
   );

   // Execute RPC call
   client.getUser({ userId: '12345' }, (err, response) => {
     if (err) console.error(`gRPC Error [${err.code}]:`, err.message);
     console.log('User:', response);
   });
   ```

For schema change requests, open a pull request in `api-schemas` or reach out in `#grpc-migration`.