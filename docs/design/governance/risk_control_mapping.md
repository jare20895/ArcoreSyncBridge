# Risk and Control Mapping

| Risk | Control | Evidence |
| --- | --- | --- |
| Data leakage | Encryption at rest and in transit | KMS policy and TLS config |
| Unauthorized access | Azure AD RBAC and scoped tokens | Role assignments |
| Data drift | Ledger and drift detection reports | Run history logs |
| Service outage | Worker retries and queueing | Monitoring dashboards |
