# Internal Service Migration: JSON REST to Protobuf gRPC

We are migrating internal service-to-service communication from JSON REST (HTTP/1.1) to gRPC with Protocol Buffers over HTTP/2. This guide covers the performance rationale, measured latency improvements, and the process for updating client services.

### Architectural Rationale

- **Strict Schema Contracts**: Protocol Buffers enforce backwards-compatible, strongly typed interfaces across microservices, eliminating schema drift.
- **Multiplexing over Single TCP Channels**: HTTP/2 handles concurrent RPCs over persistent connections, avoiding HTTP/1.1 head-of-line blocking and repeated handshake overhead.
- **Efficient Binary Serialization**: Protobuf bypasses the CPU overhead of repetitive JSON string parsing and serialization.

### Latency and Throughput Benchmarks

Production canary testing shows:
- **60–80% reduction** in payload size from compact binary encoding.
- **5–8x faster** serialization and deserialization speeds across service boundaries.
- **~40% drop in p99 latencies** under load due to HTTP/2 stream multiplexing.

---

### Updating Client Stubs

#### 1. Add the Contract Dependency
Pull the target service's compiled definitions from the central registry:

```bash
npm install @company/proto-user-service
```

#### 2. Generate Stubs Locally (Optional)
If you build contracts directly from source, generate client code via `buf`:

```bash
buf generate buf.build/company/user-service
```

#### 3. Update the Transport Layer
Replace HTTP wrappers (`fetch`, `axios`) with the generated gRPC client and a persistent channel:

```typescript
import { credentials } from '@grpc/grpc-js';
import { UserServiceClient } from '@company/proto-user-service';

// Initialize a persistent gRPC channel
const client = new UserServiceClient(
  'user-service.internal:50051',
  credentials.createInsecure()
);

// Execute a strongly typed RPC call
client.getUser({ userId: '12345' }, (err, response) => {
  if (err) {
    console.error(`gRPC Error [${err.code}]:`, err.message);
    return;
  }
  console.log('User:', response);
});
```

Submit schema changes via pull request to the `api-schemas` repository, or ask questions in `#grpc-migration`.