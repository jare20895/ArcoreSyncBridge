from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.api.responses import success_response
from app.api.endpoints.database_instances import get_db
from app.core.security import ADMIN_ROLES, OPERATOR_ROLES, Principal, require_roles
from app.models.core import SharePointConnection
from app.schemas.api import ApiResponse
from app.schemas.provisioning import ProvisionRequest, ProvisionResponse
from app.services.graph import GraphClient
from app.services.provisioner import SharePointProvisioner
from app.services.secrets import resolve_sharepoint_client_secret
from app.services.audit import record_audit_event
from app.core.config import settings
import jwt

router = APIRouter()

@router.post("/list", response_model=ApiResponse[ProvisionResponse])
def provision_sharepoint_list(
    payload: ProvisionRequest,
    request: Request,
    principal: Principal = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db)
):
    # 1. Fetch Connection Details
    conn = db.get(SharePointConnection, payload.connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="SharePoint connection not found")

    if conn.status != "ACTIVE":
         raise HTTPException(status_code=400, detail="SharePoint connection is not active")

    # 2. Initialize Graph Client
    secret = resolve_sharepoint_client_secret(conn)

    try:
        graph = GraphClient(
            tenant_id=conn.tenant_id,
            client_id=conn.client_id,
            client_secret=secret,
            authority_host=conn.authority_host
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize Graph client: {str(e)}")

    # 3. Run Provisioner
    try:
        provisioner = SharePointProvisioner(graph)
        
        # Resolve Site ID first
        site_info = provisioner.get_site(payload.hostname, payload.site_path)
        site_id = site_info["id"]

        result = provisioner.provision_table_to_list(
            site_id=site_id,
            pg_columns=payload.columns,
            list_display_name=payload.list_name,
            description=payload.description,
            skip_columns=payload.skip_columns,
            column_configurations=payload.column_configurations
        )

        # 4. Upsert Inventory Record
        # We must ensure the Site exists in inventory first (it likely does if resolved, but let's be safe or assume discovery happened)
        # For robustness, we try to find the site by site_id in our DB.
        from app.models.inventory import SharePointSite, SharePointList
        from sqlalchemy import select
        from datetime import datetime

        site_rec = db.execute(select(SharePointSite).where(SharePointSite.site_id == site_id)).scalar_one_or_none()
        
        # If site doesn't exist in local DB, we create it (lazy discovery)
        if not site_rec:
            # We have site_info from Graph
            site_rec = SharePointSite(
                connection_id=conn.id,
                tenant_id=conn.tenant_id,
                hostname=site_info.get("siteCollection", {}).get("hostname") or payload.hostname,
                site_path=payload.site_path, # Approximate
                site_id=site_id,
                web_url=site_info.get("webUrl", ""),
                status="ACTIVE"
            )
            db.add(site_rec)
            db.flush() # get ID

        # Upsert List
        list_guid = result["list"]["id"]
        list_rec = db.execute(select(SharePointList).where(SharePointList.list_id == list_guid)).scalar_one_or_none()
        
        if list_rec:
            list_rec.display_name = result["list"]["displayName"]
            list_rec.description = payload.description
            list_rec.is_provisioned = True
            list_rec.last_provisioned_at = datetime.utcnow()
            list_rec.source_table_id = payload.tableId if hasattr(payload, 'tableId') else None # Wait, request doesn't have tableId in schema yet?
        else:
            list_rec = SharePointList(
                site_id=site_rec.id,
                list_id=list_guid,
                display_name=result["list"]["displayName"],
                description=payload.description,
                template="genericList",
                is_provisioned=True,
                last_provisioned_at=datetime.utcnow(),
                # source_table_id will be set if passed
            )
            db.add(list_rec)
        
        # We need tableId in ProvisionRequest to link it
        if hasattr(payload, 'table_id') and payload.table_id:
             list_rec.source_table_id = payload.table_id

        db.commit()
        record_audit_event(
            db,
            request,
            principal,
            action="provisioning.list.create",
            resource_type="sharepoint_list",
            resource_id=list_guid,
            details={"list_name": payload.list_name, "hostname": payload.hostname, "site_path": payload.site_path},
        )
        
        return success_response(request, result)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Provisioning failed: {str(e)}")


@router.get("/connections", response_model=ApiResponse[list[dict]])
def list_connections(
    request: Request,
    _: None = Depends(require_roles(*OPERATOR_ROLES)),
    db: Session = Depends(get_db),
):
    """List all SharePoint connections."""
    connections = db.query(SharePointConnection).all()
    return success_response(request, [
        {
            "id": str(conn.id),
            "tenant_id": conn.tenant_id,
            "client_id": conn.client_id,
            "status": conn.status
        }
        for conn in connections
    ])


@router.get("/debug-token/{connection_id}", response_model=ApiResponse[dict])
def debug_token(
    connection_id: UUID,
    request: Request,
    principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    """Debug endpoint to check token permissions."""
    if not settings.ENABLE_TOKEN_DEBUG_ENDPOINT:
        raise HTTPException(status_code=404, detail="Not found")

    conn = db.get(SharePointConnection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="SharePoint connection not found")

    secret = resolve_sharepoint_client_secret(conn)

    try:
        graph = GraphClient(
            tenant_id=conn.tenant_id,
            client_id=conn.client_id,
            client_secret=secret,
            authority_host=conn.authority_host
        )

        # Get token
        token = graph._get_access_token()

        # Decode token (without verification for debugging)
        decoded = jwt.decode(token, options={"verify_signature": False})

        payload = {
            "tenant_id": conn.tenant_id,
            "client_id": conn.client_id,
            "token_roles": decoded.get("roles", []),
            "token_scopes": decoded.get("scp", ""),
            "app_id": decoded.get("appid"),
            "audience": decoded.get("aud"),
            "expires": decoded.get("exp"),
            "token_claim_keys": sorted(decoded.keys())
        }
        record_audit_event(
            db,
            request,
            principal,
            action="provisioning.token.debug",
            resource_type="sharepoint_connection",
            resource_id=str(connection_id),
        )
        return success_response(request, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to debug token: {str(e)}")
