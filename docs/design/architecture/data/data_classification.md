# Data Classification Policy

Arcore SyncBridge processes customer data sourced from Postgres and writes to SharePoint. Data is classified to enforce protection levels.

| Level | Description | Examples | Handling |
| --- | --- | --- | --- |
| Public | Non-sensitive | Public project names | Standard encryption in transit |
| Internal | Internal-only business data | Project status, tags | Access controlled, logged |
| Confidential | Sensitive business data | Cost, margin, SLA terms | Encryption at rest, restricted roles |
| Restricted | Regulated or PII | Names, emails, IDs | Minimize fields, audit, approval required |

## Enforcement
- Connection profiles record data classification.
- Restricted fields must be explicitly mapped and approved.
- Logs redact restricted fields by default.
