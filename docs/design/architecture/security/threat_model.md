# Threat Model (STRIDE)

## Threats and mitigations

| Category | Threat | Mitigation |
| --- | --- | --- |
| Spoofing | Stolen or replayed JWT | Short-lived tokens, audience validation, TLS everywhere |
| Tampering | Payload modification in transit | HTTPS, request signing for internal calls |
| Repudiation | Actions without audit trail | sync_events table and immutable run logs |
| Information disclosure | PII leakage via logs or exports | Redaction, encrypted config, least-privilege scopes |
| Denial of service | Graph throttling or high queue depth | Rate limits, backoff, worker autoscaling |
| Elevation of privilege | Over-scoped app permissions | Separate app registrations by environment |
