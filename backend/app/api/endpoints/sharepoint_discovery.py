from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.api.endpoints.database_instances import get_db
from app.models.core import SharePointConnection
from app.models.inventory import SharePointSite, SharePointList
from app.services.graph import GraphClient
from app.services.provisioner import SharePointProvisioner
from app.services.sharepoint_discovery import SharePointDiscoveryService

router = APIRouter()

def get_graph_client(connection_id: UUID, db: Session) -> GraphClient:
    conn = db.get(SharePointConnection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="SharePoint connection not found")
    
    # TODO: Refactor secret retrieval to be secure and shared
    import os
    secret = conn.client_secret or os.environ.get("AZURE_CLIENT_SECRET", "")
    if not secret and conn.client_id == os.environ.get("AZURE_CLIENT_ID"):
         secret = os.environ.get("AZURE_CLIENT_SECRET", "")
    
    try:
        return GraphClient(
            tenant_id=conn.tenant_id,
            client_id=conn.client_id,
            client_secret=secret,
            authority_host=conn.authority_host
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph init failed: {str(e)}")

def get_provisioner(connection_id: UUID, db: Session) -> SharePointProvisioner:
    graph = get_graph_client(connection_id, db)
    return SharePointProvisioner(graph)

def get_discovery_service(connection_id: UUID, db: Session) -> SharePointDiscoveryService:
    graph = get_graph_client(connection_id, db)
    return SharePointDiscoveryService(db, graph)

# --- Discovery / Extraction Endpoints ---

@router.post("/{connection_id}/sites/extract")
def extract_sites(
    connection_id: UUID,
    query: str = "*",
    db: Session = Depends(get_db)
):
    """Crawl and store SharePoint sites."""
    svc = get_discovery_service(connection_id, db)
    try:
        sites = svc.extract_sites(connection_id, query)
        return {"count": len(sites), "sites": [s.web_url for s in sites]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Site extraction failed: {str(e)}")

@router.post("/{connection_id}/sites/{site_db_id}/lists/extract")
def extract_lists(
    connection_id: UUID,
    site_db_id: UUID,
    db: Session = Depends(get_db)
):
    """Crawl and store Lists for a specific stored site."""
    svc = get_discovery_service(connection_id, db)
    try:
        lists = svc.extract_lists(site_db_id)
        return {"count": len(lists), "lists": [l.display_name for l in lists]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List extraction failed: {str(e)}")

@router.get("/{connection_id}/sites")
def list_stored_sites(
    connection_id: UUID,
    db: Session = Depends(get_db)
):
    """List sites previously extracted to inventory."""
    sites = db.execute(
        select(SharePointSite).where(SharePointSite.connection_id == connection_id)
    ).scalars().all()
    
    return [
        {
            "id": s.id,
            "hostname": s.hostname,
            "site_path": s.site_path,
            "web_url": s.web_url,
            "status": s.status
        }
        for s in sites
    ]

@router.get("/{connection_id}/sites/{site_db_id}/lists/stored")
def list_stored_lists(
    connection_id: UUID,
    site_db_id: UUID,
    db: Session = Depends(get_db)
):
    """List lists previously extracted for a site."""
    lists = db.execute(
        select(SharePointList).where(SharePointList.site_id == site_db_id)
    ).scalars().all()
    
    return [
        {
            "id": l.id,
            "display_name": l.display_name,
            "description": l.description,
            "is_provisioned": l.is_provisioned
        }
        for l in lists
    ]

# --- Direct Graph Passthrough (Legacy/Realtime) ---

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
