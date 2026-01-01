# Architecture Diagram Template

Use this structure when adding new Arcore SyncBridge diagrams. Prefer Mermaid so diagrams can be version-controlled.

## System Context
```mermaid
C4Context
    title System Context Diagram for Arcore SyncBridge
    Person(user, "Operator", "Configures sync definitions")
    System(syncbridge, "Arcore SyncBridge", "Syncs Postgres with SharePoint")
```

## Container View
```mermaid
C4Container
    title Container Diagram for Arcore SyncBridge
    Container(api, "Control Plane API", "FastAPI", "Configuration and orchestration")
    Container(worker, "Sync Workers", "Celery", "Execute sync jobs")
```

## Component View
```mermaid
flowchart LR
    Router --> Auth --> Services
```

## Sequence Diagram (Core Flow)
```mermaid
sequenceDiagram
    participant UI
    participant API
    participant Worker
    UI->>API: Start sync
    API->>Worker: Enqueue job
```
