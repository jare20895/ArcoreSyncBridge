import unittest
from unittest.mock import MagicMock, patch, ANY
from uuid import uuid4
from datetime import datetime
from app.services.synchronizer import Synchronizer
from app.services.pusher import Pusher
from app.models.core import SyncDefinition, SyncLedgerEntry, SyncSource, SyncTarget, DatabaseInstance, SharePointConnection, FieldMapping
import hashlib
import json

class TestTwoWayIntegration(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        
        # Setup Common Objects
        self.sync_def_id = uuid4()
        self.target_list_id = uuid4()
        self.instance_id = uuid4()
        
        self.sync_def = SyncDefinition(
            id=self.sync_def_id,
            name="Test Sync",
            source_schema="public",
            source_table_name="products",
            conflict_policy="DESTINATION_WINS", # Test Ingress Overwrite
            field_mappings=[
                FieldMapping(source_column_name="name", target_column_name="Title", is_key=False),
                FieldMapping(source_column_name="sku", target_column_name="SKU", is_key=True) # PK
            ]
        )
        
        self.target = SyncTarget(
            sync_def_id=self.sync_def_id,
            target_list_id=self.target_list_id,
            status="ACTIVE"
        )
        
        self.instance = DatabaseInstance(
            id=self.instance_id,
            host="localhost",
            port=5432
        )
        
        self.source = SyncSource(
            sync_def_id=self.sync_def_id,
            database_instance_id=self.instance_id,
            role="PRIMARY",
            is_enabled=True,
            database_instance=self.instance
        )
        
        self.conn = SharePointConnection(
            tenant_id="t1",
            client_id="c1",
            status="ACTIVE"
        )
        
        # Mock DB Queries
        self.mock_db.get.side_effect = lambda model, id: self.sync_def if model == SyncDefinition else None
        
        # Mock Query Chain for Connection/Target/Source
        # This is tricky with SQLAlchemy mocks, so we mock the result scalars().first()
        # We'll use side_effect on execute()
        
    @patch('app.services.synchronizer.GraphClient')
    @patch('app.services.synchronizer.SharePointContentService')
    @patch('app.services.synchronizer.DatabaseClient')
    def test_ingress_destination_wins(self, MockDBClient, MockContentService, MockGraph):
        # Scenario: SharePoint has a new item. We Ingest it.
        
        # Setup Mocks
        mock_content = MockContentService.return_value
        mock_db_client = MockDBClient.return_value
        
        # Mock Data
        sp_changes = [
            {"id": "100", "reason": "changed", "fields": {"Title": "New Product", "SKU": "P-100"}}
        ]
        mock_content.get_list_changes.return_value = (sp_changes, "new_delta_token")
        
        # Mock DB Lookups
        def db_execute_side_effect(stmt):
            # Very rough mock of SQLAlchemy select execution
            mock_result = MagicMock()
            s_str = str(stmt)
            if "sharepoint_connections" in s_str:
                mock_result.scalars.return_value.first.return_value = self.conn
            elif "sync_targets" in s_str:
                mock_result.scalars.return_value.first.return_value = self.target
            elif "sync_sources" in s_str:
                mock_result.scalars.return_value.first.return_value = self.source
            elif "sync_cursors" in s_str:
                mock_result.scalars.return_value.first.return_value = None # No token yet
            elif "sync_ledger" in s_str:
                mock_result.scalars.return_value.first.return_value = None # New Item
            return mock_result
            
        self.mock_db.execute.side_effect = db_execute_side_effect
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.conn # Handle query().filter().first() pattern

        # Init Synchronizer
        syncer = Synchronizer(self.mock_db)
        
        # Mock DB Client Insert Return
        mock_db_client.insert_row.return_value = {"sku": "P-100", "name": "New Product"}
        
        # Run
        result = syncer.run_ingress(self.sync_def_id)
        
        # Verify
        self.assertEqual(result["processed_count"], 1)
        
        # Check DB Insert
        mock_db_client.insert_row.assert_called_with(
            "public", "products", {"name": "New Product", "sku": "P-100"}
        )
        
        # Check Ledger Creation
        self.mock_db.add.assert_called()
        added_obj = self.mock_db.add.call_args[0][0]
        self.IsInstance(added_obj, SyncLedgerEntry)
        self.assertEqual(added_obj.provenance, "PULL")
        self.assertEqual(added_obj.source_identity, "P-100")

    @patch('app.services.pusher.GraphClient')
    @patch('app.services.pusher.SharePointContentService')
    @patch('app.services.pusher.DatabaseClient')
    def test_push_loop_prevention(self, MockDBClient, MockContentService, MockGraph):
        # Scenario: DB has an update. But it matches the Ledger (Echo). Should Skip.
        
        mock_content = MockContentService.return_value
        mock_db_client = MockDBClient.return_value
        
        # Mock Data
        # DB Row
        row_data = {"sku": "P-100", "name": "New Product", "updated_at": datetime.utcnow()}
        mock_db_client.fetch_changed_rows.return_value = [row_data]
        
        # Ledger Entry (Matches Content)
        content_hash = hashlib.sha256(json.dumps({"name": "New Product", "sku": "P-100"}, sort_keys=True, default=str).encode()).hexdigest()
        id_hash = hashlib.sha256("P-100".encode()).hexdigest()
        
        ledger_entry = SyncLedgerEntry(
            source_identity_hash=id_hash,
            content_hash=content_hash,
            provenance="PULL", # Last write was from SP
            sp_item_id=100
        )
        
        # Mock DB Lookups
        self.mock_db.get.side_effect = lambda model, id: self.sync_def if model == SyncDefinition else (ledger_entry if model == SyncLedgerEntry else None)
        
        def db_execute_side_effect(stmt):
            mock_result = MagicMock()
            s_str = str(stmt)
            if "sharepoint_connections" in s_str:
                mock_result.scalars.return_value.first.return_value = self.conn
            elif "sync_targets" in s_str:
                mock_result.scalars.return_value.first.return_value = self.target
            elif "sync_sources" in s_str:
                mock_result.scalars.return_value.first.return_value = self.source
            elif "sync_cursors" in s_str:
                mock_result.scalars.return_value.first.return_value = None # No watermark
            return mock_result
            
        self.mock_db.execute.side_effect = db_execute_side_effect
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.conn

        # Init Pusher
        pusher = Pusher(self.mock_db)
        
        # Run
        result = pusher.run_push(self.sync_def_id)
        
        # Verify
        # Should detect loop and SKIP update
        mock_content.update_item.assert_not_called()
        self.assertEqual(result["processed_count"], 1) # Processed but skipped

    def IsInstance(self, obj, cls):
        self.assertTrue(isinstance(obj, cls))

if __name__ == '__main__':
    unittest.main()
