# State Machine Diagram

```mermaid
stateDiagram-v2
    [*] --> New
    New --> Synced: Create item
    Synced --> OutOfSync: Source change detected
    OutOfSync --> Syncing: Job scheduled
    Syncing --> Synced: Update success
    Syncing --> Error: Update failed
    Error --> Syncing: Retry
```
