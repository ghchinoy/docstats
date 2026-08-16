# Internal Service Migration: JSON REST to Protobuf gRPC

We are migrating internal service-to-service communication from JSON REST (HTTP/1.1) to **Protobuf-powered gRPC (HTTP/2)**. Update your client services using the steps below.

### Architecture Changes
- **Strict Contracts**: Protobuf schemas enforce backwards-compatible, strongly-typed interfaces.
- **Multiplexing**: HTTP/2 processes concurrent requests over a single TCP connection. This eliminates HTTP/1.1 head-of-line blocking and connection handshake overhead.
- **Efficiency**: Binary serialization reduces CPU overhead compared to parsing JSON strings.

### Production Test Results
We observed the following metrics during production testing:
- **60–80% reduction** in payload size via compact binary encoding.
- **5–8x faster** serialization and deserialization speeds.
- **~40% drop in p99 latencies** under high concurrency due to persistent HTTP/2 connection pooling.

---

### Updating Client Stubs

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