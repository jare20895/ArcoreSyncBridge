# Configuration Guide

## Environment variables

| Variable | Description | Default |
| --- | --- | --- |
| API_HOST | Host interface for API | 0.0.0.0 |
| API_PORT | API port | 8080 |
| DATABASE_URL | Meta-store Postgres DSN | none |
| REDIS_URL | Redis connection URL | redis://localhost:6379/0 |
| LOG_LEVEL | Logging level | INFO |
| AZURE_TENANT_ID | Azure AD tenant ID | none |
| AZURE_CLIENT_ID | Azure AD app client ID | none |
| AZURE_CLIENT_SECRET | Azure AD app client secret | none |
| GRAPH_SCOPES | Graph scopes for app-only | https://graph.microsoft.com/.default |
| SP_HOSTNAME | SharePoint hostname | none |
| WORKER_CONCURRENCY | Celery worker concurrency | 4 |
| SYNC_BATCH_SIZE | Batch size for sync writes | 100 |
| RETRY_MAX_ATTEMPTS | Max retry attempts | 5 |

## Config files
- Optional YAML for environment-specific overrides
- Sensitive values should use secrets manager integrations
