"""
API endpoints for Application CRUD operations.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.core.security import EDITOR_ROLES, VIEWER_ROLES, Principal, require_roles
from app.db.session import get_db
from app.models.inventory import Application
from app.schemas.api import ApiResponse, MessageResponse
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.services.audit import record_audit_event

router = APIRouter()


@router.get("/", response_model=ApiResponse[List[ApplicationResponse]])
def list_applications(
    request: Request,
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
    q: Optional[str] = Query(None, description="Search by name, owner team, or description"),
    status: Optional[str] = Query(None, description="Filter by status"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all applications."""
    query = db.query(Application)

    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            Application.name.ilike(search)
            | Application.owner_team.ilike(search)
            | Application.description.ilike(search)
        )
    if status:
        query = query.filter(Application.status == status)

    total = query.count()
    applications = query.order_by(Application.name).offset(offset).limit(limit).all()
    return success_response(request, applications, meta={"total": total, "limit": limit, "offset": offset})


@router.get("/{application_id}", response_model=ApiResponse[ApplicationResponse])
def get_application(
    application_id: UUID,
    request: Request,
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db),
):
    """Get a specific application by ID."""
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return success_response(request, application)


@router.post("/", response_model=ApiResponse[ApplicationResponse], status_code=201)
def create_application(
    application_data: ApplicationCreate,
    request: Request,
    principal: Principal = Depends(require_roles(*EDITOR_ROLES)),
    db: Session = Depends(get_db),
):
    """Create a new application."""
    application = Application(**application_data.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    record_audit_event(
        db,
        request,
        principal,
        action="application.create",
        resource_type="application",
        resource_id=str(application.id),
        details=application_data.model_dump(),
    )
    return success_response(request, application)


@router.put("/{application_id}", response_model=ApiResponse[ApplicationResponse])
def update_application(
    application_id: UUID,
    application_data: ApplicationUpdate,
    request: Request,
    principal: Principal = Depends(require_roles(*EDITOR_ROLES)),
    db: Session = Depends(get_db),
):
    """Update an existing application."""
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Update only provided fields
    update_data = application_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)
    record_audit_event(
        db,
        request,
        principal,
        action="application.update",
        resource_type="application",
        resource_id=str(application.id),
        details=update_data,
    )
    return success_response(request, application)


@router.delete("/{application_id}", response_model=ApiResponse[MessageResponse])
def delete_application(
    application_id: UUID,
    request: Request,
    principal: Principal = Depends(require_roles(*EDITOR_ROLES)),
    db: Session = Depends(get_db),
):
    """Delete an application."""
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    db.delete(application)
    db.commit()
    record_audit_event(
        db,
        request,
        principal,
        action="application.delete",
        resource_type="application",
        resource_id=str(application_id),
        details={"name": application.name},
    )
    return success_response(request, {"message": "Application deleted"})
