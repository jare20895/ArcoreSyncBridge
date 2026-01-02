import sys
import os
import time
import cProfile
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock

# Running inside /app which is package root


from app.db.session import SessionLocal
from app.models.core import SyncDefinition, DatabaseInstance, SyncSource, SyncTarget, SharePointConnection, FieldMapping
from app.services.pusher import Pusher
from app.services.graph import GraphClient

def setup_benchmark_data(db):
    # Create Objects
    def_id = uuid4()
    
    # Instance (Localhost)
    # Assuming 'arcoresyncbridge-db-1' is not reachable from host script if running outside docker.
    # But this script usually runs where? If I run `python scripts/run_benchmark.py` on host,
    # it needs to connect to DB. 
    # 'localhost:5465' is the mapped port.
    # But `Pusher` uses `instance.host`. 
    # Hack: Use a special instance for benchmark that points to localhost:5465
    
    instance = DatabaseInstance(
        instance_label=f"benchmark_db_{uuid4()}",
        host="db",
        port=5432,
        db_name="arcore_syncbridge",
        username="arcore",
        password="arcore_password"
    )
    db.add(instance)
    db.flush()
    
    sync_def = SyncDefinition(
        id=def_id,
        name="Benchmark Sync",
        source_table_id=uuid4(),
        source_table_name="benchmark_items",
        source_schema="public",
        sync_mode="ONE_WAY_PUSH",
        conflict_policy="SOURCE_WINS",
        key_strategy="PRIMARY_KEY",
        cursor_strategy="TIMESTAMP"
    )
    db.add(sync_def)
    
    source = SyncSource(
        sync_def_id=def_id,
        database_instance_id=instance.id,
        role="PRIMARY"
    )
    db.add(source)
    
    # Mock Connection
    conn = SharePointConnection(
        tenant_id="mock-tenant",
        client_id="mock-client",
        status="ACTIVE",
        scopes=["https://graph.microsoft.com/.default"]
    )
    db.add(conn)
    db.flush()
    
    target = SyncTarget(
        sync_def_id=def_id,
        target_list_id=uuid4(),
        sharepoint_connection_id=conn.id,
        site_id="mock-site",
        status="ACTIVE"
    )
    db.add(target)
    
    # Mappings
    # name -> Title, sku -> SKU
    db.add(FieldMapping(sync_def_id=def_id, source_column_name="name", target_column_name="Title", source_column_id=uuid4(), target_column_id=uuid4(), target_type="Text"))
    db.add(FieldMapping(sync_def_id=def_id, source_column_name="sku", target_column_name="SKU", source_column_id=uuid4(), target_column_id=uuid4(), target_type="Text", is_key=True))
    
    db.commit()
    return def_id

def run_benchmark():
    db = SessionLocal()
    try:
        print("Setting up benchmark data...")
        def_id = setup_benchmark_data(db)
        
        print("Initializing Pusher...")
        pusher = Pusher(db)
        
        # Mock the Content Service creation to return a mock
        # We patch the _get_content_service method or pass a mock?
        # Pusher._get_content_service returns (service, site_id).
        # Service wraps GraphClient.
        
        mock_graph = MagicMock()
        # Mock request to return success for create/update
        mock_graph.request.return_value = {"id": "100"} 
        
        # We need to monkeypatch Pusher's _get_content_service or GraphClient
        # Easier: Mock GraphClient class in `app.services.pusher` module?
        # Or just mock `_get_content_service`.
        
        original_get_content = pusher._get_content_service
        
        def mock_get_content(target):
            from app.services.sharepoint_content import SharePointContentService
            svc = SharePointContentService(mock_graph)
            # Mock create_item to be fast
            svc.create_item = MagicMock(return_value="100")
            svc.update_item = MagicMock()
            return svc, "mock-site"
            
        pusher._get_content_service = mock_get_content
        
        print("Starting Sync of 10k items...")
        start_time = time.time()
        
        total_processed = 0
        while True:
            result = pusher.run_push(def_id)
            count = result["processed_count"]
            total_processed += count
            print(f"Batch processed: {count}")
            if count == 0:
                break
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Completed in {duration:.2f} seconds")
        print(f"Total Processed: {total_processed}")
        if duration > 0:
            print(f"Throughput: {total_processed / duration:.2f} items/sec")
        
    finally:
        # Cleanup?
        # db.rollback() # Or keep for analysis
        db.close()

if __name__ == "__main__":
    run_benchmark()
