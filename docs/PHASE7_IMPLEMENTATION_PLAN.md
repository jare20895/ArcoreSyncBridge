# Phase 7 Implementation Plan (Epics and Tickets)

Phase 7 focuses on scheduled sync automation (intervals + cron), real-time CDC push sync, and in-app monitoring/alerting.

## Prerequisites
- Phase 6 completed: Directional mapping, system field support, field mapping CRUD
- Manual sync working reliably with robust error handling
- Celery + Redis infrastructure configured
- PostgreSQL logical replication enabled

## User Requirements
- **Scheduling**: Support both simple intervals (every X minutes) AND cron expressions (complex schedules)
- **CDC**: Push only (Database → SharePoint real-time)
- **Monitoring**: In-app alerts only (no email/webhook notifications initially)

## Technology Stack
- **Scheduler**: Celery Beat with celery-sqlalchemy-scheduler (database-backed dynamic schedules)
- **Concurrent Prevention**: Redis distributed locks (prevent duplicate runs)
- **CDC Architecture**: Dedicated worker process for long-running consumer loop
- **Monitoring**: Database-backed alerts with frontend polling

---

## Epic 1: Database Schema & Migrations

**Goal**: Extend schema to support scheduling, CDC tracking, and alerting

### Tickets

**P7-01: Create Scheduling Migration**
- Add scheduling fields to SyncDefinition:
  - `schedule_enabled: bool`
  - `schedule_type: str` (INTERVAL or CRON)
  - `schedule_interval_seconds: int`
  - `schedule_cron_expression: str`
  - `schedule_timezone: str`
  - `last_scheduled_run: datetime`
  - `next_scheduled_run: datetime`
- Update SyncRun model:
  - `trigger_type: str` (MANUAL, SCHEDULED, CDC)
  - `celery_task_id: str`
- Files: `backend/alembic/versions/XXXX_add_scheduling_support.py`

**P7-02: Create CeleryPeriodicTask Table**
- Compatible with celery-sqlalchemy-scheduler
- Fields: name, task, interval_seconds, crontab fields, args, enabled, sync_def_id
- Foreign key to SyncDefinition with CASCADE delete
- Files: `backend/app/models/core.py`

**P7-03: Create ScheduledSyncAudit Table**
- Track scheduled runs, skips, and failures
- Fields: sync_def_id, scheduled_time, actual_start_time, status, skip_reason, sync_run_id
- Indexes on sync_def_id and status
- Files: `backend/app/models/core.py`

**P7-04: Create SyncAlert Table**
- In-app alert system
- Fields: sync_def_id, alert_type, severity, message, metadata, is_resolved, created_at, resolved_at
- Alert types: CONSECUTIVE_FAILURES, CDC_LAG, SCHEDULE_SKIP
- Severity levels: WARNING, ERROR, CRITICAL
- Files: `backend/app/models/core.py`

**P7-05: Update Schemas**
- Add schedule fields to SyncDefinitionBase and SyncDefinitionUpdate
- Files: `backend/app/schemas/sync_definition.py`

**Success Criteria**:
- Migration runs cleanly on dev/staging databases
- All new tables have proper indexes and foreign keys
- ORM models align with schema definitions

---

## Epic 2: Scheduled Sync Backend (Week 1 - Foundation)

**Goal**: Implement basic scheduled sync with interval support

### Tickets

**P7-06: Install Dependencies**
- Add to requirements.txt:
  - `celery-sqlalchemy-scheduler>=0.4.0`
  - `croniter>=2.0.0`
- Files: `backend/requirements.txt`

**P7-07: Configure Celery Beat**
- Update celery_app.py with Beat scheduler config
- Add DatabaseScheduler with DATABASE_URL
- Add task routing for run_scheduled_sync
- Files: `backend/app/worker/celery_app.py`

**P7-08: Implement Concurrent Prevention**
- Create SingletonTask base class with Redis lock
- Lock key: `sync_lock:{sync_def_id}`
- 1-hour timeout with non-blocking acquire
- Log skips to ScheduledSyncAudit
- Files: `backend/app/worker/tasks.py`

**P7-09: Create Scheduled Sync Task**
- `run_scheduled_sync(sync_def_id)` task
- Acquire Redis lock (skip if already running)
- Check schedule_enabled and is_paused
- Update last_scheduled_run timestamp
- Call existing run_push_sync and run_ingress_sync with trigger_type="SCHEDULED"
- Files: `backend/app/worker/tasks.py`

**P7-10: Update Existing Sync Tasks**
- Add `trigger_type` parameter to run_push_sync and run_ingress_sync
- Pass trigger_type and celery_task_id to RunHistoryService.start_run()
- Default trigger_type="MANUAL" for backward compatibility
- Files: `backend/app/worker/tasks.py`

**P7-11: Update Run History Service**
- Update start_run() signature to accept trigger_type and celery_task_id
- Store values in SyncRun record
- Files: `backend/app/services/run_history.py`

**Success Criteria**:
- Scheduled sync task can be triggered manually
- Redis lock prevents concurrent execution
- Trigger type tracked in run history
- Skipped runs logged to audit table

---

## Epic 3: Schedule Management Service & API

**Goal**: Implement schedule CRUD with interval and cron support

### Tickets

**P7-12: Implement ScheduleService (Interval Support)**
- `enable_schedule()` - Creates/updates CeleryPeriodicTask
- `disable_schedule()` - Sets enabled=False
- `delete_schedule()` - Removes periodic task
- `_calculate_next_run()` - Calculates next run time
- Interval validation (minimum 60 seconds)
- Files: `backend/app/services/schedule_service.py` (NEW)

**P7-13: Add Cron Support to ScheduleService**
- Parse cron expressions with croniter
- Validate cron syntax
- Set crontab fields in CeleryPeriodicTask
- Handle timezone conversion
- Files: `backend/app/services/schedule_service.py`

**P7-14: Implement ScheduleAuditService**
- `log_skip()` - Records skipped runs
- `get_recent_audits()` - Retrieves audit history
- Files: `backend/app/services/schedule_audit.py` (NEW)

**P7-15: Create Schedule API Endpoints**
- POST /api/schedules/{sync_def_id}/enable
- POST /api/schedules/{sync_def_id}/disable
- DELETE /api/schedules/{sync_def_id}
- GET /api/schedules/{sync_def_id}/audit
- Request/response schemas with validation
- Files: `backend/app/api/endpoints/schedules.py` (NEW)

**P7-16: Register Schedule Router**
- Add schedules router to main.py
- Tag: "schedules"
- Files: `backend/app/main.py`

**Success Criteria**:
- Schedules can be created with interval or cron
- Next run time calculated correctly
- API endpoints return proper errors for invalid input
- Audit logs track all schedule events

---

## Epic 4: CDC Integration Backend (Week 3)

**Goal**: Integrate real-time CDC push sync

### Tickets

**P7-17: Implement CDC Manager Service**
- Manage CDC service threads per database instance
- `start_cdc_for_instance()` - Starts CDC thread
- `stop_cdc_for_instance()` - Stops CDC thread
- `start_all_enabled_cdc()` - Starts CDC for all enabled instances
- Thread registry: `{instance_id: (CDCService, Thread, StopEvent)}`
- Files: `backend/app/services/cdc_manager.py` (NEW)

**P7-18: Create CDC Consumer Worker**
- Standalone worker process (python -m app.worker.cdc_consumer_worker)
- Instantiates CDCConsumer from existing code
- Calls consumer.run() blocking loop
- Handles SIGINT/SIGTERM for graceful shutdown
- Files: `backend/app/worker/cdc_consumer_worker.py` (NEW)

**P7-19: Add CDC Startup Integration**
- Add lifespan handler to main.py
- Create CDCManager on startup
- Call start_all_enabled_cdc()
- Stop all CDC threads on shutdown
- Files: `backend/app/main.py`

**P7-20: Create CDC Control API**
- POST /api/cdc/{sync_def_id}/enable-cdc
- POST /api/cdc/{sync_def_id}/disable-cdc
- Enable/disable cdc_enabled flag
- Start/stop CDC manager threads
- Files: `backend/app/api/endpoints/cdc.py` (NEW)

**P7-21: Register CDC Router**
- Add cdc router to main.py
- Tag: "cdc"
- Files: `backend/app/main.py`

**P7-22: Enhance Replication Endpoints**
- POST /replication/{instance_id}/assign-slot
- Assign replication slot to database instance
- Update instance.replication_slot_name
- Files: `backend/app/api/endpoints/replication.py`

**Success Criteria**:
- CDC threads start/stop cleanly
- Database changes pushed to SharePoint in real-time
- Echo prevention works (PULL provenance check)
- CDC events respect sharding rules

---

## Epic 5: Infrastructure & Docker (Week 1)

**Goal**: Add worker services to Docker Compose

### Tickets

**P7-23: Add Celery Worker Service**
- Build from backend Dockerfile
- Command: celery -A app.worker.celery_app worker --loglevel=info --queues=sync_queue,default
- Environment: REDIS_URL, DATABASE_URL, etc.
- Depends on: db, redis
- Files: `docker-compose.yml`

**P7-24: Add Celery Beat Service**
- Build from backend Dockerfile
- Command: celery -A app.worker.celery_app beat --loglevel=info
- Same environment as worker
- Depends on: db, redis
- Files: `docker-compose.yml`

**P7-25: Add CDC Consumer Service**
- Build from backend Dockerfile
- Command: python -m app.worker.cdc_consumer_worker
- Same environment as worker
- Depends on: db, redis
- Files: `docker-compose.yml`

**P7-26: Update Environment Configuration**
- Add DATABASE_URL to .env
- Add CELERY_BROKER_URL to .env
- Add CELERY_RESULT_BACKEND to .env
- Files: `backend/.env`, `.env.example`

**Success Criteria**:
- All services start via docker-compose up
- Worker connects to Redis and Postgres
- Beat scheduler connects to database
- CDC consumer connects to Redis stream

---

## Epic 6: Frontend - Schedule UI (Week 2)

**Goal**: Build schedule configuration UI

### Tickets

**P7-27: Create ScheduleConfig Component**
- Radio toggle: Interval vs Cron
- Interval input: minutes (converted to seconds)
- Cron input: text field with format hints
- Display next scheduled run time
- Enable/Disable buttons
- Call enableSchedule() and disableSchedule() APIs
- Files: `frontend/src/components/ScheduleConfig.tsx` (NEW)

**P7-28: Create CDC Toggle Component**
- Toggle button for CDC enabled/disabled
- Status indicator (green when enabled)
- Call enableCDC() and disableCDC() APIs
- Files: `frontend/src/components/CDCToggle.tsx` (NEW)

**P7-29: Update Sync Definition Detail Page**
- Add ScheduleConfig section
- Add CDCToggle section
- Wire up API handlers
- Refresh sync definition after changes
- Files: `frontend/src/pages/sync-definitions/[id].tsx`

**P7-30: Update API Service**
- Add enableSchedule(syncDefId, config)
- Add disableSchedule(syncDefId)
- Add getScheduleAudit(syncDefId)
- Add enableCDC(syncDefId)
- Add disableCDC(syncDefId)
- Files: `frontend/src/services/api.ts`

**P7-31: Enhance Run History Page**
- Add Trigger column (MANUAL/SCHEDULED/CDC)
- Color-coded badges (gray/blue/purple)
- Files: `frontend/src/pages/runs.tsx`

**Success Criteria**:
- Users can create interval schedules via UI
- Users can create cron schedules via UI
- Next run time displays correctly
- CDC can be enabled/disabled per sync definition
- Run history shows trigger type

---

## Epic 7: Monitoring & Alerting (Week 4)

**Goal**: Implement in-app alert system

### Tickets

**P7-32: Implement Alert Service**
- `check_consecutive_failures()` - Creates alert if 3+ consecutive failures
- `get_active_alerts()` - Returns unresolved alerts
- `resolve_alert()` - Marks alert as resolved
- Files: `backend/app/services/alert_service.py` (NEW)

**P7-33: Integrate Alert Checks**
- Call check_consecutive_failures() in run_scheduled_sync after completion
- Files: `backend/app/worker/tasks.py`

**P7-34: Create Alert API Endpoints**
- GET /api/alerts - Get active alerts
- POST /api/alerts/{alert_id}/resolve - Resolve alert
- Files: `backend/app/api/endpoints/alerts.py` (NEW)

**P7-35: Register Alert Router**
- Add alerts router to main.py
- Tag: "alerts"
- Files: `backend/app/main.py`

**P7-36: Create Alert Banner Component**
- Fixed position (top-right)
- Poll /api/alerts every 30s
- Color-coded by severity (red/orange/yellow)
- Dismiss button (calls resolve API)
- Files: `frontend/src/components/AlertBanner.tsx` (NEW)

**P7-37: Integrate Alert Banner**
- Add to main layout or App component
- Files: `frontend/src/pages/_app.tsx` or layout component

**Success Criteria**:
- Alerts created after 3 consecutive failures
- Alerts display in UI with correct severity colors
- Users can dismiss alerts
- Alerts auto-refresh every 30 seconds

---

## Epic 8: Testing & Documentation

**Goal**: Comprehensive testing and user documentation

### Tickets

**P7-38: Unit Tests - Schedule Service**
- Test enable/disable schedule
- Test interval vs cron validation
- Test next_run calculation
- Test concurrent execution prevention
- Files: `backend/tests/test_schedule_service.py` (NEW)

**P7-39: Unit Tests - CDC Manager**
- Test start/stop CDC threads
- Test instance filtering
- Test multiple sync definitions per instance
- Files: `backend/tests/test_cdc_manager.py` (NEW)

**P7-40: Integration Tests - Scheduled Sync**
- Create sync def → enable schedule → wait → verify SyncRun created
- Test concurrent prevention (manual + scheduled overlap)
- Files: `backend/tests/integration/test_scheduled_sync.py` (NEW)

**P7-41: Integration Tests - CDC**
- Enable CDC → insert row → verify SharePoint item created
- Test echo prevention (PULL provenance)
- Test sharding with CDC events
- Files: `backend/tests/integration/test_cdc_realtime.py` (NEW)

**P7-42: User Guide - Scheduling**
- How to create interval schedules
- How to create cron schedules
- Schedule management best practices
- Files: `docs/guides/user/scheduling.md` (NEW)

**P7-43: User Guide - CDC Setup**
- Replication slot creation
- Enabling CDC per sync definition
- Monitoring CDC lag
- Troubleshooting CDC issues
- Files: `docs/guides/user/cdc_setup.md` (enhance existing)

**P7-44: Admin Guide - Operations**
- Managing Celery workers
- Monitoring scheduled syncs
- Replication slot maintenance
- Alert management
- Files: `docs/guides/admin/scheduled_sync_operations.md` (NEW)

**Success Criteria**:
- >80% code coverage for new services
- All integration tests pass
- Documentation reviewed and approved
- User guide tested with real use cases

---

## Implementation Timeline

### Week 1: Foundation + Basic Scheduling
**Goal**: Working scheduled sync with intervals

- Epic 1: Database Schema (P7-01 to P7-05)
- Epic 2: Scheduled Sync Backend (P7-06 to P7-11)
- Epic 5: Infrastructure (P7-23 to P7-26)

**Milestone**: Scheduled sync executes every X minutes

### Week 2: Enhanced Scheduling + Frontend
**Goal**: Full scheduling with cron + UI

- Epic 3: Schedule Management (P7-12 to P7-16)
- Epic 6: Frontend UI (P7-27 to P7-31)

**Milestone**: Users can create/manage schedules via UI

### Week 3: CDC Integration
**Goal**: Real-time CDC push sync

- Epic 4: CDC Integration (P7-17 to P7-22)

**Milestone**: Database changes push to SharePoint in real-time

### Week 4: Monitoring + Polish
**Goal**: Production-ready system

- Epic 7: Monitoring & Alerting (P7-32 to P7-37)
- Epic 8: Testing & Documentation (P7-38 to P7-44)

**Milestone**: Production-ready automated sync system

---

## Success Criteria

### Functional Requirements
- ✅ Schedule CRUD via UI (interval + cron)
- ✅ Scheduled syncs execute on time (± 1 minute)
- ✅ Concurrent execution prevention works (no duplicate runs)
- ✅ CDC detects DB changes and pushes to SharePoint in real-time (<5s latency)
- ✅ In-app alerts notify of consecutive failures
- ✅ Run history distinguishes manual vs scheduled vs CDC
- ✅ All Docker services start cleanly
- ✅ Audit logs track skipped runs and reasons

### Performance Requirements
- P95 scheduled sync trigger latency: <60 seconds
- P95 CDC end-to-end latency: <5 seconds
- Zero duplicate writes across restarts
- Cursor checkpoints consistent and resumable

### Operational Requirements
- CDC lag monitoring and alerting
- Replication slot management procedures documented
- Disaster recovery plan includes scheduled sync state
- Rollback procedures tested in staging

---

## Key Architectural Decisions

### Decision 1: Celery Beat over APScheduler
**Rationale**: Unified infrastructure, database-backed schedules, production-ready, horizontal scaling support

**Trade-offs**: Additional dependency, slightly more complex than APScheduler

### Decision 2: Redis Locks for Concurrent Prevention
**Rationale**: Distributed, timeout-protected, works across worker nodes

**Trade-offs**: Dependency on Redis availability, lock timeout tuning required

### Decision 3: Separate CDC Worker Process
**Rationale**: Isolates long-running consumer from Celery task model, simpler restart/recovery

**Trade-offs**: Additional process to monitor

### Decision 4: Push-Only CDC Initially
**Rationale**: SharePoint lacks reliable CDC (webhooks unreliable), scheduled ingress handles pull

**Trade-offs**: Not truly bidirectional real-time (future: add SharePoint webhooks)

### Decision 5: In-App Alerts Only
**Rationale**: User requirement, simpler implementation, extensible to email/webhook later

**Trade-offs**: Requires users to check app

---

## Risks & Mitigations

### Risk: CDC Lag with High Volume
**Impact**: CDC consumer can't keep up with change volume
**Mitigation**:
- Batch processing (10 events at a time)
- Backpressure monitoring
- Horizontal scaling (multiple CDC consumers)
- Monitor Redis stream length

### Risk: Replication Slot Disk Usage
**Impact**: Slots hold WAL logs, can fill disk if consumer stops
**Mitigation**:
- Monitor slot lag (pg_replication_slots.restart_lsn)
- Alert if lag > 1GB
- Automatic slot drop if inactive > 24 hours
- Document slot management procedures

### Risk: Schedule Drift
**Impact**: Celery Beat may not fire exactly on time
**Mitigation**:
- Accept minor drift (< 1 minute)
- Use task expires to skip late runs
- Monitor schedule accuracy via audit logs

### Risk: Lock Timeout False Positives
**Impact**: Lock timeout could cause skips even when no run is active
**Mitigation**:
- Set reasonable lock timeout (1 hour)
- Log lock acquisition failures with context
- Allow manual override to force run
- Monitor skip rate

---

## Future Enhancements (Post-Phase 7)

### Phase 8 Candidates

1. **Advanced Scheduling**:
   - Blackout windows (don't run during business hours)
   - Conditional schedules (only if data changed)
   - Schedule templates and presets

2. **Bidirectional CDC**:
   - SharePoint webhooks for pull CDC
   - Multi-table CDC transactions
   - CDC event replay for debugging

3. **Enhanced Monitoring**:
   - Prometheus/Grafana integration
   - Slack/Teams notifications
   - SLA tracking (% of syncs on time)

4. **Performance Optimization**:
   - Parallel sync execution (multiple tables)
   - Incremental CDC batching
   - Connection pooling improvements

5. **Advanced Alerting**:
   - Custom alert rules (threshold, conditions)
   - Alert escalation workflows
   - Email/webhook notification channels

6. **Governance**:
   - Audit log for schedule changes
   - Schedule approval workflow
   - Role-based access to scheduling

---

## Dependencies

### External Dependencies
- Redis (Celery broker)
- PostgreSQL 15+ with logical replication
- Docker Compose for local development

### Internal Dependencies
- Phase 6 completed (directional mapping, field CRUD)
- Robust manual sync implementation
- Run history tracking functional

### Team Dependencies
- DevOps: Docker infrastructure setup
- QA: Integration testing support
- Documentation: User guide review
