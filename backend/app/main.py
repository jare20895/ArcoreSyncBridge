import time
import uuid
import logging
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Arcore SyncBridge", version="0.1.0")

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

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "arcore-syncbridge"}

@app.get("/")
async def root():
    return {"message": "Arcore SyncBridge Control Plane"}
