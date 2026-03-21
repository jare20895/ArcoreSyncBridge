import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.platform import AppUser

VIEWER_ROLES = ("viewer", "operator", "editor", "admin", "platform_admin")
EDITOR_ROLES = ("editor", "admin", "platform_admin")
OPERATOR_ROLES = ("operator", "admin", "platform_admin")
ADMIN_ROLES = ("admin", "platform_admin")


class Principal(BaseModel):
    user_id: Optional[uuid.UUID] = None
    email: str
    role: str
    auth_mode: str


def get_current_principal(
    request: Request,
    db: Session = Depends(get_db),
) -> Principal:
    if settings.AUTH_MODE == "disabled":
        return Principal(
            email="system@local",
            role=settings.AUTH_DISABLED_ROLE,
            auth_mode="disabled",
        )

    if settings.AUTH_MODE == "header":
        email = request.headers.get(settings.AUTH_HEADER_EMAIL)
        normalized_email = email.lower().strip() if email else None

        if not normalized_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication email header is required",
            )

        user = db.query(AppUser).filter(AppUser.email == normalized_email).one_or_none()
        if user:
            if user.status != "ACTIVE":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is disabled",
                )
            user.last_login_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            return Principal(
                user_id=user.id,
                email=user.email,
                role=user.role,
                auth_mode="header",
            )

        if not settings.AUTH_AUTO_PROVISION_USERS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not provisioned",
            )

        user = AppUser(
            email=normalized_email,
            display_name=normalized_email.split("@", 1)[0],
            role="platform_admin" if normalized_email in settings.auth_bootstrap_emails else settings.AUTH_DEFAULT_ROLE,
            status="ACTIVE",
            last_login_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return Principal(
            user_id=user.id,
            email=user.email,
            role=user.role,
            auth_mode="header",
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unsupported auth mode: {settings.AUTH_MODE}",
    )


def require_roles(*allowed_roles: str) -> Callable[[Principal], Principal]:
    allowed = set(allowed_roles)

    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return principal

    return dependency
