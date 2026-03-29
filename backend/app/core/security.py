import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any, Optional

import jwt
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


def _resolve_display_name(claims: dict[str, Any]) -> str:
    for claim_name in settings.auth_jwt_display_name_claims:
        value = claims.get(claim_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    fallback_email = _resolve_email(claims)
    return fallback_email.split("@", 1)[0]


def _resolve_email(claims: dict[str, Any]) -> str:
    for claim_name in settings.auth_jwt_email_claims:
        value = claims.get(claim_name)
        if isinstance(value, str) and value.strip():
            return value.lower().strip()
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="JWT token is missing a supported email claim",
    )


def _decode_jwt_token(token: str) -> dict[str, Any]:
    decode_kwargs: dict[str, Any] = {
        "algorithms": settings.auth_jwt_algorithms,
    }
    if settings.AUTH_JWT_AUDIENCE:
        decode_kwargs["audience"] = settings.AUTH_JWT_AUDIENCE
    if settings.AUTH_JWT_ISSUER:
        decode_kwargs["issuer"] = settings.AUTH_JWT_ISSUER

    try:
        if settings.AUTH_JWT_JWKS_URL:
            signing_key = jwt.PyJWKClient(settings.AUTH_JWT_JWKS_URL).get_signing_key_from_jwt(token).key
            return jwt.decode(token, signing_key, **decode_kwargs)

        secret = settings.AUTH_JWT_SECRET or settings.SECRET_KEY
        return jwt.decode(token, secret, **decode_kwargs)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid bearer token: {exc}",
        ) from exc


def _resolve_principal_for_email(
    db: Session,
    *,
    email: str,
    auth_mode: str,
    display_name: Optional[str] = None,
) -> Principal:
    user = db.query(AppUser).filter(AppUser.email == email).one_or_none()
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
            auth_mode=auth_mode,
        )

    if not settings.AUTH_AUTO_PROVISION_USERS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not provisioned",
        )

    user = AppUser(
        email=email,
        display_name=display_name or email.split("@", 1)[0],
        role="platform_admin" if email in settings.auth_bootstrap_emails else settings.AUTH_DEFAULT_ROLE,
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
        auth_mode=auth_mode,
    )


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
        return _resolve_principal_for_email(
            db,
            email=normalized_email,
            auth_mode="header",
        )

    if settings.AUTH_MODE == "jwt":
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer token is required",
            )

        token = authorization.split(" ", 1)[1].strip()
        claims = _decode_jwt_token(token)
        email = _resolve_email(claims)
        display_name = _resolve_display_name(claims)
        return _resolve_principal_for_email(
            db,
            email=email,
            auth_mode="jwt",
            display_name=display_name,
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
