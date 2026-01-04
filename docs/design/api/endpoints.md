# API Endpoints Reference

## Conventions
- **Base URL**: `/api/v1`
- **Authentication**: Bearer token in Authorization header (future enhancement)
- **Content-Type**: `application/json`
- **Response Format**: JSON with camelCase field names
- **Error Format**: `{"detail": "error message"}`

## Health & Status

### Health Check
- **GET** `/health`
- Returns service health status

**Response:**
```json
{
  "status": "ok",
  "service": "arcore-syncbridge"
}
```

### Root
- **GET** `/`
- Returns service identification

## Applications

### List Applications
- **GET** `/api/v1/applications`
- Returns all applications

### Get Application
- **GET** `/api/v1/applications/{application_id}`
- Returns single application

### Create Application
- **POST** `/api/v1/applications`
- Creates a new application

**Request Body:**
```json
{
  "name": "Arcore Finance",
  "owner_team": "Finance Team",
  "description": "Financial management application",
  "status": "ACTIVE"
}
```

### Update Application
- **PUT** `/api/v1/applications/{application_id}`
- Updates an existing application

### Delete Application
- **DELETE** `/api/v1/applications/{application_id}`
- Deletes an application (204 No Content)

## Databases

### List Databases
- **GET** `/api/v1/databases`
- Returns all logical databases

### Get Database
- **GET** `/api/v1/databases/{database_id}`
- Returns single database

### Create Database
- **POST** `/api/v1/databases`
- Creates a new logical database

**Request Body:**
```json
{
  "application_id": "uuid",
  "name": "arcore_finance_db",
  "db_type": "POSTGRES",
  "environment": "PROD",
  "database_name": "arcore_finance",
  "status": "ACTIVE"
}
```

### Update Database
- **PUT** `/api/v1/databases/{database_id}`
- Updates an existing database

### Delete Database
- **DELETE** `/api/v1/databases/{database_id}`
- Deletes a database (204 No Content)

## Database Instances

### List Database Instances
- **GET** `/api/v1/database-instances`
- Returns all database instances

### Get Database Instance
- **GET** `/api/v1/database-instances/{instance_id}`
- Returns single instance with credentials

### Create Database Instance
- **POST** `/api/v1/database-instances`
- Creates a new physical database instance

**Request Body:**
```json
{
  "database_id": "uuid",
  "instance_label": "prod-primary",
  "host": "db01.internal",
  "port": 5432,
  "db_name": "arcore_finance",
  "db_user": "arcore_user",
  "db_password": "encrypted_password",
  "role": "PRIMARY",
  "priority": 1,
  "status": "ACTIVE"
}
```

### Update Database Instance
- **PUT** `/api/v1/database-instances/{instance_id}`
- Updates an existing instance

### Delete Database Instance
- **DELETE** `/api/v1/database-instances/{instance_id}`
- Deletes an instance (204 No Content)

### Test Connection
- **POST** `/api/v1/database-instances/test-connection`
- Tests database connectivity before creating instance

**Request Body:**
```json
{
  "host": "db01.internal",
  "port": 5432,
  "db_name": "arcore_finance",
  "db_user": "arcore_user",
  "db_password": "password"
}
```

- **POST** `/api/v1/database-instances/{instance_id}/test-connection`
- Tests connectivity of existing instance

### Get Schema
- **GET** `/api/v1/database-instances/{instance_id}/schema`
- Returns introspected schema snapshot

## Data Sources (Tables)

### List Tables
- **GET** `/api/v1/data-sources/tables`
- Returns all database tables in inventory

### Extract Tables
- **POST** `/api/v1/data-sources/tables/extract`
- Extracts table list from a database instance

**Request Body:**
```json
{
  "database_id": "uuid",
  "instance_id": "uuid"
}
```

### Extract Table Details
- **POST** `/api/v1/data-sources/tables/extract-details`
- Extracts columns, constraints, indexes for a table

**Request Body:**
```json
{
  "instance_id": "uuid",
  "table_id": "uuid"
}
```

### Get Table Details
- **GET** `/api/v1/data-sources/tables/{table_id}`
- Returns table with columns, constraints, indexes

## SharePoint Connections

### List Connections
- **GET** `/api/v1/sharepoint-connections`
- Returns all SharePoint connections

### Get Connection
- **GET** `/api/v1/sharepoint-connections/{connection_id}`
- Returns single connection

### Create Connection
- **POST** `/api/v1/sharepoint-connections`
- Creates a new SharePoint connection

**Request Body:**
```json
{
  "name": "Production SharePoint",
  "tenant_id": "your-tenant-id",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "authority_host": "https://login.microsoftonline.com",
  "scopes": ["https://graph.microsoft.com/.default"],
  "status": "ACTIVE"
}
```

### Update Connection
- **PUT** `/api/v1/sharepoint-connections/{connection_id}`
- Updates an existing connection

### Delete Connection
- **DELETE** `/api/v1/sharepoint-connections/{connection_id}`
- Deletes a connection (204 No Content)

## Data Targets (SharePoint Sites & Lists)

### List Sites
- **GET** `/api/v1/data-targets/sites`
- Returns all SharePoint sites in inventory

### Resolve Site
- **POST** `/api/v1/data-targets/sites/resolve`
- Resolves a SharePoint site by URL

**Request Body:**
```json
{
  "connection_id": "uuid",
  "site_url": "https://tenant.sharepoint.com/sites/FinanceHub"
}
```

### Extract Sites
- **POST** `/api/v1/data-targets/sites/extract`
- Extracts sites from SharePoint tenant

**Request Body:**
```json
{
  "connection_id": "uuid"
}
```

### List Lists by Site
- **GET** `/api/v1/data-targets/sites/{site_id}/lists`
- Returns all lists for a site

### Extract Lists
- **POST** `/api/v1/data-targets/sites/{site_id}/lists/extract`
- Extracts lists from a SharePoint site

**Request Body:**
```json
{
  "connection_id": "uuid",
  "site_id": "uuid"
}
```

### List Lists by Source
- **GET** `/api/v1/data-targets/lists/by-source`
- Returns lists filtered by source table (for mapping UI)

**Query Params:**
- `connection_id`: UUID
- `site_id`: UUID (optional)

### List Columns
- **GET** `/api/v1/data-targets/lists/{list_id}/columns`
- Returns all columns for a list

### Extract Columns
- **POST** `/api/v1/data-targets/lists/{list_id}/columns/extract`
- Extracts columns from a SharePoint list

**Request Body:**
```json
{
  "connection_id": "uuid",
  "site_id": "uuid"
}
```

## SharePoint Discovery (Legacy - use Data Targets)

### Extract Sites
- **POST** `/api/v1/sharepoint-discovery/{connection_id}/sites/extract`

### Extract Lists
- **POST** `/api/v1/sharepoint-discovery/{connection_id}/sites/{site_db_id}/lists/extract`

### Get Sites
- **GET** `/api/v1/sharepoint-discovery/{connection_id}/sites`

### Get Lists
- **GET** `/api/v1/sharepoint-discovery/{connection_id}/sites/{site_db_id}/lists/stored`

### Resolve Site
- **GET** `/api/v1/sharepoint-discovery/{connection_id}/sites/resolve`

### Get Site Lists
- **GET** `/api/v1/sharepoint-discovery/{connection_id}/sites/{site_id}/lists`

### Get List Columns
- **GET** `/api/v1/sharepoint-discovery/{connection_id}/sites/{site_id}/lists/{list_id}/columns`

## Sync Definitions

### List Sync Definitions
- **GET** `/api/v1/sync-definitions`
- Returns all sync definitions

### Get Sync Definition
- **GET** `/api/v1/sync-definitions/{def_id}`
- Returns single sync definition with related data

### Create Sync Definition
- **POST** `/api/v1/sync-definitions`
- Creates a new sync definition

**Request Body:**
```json
{
  "name": "Projects Sync",
  "source_table_id": "uuid",
  "sync_mode": "TWO_WAY",
  "conflict_policy": "SOURCE_WINS",
  "key_strategy": "PRIMARY_KEY",
  "target_strategy": "SINGLE",
  "cursor_strategy": "UPDATED_AT",
  "cursor_column_id": "uuid",
  "is_enabled": true
}
```

### Update Sync Definition
- **PUT** `/api/v1/sync-definitions/{def_id}`
- Updates an existing sync definition

### Delete Sync Definition
- **DELETE** `/api/v1/sync-definitions/{def_id}`
- Deletes a sync definition (204 No Content)

## Field Mappings

### List Field Mappings
- **GET** `/api/v1/field-mappings/sync-definition/{sync_def_id}`
- Returns all field mappings for a sync definition

### Get Field Mapping
- **GET** `/api/v1/field-mappings/{mapping_id}`
- Returns single field mapping

### Create Field Mapping
- **POST** `/api/v1/field-mappings`
- Creates a new field mapping

**Request Body:**
```json
{
  "sync_def_id": "uuid",
  "source_column_id": "uuid",
  "source_column_name": "budget_amount",
  "target_column_id": "uuid",
  "target_column_name": "BudgetAmount",
  "target_type": "number",
  "sync_direction": "BIDIRECTIONAL",
  "is_system_field": false,
  "is_key": false
}
```

### Update Field Mapping
- **PUT** `/api/v1/field-mappings/{mapping_id}`
- Updates an existing field mapping

### Delete Field Mapping
- **DELETE** `/api/v1/field-mappings/{mapping_id}`
- Deletes a field mapping (204 No Content)

### Bulk Create Field Mappings
- **POST** `/api/v1/field-mappings/sync-definition/{sync_def_id}/bulk`
- Creates multiple field mappings at once

**Request Body:**
```json
{
  "mappings": [
    {
      "source_column_id": "uuid",
      "target_column_id": "uuid",
      "sync_direction": "BIDIRECTIONAL"
    }
  ]
}
```

## Provisioning

### Provision List
- **POST** `/api/v1/provisioning/list`
- Provisions a new SharePoint list with columns

**Request Body:**
```json
{
  "connection_id": "uuid",
  "site_id": "uuid",
  "display_name": "Active Projects",
  "description": "List of active projects",
  "template": "genericList",
  "columns": [
    {
      "name": "ProjectCode",
      "type": "text",
      "required": true
    },
    {
      "name": "BudgetAmount",
      "type": "number",
      "required": false
    }
  ]
}
```

### List Connections
- **GET** `/api/v1/provisioning/connections`
- Returns available SharePoint connections for provisioning

### Debug Token
- **GET** `/api/v1/provisioning/debug-token/{connection_id}`
- Returns Graph API token details for debugging

## Operations (Ops)

### Trigger Sync
- **POST** `/api/v1/ops/sync/{sync_def_id}`
- Triggers a manual sync run (push and/or ingress)

**Response:**
```json
{
  "push": {
    "processed_count": 120,
    "success_count": 118,
    "failed_count": 2
  },
  "ingress": {
    "processed_count": 5,
    "delta_token": "new_token"
  }
}
```

### Trigger Ingress
- **POST** `/api/v1/ops/ingress/{sync_def_id}`
- Triggers ingress (pull) sync only

### Reset Cursors
- **DELETE** `/api/v1/ops/sync/{sync_def_id}/cursors`
- Deletes all sync cursors for a definition

**Response:**
```json
{
  "message": "Reset 2 cursor(s) for sync definition",
  "deleted_count": 2
}
```

### Generate Drift Report
- **POST** `/api/v1/ops/drift-report`
- Generates drift detection report

**Request Body:**
```json
{
  "sync_def_id": "uuid",
  "check_type": "ORPHANED_ITEMS"
}
```

### Trigger Failover
- **POST** `/api/v1/ops/failover`
- Promotes secondary database instance to primary

**Request Body:**
```json
{
  "new_primary_instance_id": "uuid",
  "old_primary_instance_id": "uuid"
}
```

## Sync Runs

### List Sync Runs
- **GET** `/api/v1/runs`
- Returns all sync run history

**Query Params:**
- `sync_def_id`: UUID (optional filter)
- `status`: RUNNING|COMPLETED|FAILED (optional filter)
- `run_type`: PUSH|INGRESS|CDC (optional filter)

**Response:**
```json
[
  {
    "id": "uuid",
    "sync_def_id": "uuid",
    "run_type": "PUSH",
    "status": "COMPLETED",
    "start_time": "2025-01-03T12:00:00Z",
    "end_time": "2025-01-03T12:05:30Z",
    "items_processed": 120,
    "items_failed": 2,
    "error_message": null
  }
]
```

## Replication (CDC)

### List Replication Slots
- **GET** `/api/v1/replication/slots/{instance_id}`
- Returns PostgreSQL replication slots

### Create Replication Slot
- **POST** `/api/v1/replication/slots`
- Creates a new replication slot for CDC

**Request Body:**
```json
{
  "instance_id": "uuid",
  "slot_name": "arcore_sync_slot",
  "plugin": "pgoutput"
}
```

### Delete Replication Slot
- **DELETE** `/api/v1/replication/slots`
- Deletes a replication slot

**Request Body:**
```json
{
  "instance_id": "uuid",
  "slot_name": "arcore_sync_slot"
}
```

## Moves

### Move Item
- **POST** `/api/v1/moves/item`
- Moves a SharePoint item between lists

**Request Body:**
```json
{
  "sync_def_id": "uuid",
  "source_identity_hash": "sha256_hash",
  "old_list_id": "uuid",
  "new_list_id": "uuid",
  "reason": "Sharding rule changed"
}
```

## Admin UI (SQLAdmin)
- **Web UI**: `/admin`
- Provides direct database access for advanced operations
- Tables: DatabaseInstance, SharePointConnection, SyncDefinition, SyncSource, SyncTarget, FieldMapping, SyncLedgerEntry, SyncCursor, MoveAuditLog

## Error Responses

All endpoints return standard error responses:

**400 Bad Request:**
```json
{
  "detail": "Validation error message"
}
```

**404 Not Found:**
```json
{
  "detail": "Resource not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to process request: error details"
}
```
