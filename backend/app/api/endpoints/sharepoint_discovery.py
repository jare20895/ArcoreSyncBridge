from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.endpoints.database_instances import get_db
from app.models.core import SharePointConnection
from app.services.graph import GraphClient
from app.services.provisioner import SharePointProvisioner

router = APIRouter()

def get_provisioner(connection_id: UUID, db: Session) -> SharePointProvisioner:
    conn = db.get(SharePointConnection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="SharePoint connection not found")
    
    # TODO: Refactor secret retrieval to be secure and shared
    import os
    secret = conn.client_secret or os.environ.get("AZURE_CLIENT_SECRET", "")
    if not secret and conn.client_id == os.environ.get("AZURE_CLIENT_ID"):
         secret = os.environ.get("AZURE_CLIENT_SECRET", "")
    
    try:
        graph = GraphClient(
            tenant_id=conn.tenant_id,
            client_id=conn.client_id,
            client_secret=secret,
            authority_host=conn.authority_host
        )
        return SharePointProvisioner(graph)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph init failed: {str(e)}")

@router.get("/{connection_id}/sites/resolve")
def resolve_site(
    connection_id: UUID,
    hostname: str,
    path: str,
    db: Session = Depends(get_db)
):
    prov = get_provisioner(connection_id, db)
    try:
        return prov.get_site(hostname, path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Site resolution failed: {str(e)}")

@router.get("/{connection_id}/sites/{site_id}/lists")
def get_site_lists(
    connection_id: UUID,
    site_id: str,
    db: Session = Depends(get_db)
):
    prov = get_provisioner(connection_id, db)
    try:
        # Re-using internal graph client exposed via provisioner or adding method to provisioner?
        # Provisioner doesn't expose raw "get lists" public method returning simple list, 
        # it has `find_list_by_display_name`.
        # I should add `get_lists` to SharePointProvisioner or call graph directly.
        # Calling graph directly via prov.graph is easiest for now.
        return prov.graph.request("GET", f"/sites/{site_id}/lists")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"List fetch failed: {str(e)}")

@router.get("/{connection_id}/sites/{site_id}/lists/{list_id}/columns")
def get_list_columns(
    connection_id: UUID,
    site_id: str,
    list_id: str,
    db: Session = Depends(get_db)
):
    prov = get_provisioner(connection_id, db)
    try:
        return prov.graph.request("GET", f"/sites/{site_id}/lists/{list_id}/columns")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Column fetch failed: {str(e)}")
