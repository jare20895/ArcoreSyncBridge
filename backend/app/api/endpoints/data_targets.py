import os
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.core import SharePointConnection
from app.models.inventory import SharePointSite, SharePointList, SharePointColumn
from app.schemas.catalog import (
    SharePointSiteResolveRequest,
    SharePointSiteRead,
    SharePointListRead,
    SharePointColumnRead,
)
from app.services.graph import GraphClient
from app.services.sharepoint_discovery import SharePointDiscoveryService

router = APIRouter()


def _get_graph_client(connection: SharePointConnection) -> GraphClient:
    secret = connection.client_secret or os.environ.get("AZURE_CLIENT_SECRET", "")
    if not secret and connection.client_id == os.environ.get("AZURE_CLIENT_ID"):
        secret = os.environ.get("AZURE_CLIENT_SECRET", "")
    if not secret:
        raise HTTPException(status_code=400, detail="SharePoint connection secret is missing")
    return GraphClient(
        tenant_id=connection.tenant_id,
        client_id=connection.client_id,
        client_secret=secret,
        authority_host=connection.authority_host,
    )


def _serialize_lists(db: Session, site_id: UUID) -> List[SharePointListRead]:
    stmt = (
        select(SharePointList, func.count(SharePointColumn.id).label("columns_count"))
        .outerjoin(SharePointColumn, SharePointColumn.list_id == SharePointList.id)
        .where(
            SharePointList.site_id == site_id,
            SharePointList.status == "ACTIVE"
        )
        .group_by(SharePointList.id)
        .order_by(SharePointList.display_name)
    )
    results = db.execute(stmt).all()
    lists = []
    for sp_list, columns_count in results:
        lists.append(
            SharePointListRead(
                id=sp_list.id,
                site_id=sp_list.site_id,
                list_id=sp_list.list_id,
                display_name=sp_list.display_name,
                description=sp_list.description,
                template=sp_list.template,
                is_provisioned=sp_list.is_provisioned,
                last_provisioned_at=sp_list.last_provisioned_at,
                columns_count=int(columns_count or 0),
            )
        )
    return lists


@router.get("/lists/by-source", response_model=List[SharePointListRead])
def get_lists_by_source(
    source_table_id: UUID,
    db: Session = Depends(get_db),
):
    """Get SharePoint lists that were provisioned from a specific source table."""
    lists = (
        db.query(SharePointList)
        .filter(
            SharePointList.source_table_id == source_table_id,
            SharePointList.status == "ACTIVE"
        )
        .all()
    )
    
    results = []
    for sp_list in lists:
        # Calculate column count manually since _serialize_lists logic is complex to reuse directly here without site_id
        count = db.scalar(
            select(func.count(SharePointColumn.id))
            .where(SharePointColumn.list_id == sp_list.id)
        )
        
        results.append(
            SharePointListRead(
                id=sp_list.id,
                site_id=sp_list.site_id,
                list_id=sp_list.list_id,
                display_name=sp_list.display_name,
                description=sp_list.description,
                template=sp_list.template,
                is_provisioned=sp_list.is_provisioned,
                last_provisioned_at=sp_list.last_provisioned_at,
                columns_count=count or 0,
            )
        )
    return results


@router.get("/sites", response_model=List[SharePointSiteRead])
def list_sites(
    connection_id: Optional[UUID] = Query(None, description="SharePoint connection ID"),
    db: Session = Depends(get_db),
):
    query = db.query(SharePointSite)
    if connection_id:
        query = query.filter(SharePointSite.connection_id == connection_id)
    return query.order_by(SharePointSite.hostname, SharePointSite.site_path).all()


@router.post("/sites/resolve", response_model=SharePointSiteRead)
def resolve_site(
    request: SharePointSiteResolveRequest,
    db: Session = Depends(get_db),
):
    connection = db.get(SharePointConnection, request.connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="SharePoint connection not found")

    graph = _get_graph_client(connection)
    try:
        site_info = graph.request("GET", f"/sites/{request.hostname}:{request.site_path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Site resolution failed: {str(e)}")

    existing = (
        db.query(SharePointSite)
        .filter(
            SharePointSite.connection_id == connection.id,
            SharePointSite.site_id == site_info.get("id"),
        )
        .one_or_none()
    )

    if existing:
        existing.hostname = request.hostname
        existing.site_path = request.site_path
        existing.web_url = site_info.get("webUrl", existing.web_url)
        existing.status = "ACTIVE"
        site = existing
    else:
        site = SharePointSite(
            connection_id=connection.id,
            tenant_id=connection.tenant_id,
            hostname=request.hostname,
            site_path=request.site_path,
            site_id=site_info.get("id"),
            web_url=site_info.get("webUrl", ""),
            status="ACTIVE",
        )
        db.add(site)

    db.commit()
    db.refresh(site)
    return site


@router.post("/sites/extract", response_model=List[SharePointSiteRead])
def extract_sites(
    connection_id: UUID,
    query: str = Query("*", description="Search query for sites"),
    db: Session = Depends(get_db),
):
    """Search and extract multiple sites from Graph API."""
    connection = db.get(SharePointConnection, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="SharePoint connection not found")

    graph = _get_graph_client(connection)
    discovery = SharePointDiscoveryService(db, graph)
    try:
        # Use service
        results = discovery.extract_sites(connection_id, query)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Site search failed: {str(e)}")


@router.get("/sites/{site_id}/lists", response_model=List[SharePointListRead])
def list_site_lists(
    site_id: UUID,
    db: Session = Depends(get_db),
):
    site = db.get(SharePointSite, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="SharePoint site not found")
    return _serialize_lists(db, site_id)


@router.post("/sites/{site_id}/lists/extract", response_model=List[SharePointListRead])
def extract_site_lists(
    site_id: UUID,
    db: Session = Depends(get_db),
):
    site = db.get(SharePointSite, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="SharePoint site not found")

    connection = db.get(SharePointConnection, site.connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="SharePoint connection not found")

    graph = _get_graph_client(connection)
    discovery = SharePointDiscoveryService(db, graph)
    
    try:
        discovery.extract_lists(site.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"List discovery failed: {str(e)}")

    return _serialize_lists(db, site.id)


@router.get("/lists/{list_id}/columns", response_model=List[SharePointColumnRead])
def list_list_columns(
    list_id: UUID,
    db: Session = Depends(get_db),
):
    sp_list = db.get(SharePointList, list_id)
    if not sp_list:
        raise HTTPException(status_code=404, detail="SharePoint list not found")

    columns = (
        db.query(SharePointColumn)
        .filter(SharePointColumn.list_id == sp_list.id)
        .order_by(SharePointColumn.column_name)
        .all()
    )
    return [SharePointColumnRead.model_validate(col) for col in columns]


def _resolve_column_type(item: dict) -> str:
    """
    Determine column type from Graph API column definition.
    Graph API returns type as a key in the resource (e.g. 'text': {}, 'number': {}).
    """
    # Map of Graph API property keys to our simplified type string
    type_map = {
        "text": "Text",
        "number": "Number",
        "boolean": "Boolean",
        "dateTime": "DateTime",
        "choice": "Choice",
        "lookup": "Lookup",
        "personOrGroup": "Person",
        "currency": "Currency",
        "calculated": "Calculated",
        "computed": "Computed", # Added Computed
        "hyperlinkOrPicture": "Url",
        "geolocation": "Geolocation",
        "term": "Taxonomy",
        "thumbnail": "Thumbnail",
        "approvalStatus": "ApprovalStatus",
        "contentApprovalStatus": "ContentApprovalStatus"
    }
    
    for key, value in type_map.items():
        if key in item:
            return value
            
    # Fallback: Check known system field names if no type facet is found
    name = item.get("name", "")
    if name == "ID":
        return "Counter"
    if name == "ContentType":
        return "ContentType"
    if name == "Attachments":
        return "Attachments"
    if name in ["LinkTitle", "LinkTitleNoMenu", "DocIcon", "Edit"]:
        return "Computed"
    if name.startswith("_"): # Hidden system fields often
        return "System"

    # Fallback to columnType if present (less reliable)
    if "columnType" in item:
        return item["columnType"]
        
    return "unknown"

@router.post("/lists/{list_id}/columns/extract", response_model=List[SharePointColumnRead])
def extract_list_columns(
    list_id: UUID,
    db: Session = Depends(get_db),
):
    sp_list = db.get(SharePointList, list_id)
    if not sp_list:
        raise HTTPException(status_code=404, detail="SharePoint list not found")

    site = db.get(SharePointSite, sp_list.site_id)
    if not site:
        raise HTTPException(status_code=404, detail="SharePoint site not found")

    connection = db.get(SharePointConnection, site.connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="SharePoint connection not found")

    graph = _get_graph_client(connection)
    try:
        payload = graph.request("GET", f"/sites/{site.site_id}/lists/{sp_list.list_id}/columns")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Column discovery failed: {str(e)}")

    db.query(SharePointColumn).filter(SharePointColumn.list_id == sp_list.id).delete(synchronize_session=False)

    for item in payload.get("value", []):
        column_name = item.get("name") or item.get("displayName")
        if not column_name:
            continue
        
        column_type = _resolve_column_type(item)
        
        db.add(
            SharePointColumn(
                list_id=sp_list.id,
                column_name=column_name,
                column_type=column_type,
                is_required=bool(item.get("required", False)),
                is_readonly=bool(item.get("readOnly", False)),
            )
        )

    db.commit()

    columns = (
        db.query(SharePointColumn)
        .filter(SharePointColumn.list_id == sp_list.id)
        .order_by(SharePointColumn.column_name)
        .all()
    )
    return [SharePointColumnRead.model_validate(col) for col in columns]
