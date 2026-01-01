# Sync Configuration Workflow

## Overview
Defines the steps to configure a new sync definition from Postgres to SharePoint.

## Steps
1. Create source and destination connection profiles.
2. Select source table and primary key.
3. Review field mappings and transformations.
4. Define sharding policy (optional).
5. Run provisioning to create lists and columns.
6. Trigger first sync run and review results.

## Diagram
```mermaid
flowchart LR
    A[Connections] --> B[Mapping]
    B --> C[Sharding]
    C --> D[Provision]
    D --> E[Run]
    E --> F[Review]
```
