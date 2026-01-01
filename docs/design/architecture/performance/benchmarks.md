# Performance Benchmarks

Target metrics are defined for Phase 1. Observed values will be recorded during load testing.

| Metric | Target | Observed (Phase 0) |
| --- | --- | --- |
| Ingestion Throughput | 500 rows/min per worker | Not measured |
| Graph API Latency | < 300 ms p95 | Not measured |
| Ledger Update Latency | < 50 ms p95 | Not measured |
| End-to-End Push Sync | < 5 min for 10k rows | Not measured |

## Measurement plan
- Synthetic workloads per list size (1k, 10k, 100k items)
- Track p95/p99 latency and error rates
- Store results in versioned benchmark reports
