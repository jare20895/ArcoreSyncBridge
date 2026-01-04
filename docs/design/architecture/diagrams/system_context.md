# System Context Diagram (C4 Level 1)

## Overview
Arcore SyncBridge provides bidirectional synchronization between PostgreSQL databases and SharePoint lists with real-time CDC capabilities.

```mermaid
C4Context
    title System Context Diagram for Arcore SyncBridge

    Person(operator, "Data Steward", "Configures sync definitions, manages field mappings, monitors runs")
    Person(admin, "Platform Admin", "Manages database instances, SharePoint connections, and policies")
    Person(user, "Business User", "Views and edits data in SharePoint")

    System(syncbridge, "Arcore SyncBridge", "Bidirectional data synchronization platform with real-time CDC, field mapping, sharding, and drift detection")

    System_Ext(postgres, "PostgreSQL Database", "System of record with logical replication")
    System_Ext(sharepoint, "SharePoint Lists", "Collaboration UI and data entry")
    System_Ext(graph, "Microsoft Graph API", "SharePoint list and item operations")
    System_Ext(aad, "Azure AD", "OAuth 2.0 identity and access management")

    Rel(operator, syncbridge, "Configures sync definitions, field mappings, monitors via Web UI")
    Rel(admin, syncbridge, "Manages connections, database instances, policies via Web UI")
    Rel(user, sharepoint, "Views and edits data")

    Rel(syncbridge, postgres, "Reads changes (SELECT), writes updates (INSERT/UPDATE), streams CDC via logical replication")
    Rel(syncbridge, graph, "CRUD operations via REST API (sites, lists, items, delta queries)")
    Rel(graph, sharepoint, "Persists to SharePoint lists")
    Rel(syncbridge, aad, "Authenticates via OAuth 2.0 client credentials flow")

    UpdateRelStyle(syncbridge, postgres, $offsetY="-20", $offsetX="-50")
    UpdateRelStyle(syncbridge, graph, $offsetY="20", $offsetX="-50")
```

## External Systems

### PostgreSQL Database
- **Role**: System of record (authoritative source)
- **Access**: Read-only for sync (SELECT), write access for bidirectional sync (INSERT/UPDATE)
- **CDC**: Logical replication via pgoutput plugin for real-time streaming
- **Requirements**: PostgreSQL 13+, wal_level=logical, replication slot

### Microsoft Graph API
- **Role**: SharePoint access layer
- **Operations**:
  - Sites: List and resolve SharePoint sites
  - Lists: Create, read, update list metadata
  - Items: CRUD operations on list items
  - Delta: Incremental change tracking via delta tokens
- **Authentication**: OAuth 2.0 client credentials
- **Rate Limits**: 10,000 requests per 10 minutes per tenant

### SharePoint Lists
- **Role**: Collaboration and data entry interface
- **Access**: Via Microsoft Graph API
- **Features**: Rich field types, versioning, permissions, workflows

### Azure AD
- **Role**: Identity provider and access control
- **Flow**: OAuth 2.0 client credentials flow
- **Requirements**: App registration with Sites.ReadWrite.All permission
