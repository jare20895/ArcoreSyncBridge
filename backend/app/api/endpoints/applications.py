"""
API endpoints for Application CRUD operations.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.inventory import Application
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse

router = APIRouter()


@router.get("/", response_model=List[ApplicationResponse])
def list_applications(db: Session = Depends(get_db)):
    """List all applications."""
    applications = db.query(Application).order_by(Application.name).all()
    return applications


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(application_id: UUID, db: Session = Depends(get_db)):
    """Get a specific application by ID."""
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.post("/", response_model=ApplicationResponse, status_code=201)
def create_application(application_data: ApplicationCreate, db: Session = Depends(get_db)):
    """Create a new application."""
    application = Application(**application_data.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: UUID,
    application_data: ApplicationUpdate,
    db: Session = Depends(get_db)
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
    return application


@router.delete("/{application_id}", status_code=204)
def delete_application(application_id: UUID, db: Session = Depends(get_db)):
    """Delete an application."""
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    db.delete(application)
    db.commit()
    return None
