import os
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.core.security import OPERATOR_ROLES, VIEWER_ROLES, Principal, require_roles
from app.db.session import get_db
from app.models.core import SharePointConnection
from app.models.inventory import SharePointSite, SharePointList, SharePointColumn
from app.schemas.catalog import (
    SharePointSiteResolveRequest,
    SharePointSiteRead,
    SharePointListRead,
    SharePointColumnRead,
)
from app.schemas.api import ApiResponse
from app.services.graph import GraphClient
from app.services.secrets import resolve_sharepoint_client_secret
from app.services.sharepoint_discovery import SharePointDiscoveryService
from app.services.audit import record_audit_event

router = APIRouter()


def _get_graph_client(connection: SharePointConnection) -> GraphClient:
    secret = resolve_sharepoint_client_secret(connection)
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


@router.get("/lists/by-source", response_model=ApiResponse[List[SharePointListRead]])
def get_lists_by_source(
    source_table_id: UUID,
    request: Request,
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
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
    return success_response(request, results)


@router.get("/sites", response_model=ApiResponse[List[SharePointSiteRead]])
def list_sites(
    request: Request,
    connection_id: Optional[UUID] = Query(None, description="SharePoint connection ID"),
    q: Optional[str] = Query(None, description="Search by hostname or site path"),
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db),
):
    query = db.query(SharePointSite)
    if connection_id:
        query = query.filter(SharePointSite.connection_id == connection_id)
    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            SharePointSite.hostname.ilike(search)
            | SharePointSite.site_path.ilike(search)
        )
    if status:
        query = query.filter(SharePointSite.status == status)

    total = query.count()
    rows = query.order_by(SharePointSite.hostname, SharePointSite.site_path).offset(offset).limit(limit).all()
    return success_response(request, rows, meta={"total": total, "limit": limit, "offset": offset})


@router.post("/sites/resolve", response_model=ApiResponse[SharePointSiteRead])
def resolve_site(
    payload: SharePointSiteResolveRequest,
    request: Request,
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db),
):
    connection = db.get(SharePointConnection, payload.connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="SharePoint connection not found")

    graph = _get_graph_client(connection)
    try:
        site_info = graph.request("GET", f"/sites/{payload.hostname}:{payload.site_path}")
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
        existing.hostname = payload.hostname
        existing.site_path = payload.site_path
        existing.web_url = site_info.get("webUrl", existing.web_url)
        existing.status = "ACTIVE"
        site = existing
    else:
        site = SharePointSite(
            connection_id=connection.id,
            tenant_id=connection.tenant_id,
            hostname=payload.hostname,
            site_path=payload.site_path,
            site_id=site_info.get("id"),
            web_url=site_info.get("webUrl", ""),
            status="ACTIVE",
        )
        db.add(site)

    db.commit()
    db.refresh(site)
    record_audit_event(
        db,
        request,
        principal,
        action="inventory.sharepoint_site.resolve",
        resource_type="sharepoint_site",
        resource_id=str(site.id),
        details={"connection_id": str(payload.connection_id), "hostname": payload.hostname, "site_path": payload.site_path},
    )
    return success_response(request, site)


@router.post("/sites/extract", response_model=ApiResponse[List[SharePointSiteRead]])
def extract_sites(
    connection_id: UUID,
    request: Request,
    query: str = Query("*", description="Search query for sites"),
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
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
        record_audit_event(
            db,
            request,
            principal,
            action="inventory.sharepoint_sites.extract",
            resource_type="sharepoint_connection",
            resource_id=str(connection_id),
            details={"query": query, "site_count": len(results)},
        )
        return success_response(request, results)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Site search failed: {str(e)}")


@router.get("/sites/{site_id}/lists", response_model=ApiResponse[List[SharePointListRead]])
def list_site_lists(
    site_id: UUID,
    request: Request,
    q: Optional[str] = Query(None, description="Search by list display name or template"),
    is_provisioned: Optional[bool] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db),
):
    site = db.get(SharePointSite, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="SharePoint site not found")

    query = db.query(SharePointList).filter(
        SharePointList.site_id == site_id,
        SharePointList.status == "ACTIVE",
    )
    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            SharePointList.display_name.ilike(search)
            | SharePointList.template.ilike(search)
        )
    if is_provisioned is not None:
        query = query.filter(SharePointList.is_provisioned == is_provisioned)

    total = query.count()
    rows = (
        query.order_by(SharePointList.display_name)
        .offset(offset)
        .limit(limit)
        .all()
    )
    list_ids = [row.id for row in rows]
    column_counts = {}
    if list_ids:
        counts = (
            db.query(SharePointColumn.list_id, func.count(SharePointColumn.id))
            .filter(SharePointColumn.list_id.in_(list_ids))
            .group_by(SharePointColumn.list_id)
            .all()
        )
        column_counts = {list_id: int(count or 0) for list_id, count in counts}

    results = [
        SharePointListRead(
            id=sp_list.id,
            site_id=sp_list.site_id,
            list_id=sp_list.list_id,
            display_name=sp_list.display_name,
            description=sp_list.description,
            template=sp_list.template,
            is_provisioned=sp_list.is_provisioned,
            last_provisioned_at=sp_list.last_provisioned_at,
            columns_count=column_counts.get(sp_list.id, 0),
        )
        for sp_list in rows
    ]
    return success_response(request, results, meta={"total": total, "limit": limit, "offset": offset})


@router.post("/sites/{site_id}/lists/extract", response_model=ApiResponse[List[SharePointListRead]])
def extract_site_lists(
    site_id: UUID,
    request: Request,
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
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

    result = _serialize_lists(db, site.id)
    record_audit_event(
        db,
        request,
        principal,
        action="inventory.sharepoint_lists.extract",
        resource_type="sharepoint_site",
        resource_id=str(site.id),
        details={"list_count": len(result)},
    )
    return success_response(request, result)


@router.get("/lists/{list_id}/columns", response_model=ApiResponse[List[SharePointColumnRead]])
def list_list_columns(
    list_id: UUID,
    request: Request,
    q: Optional[str] = Query(None, description="Search by column name or type"),
    is_readonly: Optional[bool] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: Principal = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db),
):
    sp_list = db.get(SharePointList, list_id)
    if not sp_list:
        raise HTTPException(status_code=404, detail="SharePoint list not found")

    query = db.query(SharePointColumn).filter(SharePointColumn.list_id == sp_list.id)
    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            SharePointColumn.column_name.ilike(search)
            | SharePointColumn.column_type.ilike(search)
        )
    if is_readonly is not None:
        query = query.filter(SharePointColumn.is_readonly == is_readonly)

    total = query.count()
    columns = query.order_by(SharePointColumn.column_name).offset(offset).limit(limit).all()
    return success_response(
        request,
        [SharePointColumnRead.model_validate(col) for col in columns],
        meta={"total": total, "limit": limit, "offset": offset},
    )


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

@router.post("/lists/{list_id}/columns/extract", response_model=ApiResponse[List[SharePointColumnRead]])
def extract_list_columns(
    list_id: UUID,
    request: Request,
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
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
    result = [SharePointColumnRead.model_validate(col) for col in columns]
    record_audit_event(
        db,
        request,
        principal,
        action="inventory.sharepoint_columns.extract",
        resource_type="sharepoint_list",
        resource_id=str(list_id),
        details={"column_count": len(result)},
    )
    return success_response(request, result)
