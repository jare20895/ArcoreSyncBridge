# Getting Started with Arcore SyncBridge

This guide walks you through setting up your first data synchronization between a PostgreSQL database and SharePoint.

## Prerequisites

### System Requirements
- PostgreSQL 13+ with superuser access (for CDC features)
- Azure AD app registration with Microsoft Graph permissions
- SharePoint site with list creation permissions
- Python 3.11+ and Node.js 18+ (for local development)

### Required Permissions

**PostgreSQL:**
- Read access to source tables
- Superuser access for CDC/replication setup (optional, for real-time sync)

**Microsoft Graph API:**
- Sites.Read.All
- Sites.ReadWrite.All
- User.Read (for authentication)

### Azure AD App Registration
1. Go to Azure Portal → Azure Active Directory → App registrations
2. Create new registration or use existing app
3. Note the **Tenant ID** and **Client ID**
4. Create a **Client Secret** under "Certificates & secrets"
5. Grant API permissions: Microsoft Graph → Application permissions → Sites.ReadWrite.All
6. Admin consent required for application permissions

## Quick Start Workflow

### Step 1: Set Up Your Application and Database

1. **Navigate to the UI**: Open http://localhost:3000 (frontend) after starting services
2. **Create an Application**:
   - Go to **Connections** → **Applications**
   - Click "New Application"
   - Fill in:
     - Name: e.g., "Arcore Finance"
     - Owner Team: e.g., "Finance Team"
     - Description: Brief description of the application
     - Status: ACTIVE
   - Save

3. **Create a Logical Database**:
   - Go to **Connections** → **Databases**
   - Click "New Database"
   - Fill in:
     - Application: Select the application created above
     - Name: e.g., "arcore_finance_db"
     - Database Type: POSTGRES
     - Environment: PROD (or DEV/STAGING)
     - Database Name: The actual PostgreSQL database name
     - Status: ACTIVE
   - Save

4. **Create a Database Instance**:
   - Go to **Connections** → **Database Instances**
   - Click "New Instance"
   - Fill in:
     - Database: Select the database created above
     - Instance Label: e.g., "prod-primary"
     - Host: Database server hostname or IP
     - Port: 5432 (default PostgreSQL port)
     - Database Name: The actual database name
     - Username: Database user with read permissions
     - Password: Database password
     - Role: PRIMARY
     - Priority: 1
     - Status: ACTIVE
   - Click "Test Connection" to verify
   - Save

### Step 2: Set Up SharePoint Connection

1. **Create a SharePoint Connection**:
   - Go to **Connections** → **SharePoint Connections**
   - Click "New Connection"
   - Fill in:
     - Name: e.g., "Production SharePoint"
     - Tenant ID: From Azure AD
     - Client ID: From Azure AD app registration
     - Client Secret: From Azure AD app registration
     - Authority Host: https://login.microsoftonline.com (default)
     - Status: ACTIVE
   - Save

### Step 3: Discover Data Sources

1. **Extract Database Tables**:
   - Go to **Data Sources** → **Inventory**
   - Click "Extract Tables"
   - Select your database and instance
   - Click "Extract" - this introspects the database schema
   - View the list of available tables

2. **Select a Table and Extract Details**:
   - Click on a table from the list
   - Click "Extract Details" to load columns, constraints, and indexes
   - Review the table structure

### Step 4: Discover Data Targets

1. **Extract SharePoint Sites**:
   - Go to **Data Targets** → **Sites**
   - Click "Extract Sites"
   - Select your SharePoint connection
   - Click "Extract" - this discovers SharePoint sites in your tenant
   - View the list of available sites

2. **Extract SharePoint Lists** (if using existing lists):
   - Click on a site from the list
   - Click "Extract Lists"
   - View the lists available in that site
   - Click on a list to view its columns

3. **OR Provision a New List** (if creating a new list):
   - We'll do this in the next step during sync definition setup

### Step 5: Create a Sync Definition

1. **Create the Sync Definition**:
   - Go to **Sync Definitions**
   - Click "New Sync Definition"
   - Fill in:
     - Name: e.g., "Projects Sync"
     - Source Table: Select the table you extracted
     - Sync Mode:
       - ONE_WAY_PUSH (DB → SharePoint)
       - TWO_WAY (DB ↔ SharePoint)
     - Conflict Policy: SOURCE_WINS (Postgres authoritative)
     - Key Strategy: PRIMARY_KEY (or UNIQUE_CONSTRAINT, COMPOSITE_COLUMNS)
     - Target Strategy: SINGLE (or CONDITIONAL for sharding)
     - Cursor Strategy: UPDATED_AT (requires timestamp column)
     - Cursor Column: Select the timestamp column for incremental sync
     - Enabled: Yes
   - Save

2. **Add a Sync Target**:
   - In the sync definition detail page, go to "Targets" tab
   - Click "Add Target"
   - Select:
     - SharePoint Connection
     - Site
     - List (existing) OR click "Provision New List"
   - If provisioning new list:
     - Display Name: e.g., "Active Projects"
     - Description: Brief description
     - Template: genericList
   - Save

### Step 6: Configure Field Mappings

1. **Use the Interactive Mapping Editor**:
   - In the sync definition detail page, go to "Field Mappings" tab
   - The editor shows:
     - Left column: Database columns from your source table
     - Right column: SharePoint columns from your target list
   - Click "Add Mapping" to create mappings:
     - Source Column: Select database column
     - Target Column: Select SharePoint column (or create new)
     - Target Type: text, number, datetime, boolean
     - Sync Direction:
       - BIDIRECTIONAL: Syncs in both directions
       - PUSH_ONLY: Only DB → SharePoint
       - PULL_ONLY: Only SharePoint → DB (for system fields)
     - System Field: Check if this is a SharePoint readonly field (ID, Created, Modified)
   - Repeat for all columns you want to sync
   - Save

**Example Mappings:**
- `project_code` (DB) → `Title` (SP) - BIDIRECTIONAL
- `budget_amount` (DB) → `BudgetAmount` (SP) - BIDIRECTIONAL
- `start_date` (DB) → `StartDate` (SP) - BIDIRECTIONAL
- `updated_at` (DB) → `Modified` (SP) - PULL_ONLY, System Field

### Step 7: Run Your First Sync

1. **Manual Sync Run**:
   - In the sync definition detail page
   - Click "Run Sync Now"
   - The sync will execute immediately
   - You'll see a summary with:
     - Items processed
     - Items succeeded
     - Items failed
     - Errors (if any)

2. **View Run History**:
   - Go to **Runs & Ledger** → **Run History**
   - Filter by status (all, completed, failed, running)
   - View details:
     - Duration
     - Item counts
     - Error messages
   - Click on sync definition name to navigate to details

### Step 8: Monitor and Maintain

1. **View Sync Ledger**:
   - Go to `/admin` (SQLAdmin interface)
   - Select "SyncLedgerEntry"
   - View all synchronized items with:
     - Source identity
     - SharePoint item ID
     - Content hash
     - Last sync time
     - Provenance (PUSH/PULL)

2. **Check for Drift**:
   - Use the Drift Report API endpoint
   - Identifies orphaned SharePoint items with no matching source
   - Identifies missing items that should exist in SharePoint

3. **Reset Cursor** (if needed):
   - In sync definition detail page
   - Click "Reset Cursor" button
   - Confirm the action
   - Next sync will process all rows (full resync)

## Advanced Features

### Sharding (Multi-List Routing)

To route different rows to different SharePoint lists based on conditions:

1. Set **Target Strategy** to CONDITIONAL
2. Add multiple Sync Targets (different lists)
3. Define **Sharding Policy** in the sync definition:
```json
{
  "rules": [
    {"if": "status == 'Active'", "target_list_id": "active-list-uuid"},
    {"if": "status == 'Closed'", "target_list_id": "closed-list-uuid"},
    {"if": "budget_amount >= 1000000", "target_list_id": "large-projects-uuid"}
  ],
  "default_target_list_id": "active-list-uuid"
}
```

### Two-Way Sync with Conflict Resolution

1. Set **Sync Mode** to TWO_WAY
2. Set **Conflict Policy**:
   - SOURCE_WINS: Postgres changes always win
   - DESTINATION_WINS: SharePoint changes always win
   - LATEST_WINS: Compare timestamps, newest wins
3. Configure field mappings with appropriate sync directions
4. Sync will automatically:
   - Push changes from DB to SharePoint (PUSH operation)
   - Pull changes from SharePoint to DB (INGRESS operation)
   - Detect conflicts using ledger provenance
   - Apply conflict resolution policy

### Real-Time CDC (Change Data Capture)

For near real-time sync using PostgreSQL logical replication:

1. **Set up PostgreSQL replication** (requires superuser):
   ```sql
   ALTER SYSTEM SET wal_level = 'logical';
   -- Restart PostgreSQL
   ```

2. **Create replication slot** via API:
   - POST `/api/v1/replication/slots`
   - Body: `{"instance_id": "uuid", "slot_name": "arcore_sync_slot", "plugin": "pgoutput"}`

3. **Configure CDC in sync definition**:
   - Set Cursor Strategy to LSN
   - Enable CDC in worker configuration

4. **Monitor CDC lag**:
   - View replication slot status
   - Check run history for CDC operations

## Troubleshooting

### Sync Returning 0 Items
- **Check cursor value**: May be ahead of available data
- **Solution**: Reset cursor and re-run sync

### SharePoint 404 "List not found"
- **Issue**: Database UUID used instead of SharePoint GUID
- **Solution**: System automatically resolves correct GUID from inventory

### Type Serialization Errors
- **Error**: "Object of type date is not JSON serializable"
- **Solution**: System automatically converts date/datetime/Decimal/UUID to JSON types

### Field Mapping Direction Confusion
- Use **BIDIRECTIONAL** for most fields
- Use **PUSH_ONLY** for calculated fields or DB-managed fields
- Use **PULL_ONLY** for SharePoint system fields (ID, Created, Modified)

### Authentication Failures
- Verify Azure AD app credentials
- Check that client secret hasn't expired
- Ensure API permissions are granted and admin consented

## Next Steps

- Review the [SYNCArchitecture.md](../../SYNCArchitecture.md) for detailed sync logic
- Check [API Endpoints](../api/endpoints.md) for programmatic access
- See [Operational Runbook](../../guides/admin/operational_runbook.md) for production operations
- Review [Disaster Recovery](../../guides/admin/disaster_recovery.md) for backup procedures
