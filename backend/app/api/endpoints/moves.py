from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.api.endpoints.database_instances import get_db
from app.schemas.move import MoveItemRequest, MoveItemResponse
from app.models.core import SyncDefinition, SyncLedgerEntry, SharePointConnection, SyncTarget
from app.services.mover import MoveManager
from app.services.sharepoint_content import SharePointContentService
from app.services.state import LedgerService
from app.services.graph import GraphClient
import os

router = APIRouter()

@router.post("/item", response_model=MoveItemResponse)
def move_sharepoint_item(
    request: MoveItemRequest,
    db: Session = Depends(get_db)
):
    # 1. Fetch Sync Definition
    sync_def = db.get(SyncDefinition, request.sync_def_id)
    if not sync_def:
        raise HTTPException(status_code=404, detail="Sync definition not found")
        
    # 2. Find the Ledger Entry using composite key
    entry = db.get(SyncLedgerEntry, (request.sync_def_id, request.source_identity_hash))
    if not entry:
        raise HTTPException(status_code=404, detail="Item not found in ledger")

    # 3. Resolve Target Context (Destination)
    target = db.execute(select(SyncTarget).where(
        SyncTarget.sync_def_id == request.sync_def_id,
        SyncTarget.target_list_id == request.target_list_id
    )).scalars().first()
    
    # If target not found by ID (maybe dynamic sharding to a new list not yet in targets?), fail for now.
    # Phase 2 implies dynamic creation, but usually we define targets.
    # If we assume target_list_id is valid...
    
    conn = None
    site_id = None
    
    if target:
        if target.sharepoint_connection_id:
            conn = db.get(SharePointConnection, target.sharepoint_connection_id)
        site_id = target.site_id

    # Fallback Context
    if not conn:
        conn = db.query(SharePointConnection).filter(SharePointConnection.status == "ACTIVE").first()
    
    if not site_id:
        site_id = os.environ.get("SHAREPOINT_SITE_ID", "")

    if not conn:
         raise HTTPException(status_code=400, detail="No active SharePoint connection available")
    if not site_id:
         raise HTTPException(status_code=400, detail="Site ID could not be resolved")

    # 4. Initialize Services
    try:
        client_secret = os.environ.get("AZURE_CLIENT_SECRET", "")
        
        graph_client = GraphClient(
            tenant_id=conn.tenant_id,
            client_id=conn.client_id,
            client_secret=client_secret,
            authority_host=conn.authority_host
        )
        content_service = SharePointContentService(graph_client)
        ledger_service = LedgerService(db)
        move_manager = MoveManager(content_service, ledger_service)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service initialization failed: {str(e)}")

    # 5. Execute Move
    success = move_manager.move_item(
        site_id=site_id,
        entry=entry,
        new_list_id=str(request.target_list_id),
        item_data=request.item_data
    )

    if success:
        return MoveItemResponse(
            success=True, 
            message="Item moved successfully",
            new_item_id=entry.sp_item_id # Updated by manager
        )
    else:
        raise HTTPException(status_code=500, detail="Move operation failed")
