# Scalability Strategy

## Vertical scaling
- Increase worker CPU for heavy transformation workloads.
- Increase memory for large batch payloads.

## Horizontal scaling
- Workers are stateless and can scale by queue depth.
- Partition sync jobs by sync_definition and list IDs.
- Respect Graph API per-tenant throttling to avoid noisy neighbor issues.

## Caching strategy
- Cache Graph site and list IDs in the meta-store.
- Cache field mappings per sync definition in worker memory with TTL.
