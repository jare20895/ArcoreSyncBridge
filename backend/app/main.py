import time
import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqladmin import Admin

from app.api.endpoints import database_instances, sharepoint_connections, provisioning, sharepoint_discovery, sync_definitions, moves, ops
from app.db.session import engine
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

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Arcore SyncBridge", version="0.1.0")

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
    allow_origins=["*"], # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()
        
        logger.info(f"Request started: {request.method} {request.url.path} [ID: {request_id}]")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        logger.info(f"Request completed: {request.method} {request.url.path} [ID: {request_id}] - {process_time:.4f}s")
        
        return response

app.add_middleware(RequestIDMiddleware)

app.include_router(database_instances.router, prefix="/api/v1/database-instances", tags=["database-instances"])
app.include_router(sharepoint_connections.router, prefix="/api/v1/sharepoint-connections", tags=["sharepoint-connections"])
app.include_router(provisioning.router, prefix="/api/v1/provisioning", tags=["provisioning"])
app.include_router(sharepoint_discovery.router, prefix="/api/v1/sharepoint-discovery", tags=["sharepoint-discovery"])
app.include_router(sync_definitions.router, prefix="/api/v1/sync-definitions", tags=["sync-definitions"])
app.include_router(moves.router, prefix="/api/v1/moves", tags=["moves"])
app.include_router(ops.router, prefix="/api/v1/ops", tags=["ops"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "arcore-syncbridge"}

@app.get("/")
async def root():
    return {"message": "Arcore SyncBridge Control Plane"}
