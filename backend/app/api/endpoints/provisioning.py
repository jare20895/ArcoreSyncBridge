from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.api.endpoints.database_instances import get_db
from app.models.core import SharePointConnection
from app.schemas.provisioning import ProvisionRequest, ProvisionResponse
from app.services.graph import GraphClient
from app.services.provisioner import SharePointProvisioner
import jwt
import os

router = APIRouter()

@router.post("/list", response_model=ProvisionResponse)
def provision_sharepoint_list(
    request: ProvisionRequest,
    db: Session = Depends(get_db)
):
    # 1. Fetch Connection Details
    conn = db.get(SharePointConnection, request.connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="SharePoint connection not found")

    if conn.status != "ACTIVE":
         raise HTTPException(status_code=400, detail="SharePoint connection is not active")

    # 2. Initialize Graph Client
    # NOTE: In a real app, secrets should be decrypted.
    import os
    secret = conn.client_secret or os.environ.get("AZURE_CLIENT_SECRET", "")
    if not secret and conn.client_id == os.environ.get("AZURE_CLIENT_ID"):
        secret = os.environ.get("AZURE_CLIENT_SECRET", "")
    if not secret:
        raise HTTPException(status_code=400, detail="SharePoint connection secret is missing")

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
        site_info = provisioner.get_site(request.hostname, request.site_path)
        site_id = site_info["id"]

        result = provisioner.provision_table_to_list(
            site_id=site_id,
            pg_columns=request.columns,
            list_display_name=request.list_name,
            description=request.description,
            skip_columns=request.skip_columns,
            column_configurations=request.column_configurations
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
                hostname=site_info.get("siteCollection", {}).get("hostname") or request.hostname,
                site_path=request.site_path, # Approximate
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
            list_rec.description = request.description
            list_rec.is_provisioned = True
            list_rec.last_provisioned_at = datetime.utcnow()
            list_rec.source_table_id = request.tableId if hasattr(request, 'tableId') else None # Wait, request doesn't have tableId in schema yet?
        else:
            list_rec = SharePointList(
                site_id=site_rec.id,
                list_id=list_guid,
                display_name=result["list"]["displayName"],
                description=request.description,
                template="genericList",
                is_provisioned=True,
                last_provisioned_at=datetime.utcnow(),
                # source_table_id will be set if passed
            )
            db.add(list_rec)
        
        # We need tableId in ProvisionRequest to link it
        if hasattr(request, 'table_id') and request.table_id:
             list_rec.source_table_id = request.table_id

        db.commit()
        
        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Provisioning failed: {str(e)}")


@router.get("/connections")
def list_connections(db: Session = Depends(get_db)):
    """List all SharePoint connections."""
    connections = db.query(SharePointConnection).all()
    return [
        {
            "id": str(conn.id),
            "tenant_id": conn.tenant_id,
            "client_id": conn.client_id,
            "status": conn.status
        }
        for conn in connections
    ]


@router.get("/debug-token/{connection_id}")
def debug_token(connection_id: UUID, db: Session = Depends(get_db)):
    """Debug endpoint to check token permissions."""
    conn = db.get(SharePointConnection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="SharePoint connection not found")

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

        # Get token
        token = graph._get_access_token()

        # Decode token (without verification for debugging)
        decoded = jwt.decode(token, options={"verify_signature": False})

        return {
            "tenant_id": conn.tenant_id,
            "client_id": conn.client_id,
            "token_roles": decoded.get("roles", []),
            "token_scopes": decoded.get("scp", ""),
            "app_id": decoded.get("appid"),
            "audience": decoded.get("aud"),
            "expires": decoded.get("exp"),
            "full_decoded": decoded
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to debug token: {str(e)}")
