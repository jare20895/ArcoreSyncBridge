import unittest
from unittest.mock import MagicMock
from app.services.mover import MoveManager
from app.models.core import SyncLedgerEntry
from datetime import datetime

class TestMoveManager(unittest.TestCase):
    def setUp(self):
        self.mock_content = MagicMock()
        self.mock_ledger = MagicMock()
        self.manager = MoveManager(self.mock_content, self.mock_ledger)
        
        self.site_id = "site-123"
        self.entry = SyncLedgerEntry(
            source_identity_hash="hash-1",
            sp_list_id="list-old",
            sp_item_id=100,
            last_sync_ts=datetime.utcnow()
        )
        self.item_data = {"Title": "Moved Item"}

    def test_move_success(self):
        # Setup mocks
        self.mock_content.create_item.return_value = "200"
        
        # Execute
        result = self.manager.move_item(self.site_id, self.entry, "list-new", self.item_data)
        
        # Verify
        self.assertTrue(result)
        
        # 1. Create called
        self.mock_content.create_item.assert_called_with(self.site_id, "list-new", self.item_data)
        
        # 2. Ledger updated
        self.mock_ledger.record_entry.assert_called()
        args, _ = self.mock_ledger.record_entry.call_args
        updated_entry = args[0]
        self.assertEqual(updated_entry.sp_list_id, "list-new")
        self.assertEqual(updated_entry.sp_item_id, 200)
        
        # 3. Delete called
        self.mock_content.delete_item.assert_called_with(self.site_id, "list-old", "100")

    def test_move_skip_same_list(self):
        result = self.manager.move_item(self.site_id, self.entry, "list-old", self.item_data)
        self.assertTrue(result)
        self.mock_content.create_item.assert_not_called()

    def test_create_fail(self):
        self.mock_content.create_item.side_effect = Exception("Graph Error")
        
        result = self.manager.move_item(self.site_id, self.entry, "list-new", self.item_data)
        
        self.assertFalse(result)
        self.mock_ledger.record_entry.assert_not_called()
        self.mock_content.delete_item.assert_not_called()

    def test_delete_fail_orphan(self):
        self.mock_content.create_item.return_value = "200"
        self.mock_content.delete_item.side_effect = Exception("Delete Error")
        
        result = self.manager.move_item(self.site_id, self.entry, "list-new", self.item_data)
        
        # Should still return True because the move (create + track) happened
        self.assertTrue(result)
        self.mock_ledger.record_entry.assert_called()
        self.mock_content.delete_item.assert_called()