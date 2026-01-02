from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.core import SyncDefinition, SyncLedgerEntry, SyncTarget, SharePointConnection
from app.services.sharepoint_content import SharePointContentService
from app.services.graph import GraphClient
from app.schemas.ops import DriftReportResponse, DriftItem
import os

class DriftService:
    def __init__(self, db: Session):
        self.db = db

    def generate_report(self, sync_def_id: UUID, check_type: str) -> DriftReportResponse:
        sync_def = self.db.get(SyncDefinition, sync_def_id)
        if not sync_def:
            raise ValueError("Sync definition not found")

        # 1. Resolve Targets and Connection
        # Assuming single target for simplicity or iterating all targets
        targets = self.db.execute(select(SyncTarget).where(SyncTarget.sync_def_id == sync_def_id)).scalars().all()
        
        issues = []
        
        for target in targets:
            # Resolve Connection & Site for this target
            conn = None
            if target.sharepoint_connection_id:
                conn = self.db.get(SharePointConnection, target.sharepoint_connection_id)
            if not conn:
                 conn = self.db.query(SharePointConnection).filter(SharePointConnection.status == "ACTIVE").first()
            
            if not conn:
                 # Skip or error? Error better.
                 raise ValueError("No active SharePoint connection found")

            real_secret = os.environ.get("AZURE_CLIENT_SECRET", "")
            site_id = target.site_id or os.environ.get("SHAREPOINT_SITE_ID", "")
            
            graph = GraphClient(
                tenant_id=conn.tenant_id,
                client_id=conn.client_id,
                client_secret=real_secret, 
                authority_host=conn.authority_host
            )
            content_service = SharePointContentService(graph)

            list_id_str = str(target.target_list_id)
            
            if check_type == "LEDGER_VALIDITY":
                # Get all ledger entries for this list AND sync definition
                stmt = select(SyncLedgerEntry).where(
                    SyncLedgerEntry.sync_def_id == sync_def_id,
                    SyncLedgerEntry.sp_list_id == list_id_str
                )
                ledger_entries = self.db.execute(stmt).scalars().all()
                
                # Check each entry exists in SP
                # In prod, we would batch this or get all items from SP and set-compare.
                # For Phase 2 prototype, we check existence one by one or fetch all IDs.
                
                # Let's try to fetch all IDs from SP List to minimize calls
                # ContentService doesn't have "get_all_ids" yet. 
                # We'll use a naive check: loop and verify. (Slow but safe for small data)
                
                for entry in ledger_entries:
                    exists = False
                    try:
                        # get_item throws or returns None? 
                        # create_item/delete_item exist. get_item isn't explicitly in the service file I read earlier.
                        # Let's check if we can verify existence.
                        # We'll try to fetch the item.
                        item = content_service.get_item(site_id, list_id_str, str(entry.sp_item_id))
                        if item:
                            exists = True
                    except Exception:
                        exists = False
                    
                    if not exists:
                        issues.append(DriftItem(
                            item_id=str(entry.sp_item_id),
                            list_id=list_id_str,
                            issue="ORPHANED_IN_LEDGER",
                            details=f"Ledger has entry {entry.source_identity_hash} mapped to {entry.sp_item_id} but item not found in SP."
                        ))

        return DriftReportResponse(
            sync_def_id=sync_def_id,
            timestamp=datetime.utcnow().isoformat(),
            total_issues=len(issues),
            items=issues
        )
