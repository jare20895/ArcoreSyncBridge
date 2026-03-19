from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from app.core.config import settings

VIEWER_ROLES = ("viewer", "operator", "editor", "admin", "platform_admin")
EDITOR_ROLES = ("editor", "admin", "platform_admin")
OPERATOR_ROLES = ("operator", "admin", "platform_admin")
ADMIN_ROLES = ("admin", "platform_admin")


class Principal(BaseModel):
    email: str
    role: str
    auth_mode: str


def get_current_principal(request: Request) -> Principal:
    if settings.AUTH_MODE == "disabled":
        return Principal(
            email="system@local",
            role=settings.AUTH_DISABLED_ROLE,
            auth_mode="disabled",
        )

    if settings.AUTH_MODE == "header":
        email = request.headers.get(settings.AUTH_HEADER_EMAIL)
        role = request.headers.get(settings.AUTH_HEADER_ROLE)

        if not email or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication headers are required",
            )

        return Principal(email=email, role=role, auth_mode="header")

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
