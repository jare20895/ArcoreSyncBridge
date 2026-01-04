# Architecture Diagrams Index

This directory contains comprehensive architecture diagrams for Arcore SyncBridge. All diagrams use Mermaid syntax and are rendered automatically in GitHub and most markdown viewers.

## Quick Links

### System Architecture
- **[System Context Diagram](system_context.md)** - High-level C4 context showing external systems and actors
- **[Component Diagrams](component_diagrams.md)** - Detailed component architecture, API routers, services, and workers
- **[Database Schema Visuals](../database/schema_visuals.md)** - Complete ER diagram and schema patterns

### Sync Flows
- **[One-Way Sync Flow](sync_flow_one_way.md)** - Push sync (Database → SharePoint) with sharding and field mapping
- **[Two-Way Sync Flow](sync_flow_two_way.md)** - Bidirectional sync with conflict resolution and loop prevention
- **[CDC Architecture](cdc_architecture.md)** - Real-time Change Data Capture using PostgreSQL logical replication

## Diagram Categories

### 📊 System Architecture (C4 Model)

#### System Context (Level 1)
Shows Arcore SyncBridge in the context of external systems and users.

**File**: [system_context.md](system_context.md)

**Includes**:
- External system relationships (PostgreSQL, SharePoint, Graph API, Azure AD)
- User personas (Data Steward, Platform Admin, Business User)
- Authentication and authorization flows

#### Component Architecture (Level 3)
Detailed component breakdown showing internal structure.

**File**: [component_diagrams.md](component_diagrams.md)

**Includes**:
- High-level architecture (Frontend, Backend, Storage, External)
- Control plane API components (routers, services)
- Sync worker architecture (Push, Pull, CDC)
- Field mapping & type conversion flow
- Request lifecycle sequence diagram

### 🔄 Sync Flows & Algorithms

#### One-Way Push Sync
Complete flow for Database → SharePoint synchronization.

**File**: [sync_flow_one_way.md](sync_flow_one_way.md)

**Includes**:
- High-level push sync flow
- Detailed sequence diagram
- Push sync decision tree
- Field mapping & type serialization pipeline
- Cursor management & failure recovery
- Sharding logic for multi-list routing
- Error handling & retry strategy
- Performance optimization (batching, rate limiting)

**Key Concepts**:
- Incremental sync with cursor advancement
- Ledger-based INSERT vs UPDATE decision
- Type serialization (datetime, Decimal, UUID → JSON)
- SharePoint GUID resolution
- Cursor advancement only on success

#### Two-Way Bidirectional Sync
Complete flow for Database ↔ SharePoint synchronization.

**File**: [sync_flow_two_way.md](sync_flow_two_way.md)

**Includes**:
- High-level two-way sync flow
- Complete two-way sync sequence (Push + Pull phases)
- Conflict detection & resolution flowchart
- Loop prevention mechanism
- Provenance state machine
- Field mapping directional filtering
- Conflict resolution policies (SOURCE_WINS, DESTINATION_WINS, LATEST_WINS)
- Delta query for pull sync

**Key Concepts**:
- Provenance tracking (PUSH/PULL)
- Content hash comparison
- Conflict detection and resolution
- Directional field mappings (BIDIRECTIONAL, PUSH_ONLY, PULL_ONLY)
- Loop prevention via provenance + hash

#### CDC (Change Data Capture)
Real-time sync using PostgreSQL logical replication.

**File**: [cdc_architecture.md](cdc_architecture.md)

**Includes**:
- CDC architecture diagram
- Detailed WAL streaming sequence
- CDC setup process flowchart
- Replication slot management
- CDC worker state machine
- LSN cursor management
- Backpressure & throttling controls
- Benefits comparison (CDC vs Polling)
- Monitoring queries

**Key Concepts**:
- PostgreSQL logical replication (pgoutput plugin)
- Write-Ahead Log (WAL) streaming
- LSN (Log Sequence Number) cursors
- Replication slot creation and cleanup
- Backpressure controls
- Near real-time synchronization

### 🗄️ Data Models

#### Database Schema Visuals
Complete entity-relationship diagrams for the meta-store.

**File**: [../database/schema_visuals.md](../database/schema_visuals.md)

**Includes**:
- Complete meta-store ER diagram with all entities
- Core entity relationships (Inventory, Sync Config, Runtime)
- Multi-source support pattern
- Multi-target sharding pattern
- Directional field mapping pattern
- Index strategy visualization

**Key Entities**:
- **Inventory**: Application, Database, DatabaseInstance, DatabaseTable, SharePointConnection, SharePointSite, SharePointList
- **Sync Config**: SyncDefinition, SyncSource, SyncTarget, FieldMapping, SyncKeyColumn
- **Runtime**: SyncLedger, SyncCursor, SyncRun, SyncMetric

## Diagram Conventions

### Color Coding
- 🟢 **Green** (#e8f5e9): Database/Source systems
- 🟡 **Yellow** (#fff3e0): Processing/Workers/Services
- 🔵 **Blue** (#e1f5ff): Storage/Ledger/Meta-store
- 🔴 **Pink** (#fce4ec): SharePoint/Target systems
- 🟠 **Orange** (#ffecb3): Policies/Conflict Resolution
- ⚪ **Light colors**: Success states
- 🔴 **Red tints** (#ffccbc): Error/Failed states

### Common Symbols
- `[]` Rectangle: Process or service
- `()` Rounded: Start/End state
- `{}` Diamond: Decision point
- `[()]` Cylinder: Database/Storage
- `-->` Solid arrow: Data flow
- `-.->` Dashed arrow: Conditional/Optional flow

## Usage in Documentation

### Embedding Diagrams
All diagrams use Mermaid syntax. To embed in other documentation:

```markdown
See the [One-Way Sync Flow](docs/design/architecture/diagrams/sync_flow_one_way.md) for details.
```

### Viewing Diagrams
- **GitHub**: Renders automatically
- **VS Code**: Install "Markdown Preview Mermaid Support" extension
- **Other editors**: Most support Mermaid via plugins
- **Online**: https://mermaid.live for editing/testing

## Maintenance

### Updating Diagrams
When architecture changes:
1. Update the relevant diagram file
2. Verify rendering with Mermaid live editor if needed
3. Update this index if new diagrams are added
4. Cross-reference from technical documentation

### Diagram Quality Standards
- **Clarity**: Each diagram should have a single, clear purpose
- **Detail Level**: Match C4 level or flow detail appropriately
- **Labels**: All nodes and edges should be clearly labeled
- **Legend**: Include color coding legend when helpful
- **Consistency**: Use consistent terminology across diagrams

## Related Documentation

- [PHASED_CHECKLIST.md](../../../PHASED_CHECKLIST.md) - Implementation roadmap
- [SYNCArchitecture.md](../../../SYNCArchitecture.md) - Detailed sync logic documentation
- [DATA_MODEL.md](../../../DATA_MODEL.md) - Database schema reference
- [IMPLEMENTATION_SPECS.md](../../../IMPLEMENTATION_SPECS.md) - Technical specifications
- [API Endpoints](../../api/endpoints.md) - REST API reference

## Changelog

### 2025-01-04
- ✅ Updated system_context.md with current actors and external systems
- ✅ Updated component_diagrams.md with complete architecture
- ✅ Created cdc_architecture.md with detailed CDC flow
- ✅ Created sync_flow_one_way.md with push sync details
- ✅ Created sync_flow_two_way.md with bidirectional sync and conflict resolution
- ✅ Updated schema_visuals.md with complete ER diagram
- ✅ Updated this README.md as comprehensive diagram index

### Coverage
All diagrams now reflect:
- Phase 6 completion (Advanced Mapping & Two-Way Fidelity)
- Run history tracking
- Directional field mappings
- Type serialization
- CDC architecture
- Conflict resolution
- Multi-source and multi-target support
