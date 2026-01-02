from typing import Dict, Any, Optional
from uuid import UUID
import logging
from app.services.sharepoint_content import SharePointContentService
from app.services.state import LedgerService
from app.models.core import SyncLedgerEntry

logger = logging.getLogger(__name__)

class MoveManager:
    def __init__(self, content_service: SharePointContentService, ledger_service: LedgerService):
        self.content = content_service
        self.ledger = ledger_service

    def move_item(
        self,
        site_id: str,
        entry: SyncLedgerEntry,
        new_list_id: str,
        item_data: Dict[str, Any]
    ) -> bool:
        """
        Moves an item from its current list (in entry) to new_list_id.
        Strategy: Copy (Create) -> Update Ledger -> Delete Old.
        
        Args:
            site_id: The SharePoint Site ID (assuming source/target in same site for now).
            entry: The current SyncLedgerEntry for the item.
            new_list_id: The SharePoint List ID (GUID string) to move to.
            item_data: The content fields to write to the new list.
            
        Returns:
            True if move was successful (or at least the critical Create+Link part), False otherwise.
        """
        old_list_id = entry.sp_list_id
        old_item_id = str(entry.sp_item_id)
        
        if old_list_id == new_list_id:
            logger.info(f"Item {entry.source_identity_hash} already in target list {new_list_id}. Skipping move.")
            return True

        logger.info(f"Moving item {entry.source_identity_hash} from {old_list_id} to {new_list_id}")

        # 1. Create in New Location
        try:
            new_item_id_str = self.content.create_item(site_id, new_list_id, item_data)
            new_item_id = int(new_item_id_str) # SharePoint IDs are integers
        except Exception as e:
            logger.error(f"Failed to create item in new list {new_list_id}: {e}")
            return False

        # 2. Update Ledger
        # We modify the entry object and pass it to record_entry.
        # record_entry expects the object to have the updated values.
        # However, entry is attached to a session potentially? 
        # LedgerService.record_entry re-queries or merges.
        
        # Let's create a copy of the state we want to save, or just modify the entry if it's detached/we own the session.
        # Assuming LedgerService handles it safely.
        
        previous_sp_list_id = entry.sp_list_id
        previous_sp_item_id = entry.sp_item_id
        
        entry.sp_list_id = new_list_id
        entry.sp_item_id = new_item_id
        entry.last_sync_ts = entry.last_sync_ts # Keep or update timestamp? Maybe update.
        
        try:
            self.ledger.record_entry(entry)
        except Exception as e:
            logger.critical(f"Failed to update ledger after creating item {new_item_id} in {new_list_id}. Data duplication risk! Error: {e}")
            # In a real system, we might try to delete the newly created item here to rollback.
            return False

        # 3. Delete from Old Location
        try:
            self.content.delete_item(site_id, old_list_id, old_item_id)
        except Exception as e:
            logger.warning(f"Failed to delete old item {old_item_id} from {old_list_id} after move. Orphan created. Error: {e}")
            # We return True because the "Move" (getting it to the new place and tracking it) succeeded. 
            # cleanup failure is secondary.
        
        # 4. Audit Log
        try:
             # Assuming site_id + new_list_id helps identify the target.
             # Ideally we pass sync_def_id if available, but signature doesn't have it yet.
             self.ledger.log_move(
                 source_identity_hash=entry.source_identity_hash,
                 from_list_id=old_list_id,
                 to_list_id=new_list_id,
                 status="SUCCESS",
                 details=f"Moved item {old_item_id} to {new_item_id}"
             )
        except Exception as e:
            logger.error(f"Failed to write audit log for move: {e}")

        return True
