from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.core.security import ADMIN_ROLES, Principal, require_roles
from app.db.session import get_db
from app.models.platform import AuditLog
from app.schemas.api import ApiResponse
from app.schemas.audit import AuditLogRead


router = APIRouter()


@router.get("/", response_model=ApiResponse[List[AuditLogRead]])
def list_audit_logs(
    request: Request,
    _: Principal = Depends(require_roles(*ADMIN_ROLES)),
    actor_email: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)

    if actor_email:
        query = query.filter(AuditLog.actor_email == actor_email.lower())
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)

    rows = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return success_response(request, rows)
