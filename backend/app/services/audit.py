import logging
from typing import Any, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.security import Principal
from app.models.platform import AuditLog


logger = logging.getLogger(__name__)


def record_audit_event(
    db: Session,
    request: Request,
    principal: Principal,
    *,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    try:
        db.add(
            AuditLog(
                actor_user_id=principal.user_id,
                actor_email=principal.email,
                actor_role=principal.role,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                details=details,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "audit_log_write_failed action=%s resource_type=%s resource_id=%s request_id=%s",
            action,
            resource_type,
            resource_id,
            getattr(request.state, "request_id", None),
        )
