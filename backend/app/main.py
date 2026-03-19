import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqladmin import Admin

from app.api.endpoints import database_instances, sharepoint_connections, provisioning, sharepoint_discovery, sync_definitions, moves, ops, replication, runs, applications, databases, data_sources, data_targets, field_mappings, schedules, cdc, health, metrics
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import engine, SessionLocal
from app.services.cdc_manager import CDCManager
from app.admin import (
    DatabaseInstanceAdmin,
    SharePointConnectionAdmin,
    SyncDefinitionAdmin,
    SyncSourceAdmin,
    SyncTargetAdmin,
    FieldMappingAdmin,
    SyncLedgerEntryAdmin,
    SyncCursorAdmin,
    MoveAuditLogAdmin
)

configure_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    Handles startup and shutdown of CDC services.
    """
    # Startup: Initialize CDC Manager and start all enabled CDC
    logger.info("Application startup: Initializing CDC Manager...")
    db = SessionLocal()
    try:
        cdc_manager = CDCManager(db)
        started_count = cdc_manager.start_all_enabled_cdc()
        logger.info(f"Started CDC for {started_count} database instances")
        # Store in app state for dependency injection
        app.state.cdc_manager = cdc_manager
    except Exception as e:
        logger.error(f"Failed to start CDC on startup: {e}")
        app.state.cdc_manager = None

    yield  # Application is running

    # Shutdown: Stop all CDC threads
    logger.info("Application shutdown: Stopping CDC Manager...")
    if hasattr(app.state, 'cdc_manager') and app.state.cdc_manager:
        try:
            app.state.cdc_manager.stop_all()
            logger.info("CDC Manager stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping CDC Manager: {e}")

    db.close()


app = FastAPI(title="Arcore SyncBridge", version="0.1.0", lifespan=lifespan)

# Setup SQLAdmin
admin = Admin(app, engine)
admin.add_view(DatabaseInstanceAdmin)
admin.add_view(SharePointConnectionAdmin)
admin.add_view(SyncDefinitionAdmin)
admin.add_view(SyncSourceAdmin)
admin.add_view(SyncTargetAdmin)
admin.add_view(FieldMappingAdmin)
admin.add_view(SyncLedgerEntryAdmin)
admin.add_view(SyncCursorAdmin)
admin.add_view(MoveAuditLogAdmin)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()
        
        logger.info(
            "request_started method=%s path=%s request_id=%s",
            request.method,
            request.url.path,
            request_id,
        )
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed method=%s path=%s request_id=%s duration_seconds=%.4f",
            request.method,
            request.url.path,
            request_id,
            process_time,
        )
        
        return response

app.add_middleware(RequestIDMiddleware)

app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(databases.router, prefix="/api/v1/databases", tags=["databases"])
app.include_router(database_instances.router, prefix="/api/v1/database-instances", tags=["database-instances"])
app.include_router(data_sources.router, prefix="/api/v1/data-sources", tags=["data-sources"])
app.include_router(sharepoint_connections.router, prefix="/api/v1/sharepoint-connections", tags=["sharepoint-connections"])
app.include_router(provisioning.router, prefix="/api/v1/provisioning", tags=["provisioning"])
app.include_router(sharepoint_discovery.router, prefix="/api/v1/sharepoint-discovery", tags=["sharepoint-discovery"])
app.include_router(data_targets.router, prefix="/api/v1/data-targets", tags=["data-targets"])
app.include_router(sync_definitions.router, prefix="/api/v1/sync-definitions", tags=["sync-definitions"])
app.include_router(field_mappings.router, prefix="/api/v1/field-mappings", tags=["field-mappings"])
app.include_router(moves.router, prefix="/api/v1/moves", tags=["moves"])
app.include_router(ops.router, prefix="/api/v1/ops", tags=["ops"])
app.include_router(replication.router, prefix="/api/v1/replication", tags=["replication"])
app.include_router(runs.router, prefix="/api/v1/runs", tags=["runs"])
app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["schedules"])
app.include_router(cdc.router, prefix="/api/v1/cdc", tags=["cdc"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "arcore-syncbridge"}

@app.get("/")
async def root():
    return {"message": "Arcore SyncBridge Control Plane"}
