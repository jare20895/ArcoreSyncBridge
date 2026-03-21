from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.core.security import ADMIN_ROLES, Principal, get_current_principal, require_roles
from app.db.session import get_db
from app.models.platform import AppUser
from app.schemas.api import ApiResponse
from app.schemas.auth import AppUserCreate, AppUserRead, AppUserUpdate, PrincipalRead
from app.services.audit import record_audit_event


router = APIRouter()


@router.get("/me", response_model=ApiResponse[PrincipalRead])
def get_me(request: Request, principal: Principal = Depends(get_current_principal)):
    return success_response(request, principal)


@router.get("/admin-check", response_model=ApiResponse[PrincipalRead])
def admin_check(
    request: Request,
    principal: Principal = Depends(require_roles("admin", "platform_admin")),
):
    return success_response(request, principal)


@router.get("/users", response_model=ApiResponse[List[AppUserRead]])
def list_users(
    request: Request,
    _: Principal = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    users = db.query(AppUser).order_by(AppUser.email).all()
    return success_response(request, users)


@router.post("/users", response_model=ApiResponse[AppUserRead], status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AppUserCreate,
    request: Request,
    principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    existing = db.query(AppUser).filter(AppUser.email == payload.email.lower()).one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    user = AppUser(
        email=payload.email.lower(),
        display_name=payload.display_name,
        role=payload.role,
        status=payload.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    record_audit_event(
        db,
        request,
        principal,
        action="auth.user.create",
        resource_type="app_user",
        resource_id=str(user.id),
        details={"email": user.email, "role": user.role, "status": user.status},
    )
    return success_response(request, user)


@router.patch("/users/{user_id}", response_model=ApiResponse[AppUserRead])
def update_user(
    user_id: UUID,
    payload: AppUserUpdate,
    request: Request,
    principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    user = db.get(AppUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "email" in update_data:
        update_data["email"] = update_data["email"].lower()
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    record_audit_event(
        db,
        request,
        principal,
        action="auth.user.update",
        resource_type="app_user",
        resource_id=str(user.id),
        details=update_data,
    )
    return success_response(request, user)
