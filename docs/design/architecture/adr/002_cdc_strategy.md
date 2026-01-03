# ADR 002: CDC Strategy (Logical Decoding vs Debezium)

## Status
Proposed

## Context
Phase 5 requires Real-Time Change Data Capture (CDC) to propagate database changes to SharePoint immediately, replacing or augmenting the polling-based "Push" sync. We need a strategy to capture changes from the Source PostgreSQL database.

## Options Considered

### 1. Debezium (Kafka Connect)
- **Pros:** Robust, widely used, handles schema evolution, buffering via Kafka.
- **Cons:** Introduces heavy infrastructure dependencies (Kafka, Zookeeper/Kraft, Java Runtime for Connect). Adds operational complexity not aligned with the current lightweight Python/Docker stack.

### 2. Native Logical Decoding (psycopg / asyncpg)
- **Pros:** Direct Python integration, leverages existing Postgres connection logic, minimal infra footprint (uses existing Redis for buffering if needed).
- **Cons:** Custom implementation of consumption loop, slot management, and decoding (wal2json or pgoutput).

### 3. Polling (Status Quo)
- **Pros:** Simple, already implemented.
- **Cons:** High latency, database load, misses intermediate states.

## Decision
We will use **Native Logical Decoding** using the `psycopg` replication protocol with the `pgoutput` plugin (standard in PG10+).

## Implementation Details
- **Replication Slots:** One slot per Source Database Instance (shared across sync definitions) or per Sync Definition?
  - *Decision:* One slot per **Source Database Instance**. The CDC Service will consume the stream and multiplex events to relevant Sync Definitions based on table name filtering.
- **Publication:** We will create a publication `arcore_cdc_pub` for all tables involved in active syncs.
- **Buffering:** Events will be pushed to a Redis Stream (or Celery Queue) to decouple ingestion from processing (Graph API latency).
- **Library:** `psycopg` (v3) supports replication protocol natively.

## Implications
- Requires `replication` privilege for the database user.
- Requires `wal_level = logical` in `postgresql.conf`.
- CDC Service must run as a long-lived process (Daemon), distinct from Request/Response API or scheduled Tasks. We will add a `cdc_worker` service.

## Validation
- Verify `psycopg` replication connection stability.
- Verify LSN tracking accuracy.
