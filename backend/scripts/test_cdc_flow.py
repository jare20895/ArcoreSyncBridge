import time
import sys
import os
import threading
import requests # Added for API calls
from uuid import uuid4
from pathlib import Path

# Add backend to path (supports repo root or backend dir execution)
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.models.core import DatabaseInstance, SyncDefinition, SyncTarget, SharePointConnection, FieldMapping
from app.services.cdc import CDCService
from app.services.cdc_consumer import CDCConsumer
from sqlalchemy import text # Added for raw SQL execution
from unittest.mock import MagicMock

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000/api/v1") # Backend API (internal access)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
DB_HOST = os.environ.get("POSTGRES_HOST", "db")
DB_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
DB_NAME = os.environ.get("POSTGRES_DB", "arcore_syncbridge")
DB_USER = os.environ.get("POSTGRES_USER", "arcore")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "arcore_password")

def ensure_benchmark_table(db):
    exists = db.execute(text("SELECT to_regclass('public.benchmark_items')")).scalar()
    if exists:
        return
    db.execute(text(
        "CREATE TABLE benchmark_items ("
        "id SERIAL PRIMARY KEY, "
        "name TEXT, "
        "sku TEXT, "
        "description TEXT, "
        "price DECIMAL, "
        "updated_at TIMESTAMP DEFAULT NOW()"
        ")"
    ))
    db.commit()

def ensure_publication(db):
    exists = db.execute(text("SELECT 1 FROM pg_publication WHERE pubname = 'arcore_cdc_pub'")).first()
    if exists:
        return
    db.execute(text("CREATE PUBLICATION arcore_cdc_pub FOR ALL TABLES"))
    db.commit()

def ensure_sharepoint_connection(db):
    conn = db.query(SharePointConnection).first()
    if conn:
        return conn
    conn = SharePointConnection(
        tenant_id="mock-tenant",
        client_id="mock-client",
        client_secret="mock-secret",
        scopes=["https://graph.microsoft.com/.default"],
        status="ACTIVE",
    )
    db.add(conn)
    db.commit()
    return conn

def test_cdc_flow():
    print("Setting up test data...")
    db = SessionLocal()
    ensure_benchmark_table(db)
    ensure_publication(db)
    
    # 1. Setup Instance, SyncDef, Connection
    instance_id = uuid4()
    sync_def_id = uuid4()
    
    # Create Instance (Mocking connection for CDC Service?) 
    # Real CDC Service needs real Postgres. 
    # We will use the existing 'benchmark_db' instance if available or create one that points to 'db'.
    # Actually, CDCService connects to 'db'.
    
    # Let's verify we can connect.
    instance = DatabaseInstance(
        id=instance_id,
        instance_label=f"cdc_test_{uuid4()}",
        host=DB_HOST,
        port=DB_PORT,
        db_name=DB_NAME,
        username=DB_USER,
        password=DB_PASSWORD,
        replication_slot_name=f"test_slot_{str(uuid4()).replace('-','_')}"
    )
    db.add(instance)
    
    sync_def = SyncDefinition(
        id=sync_def_id,
        name="CDC Test Sync",
        source_table_id=uuid4(), # Ensure non-null
        source_table_name="benchmark_items", # Use existing table
        source_schema="public",
        sync_mode="TWO_WAY",
        key_strategy="PRIMARY_KEY", # Ensure non-null
        conflict_policy="SOURCE_WINS", # Ensure non-null
        cursor_strategy="UPDATED_AT", # Ensure non-null
        cdc_enabled=True,
        target_list_id=uuid4()
    )
    db.add(sync_def)
    
    # Link
    from app.models.core import SyncSource
    db.add(SyncSource(sync_def_id=sync_def_id, database_instance_id=instance_id))
    
    # Target
    conn = ensure_sharepoint_connection(db)
    db.add(SyncTarget(
        sync_def_id=sync_def_id,
        target_list_id=sync_def.target_list_id,
        sharepoint_connection_id=conn.id,
        site_id="mock-site-id",
        is_default=True
    ))
    
    # Mappings
    db.add(FieldMapping(sync_def_id=sync_def_id, source_column_name="name", target_column_name="Title", source_column_id=uuid4(), target_column_id=uuid4(), target_type="Text"))
    
    db.commit()
    
    print(f"Created Sync Def: {sync_def_id}")
    
    # 2. Create Replication Slot via API
    print(f"Creating replication slot {instance.replication_slot_name} via API...")
    try:
        slot_create_resp = requests.post(f"{API_BASE_URL}/replication/slots", json={
            "instance_id": str(instance.id),
            "slot_name": instance.replication_slot_name,
            "plugin": "pgoutput"
        })
        slot_create_resp.raise_for_status()
        print("Slot created.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 500 and "already exists" in e.response.json().get("detail", ""):
            print(f"Slot {instance.replication_slot_name} already exists. Proceeding.")
        else:
            raise

    # 3. Start CDC Service in thread
    # We need to mock the blocking loop or run it for a bit.
    # CDCService.run() is infinite loop.
    # We'll run it in a thread and kill it?
    
    stop_event = threading.Event()
    
    def run_cdc():
        try:
            service = CDCService(SessionLocal(), instance.id, stop_event=stop_event)
            service.run()
        except Exception as e:
            print(f"CDC Thread Error: {e}")

    cdc_thread = threading.Thread(target=run_cdc, daemon=True)
    cdc_thread.start()
    
    print("CDC Service started. Waiting for slot init...")
    time.sleep(2) # Give CDC service time to connect
    
    # 4. Trigger Change in DB
    print("Inserting row into DB...")
    db.execute(text("INSERT INTO benchmark_items (name, sku) VALUES (:name, :sku)"), {"name": 'CDC_TEST_ITEM', "sku": 'CDC_SKU'})
    db.commit()
    time.sleep(1) # Give CDC service time to process the new event
    
    # 5. Start Consumer (Mocked Graph)
    print("Starting Consumer...")
    
    def mock_content_service_factory(_conn, _site_id, _list_id):
        service = MagicMock()
        service.create_item.return_value = "1"
        return service

    consumer = CDCConsumer(SessionLocal(), content_service_factory=mock_content_service_factory)
    
    print("Checking Redis for events...")
    import redis
    r = redis.Redis.from_url(REDIS_URL)
    
    events = []
    found_insert_event = False
    for _ in range(20):
        # Read from stream. Look for the INSERT event.
        resp = r.xreadgroup(consumer.group_name, consumer.consumer_name, {consumer.stream_key: ">"}, count=10, block=1000)
        if resp:
            stream, messages = resp[0]
            for message_id, data in messages:
                payload = data.get(b'payload')
                if payload:
                    decoded_event = consumer.decoder.decode(payload)
                    if decoded_event and decoded_event.get("type") == "INSERT" and decoded_event.get("data", {}).get("name") == "CDC_TEST_ITEM":
                        print(f"Found INSERT message {message_id} in Redis!")
                        events.append((message_id, data))
                        consumer.redis.xack(consumer.stream_key, consumer.group_name, message_id) # Acknowledge
                        found_insert_event = True
                        break
                    else:
                        # Acknowledge other messages like BEGIN/COMMIT so they don't block
                        consumer.redis.xack(consumer.stream_key, consumer.group_name, message_id)
            if found_insert_event:
                break
        time.sleep(0.5)
        
    if not found_insert_event:
        print("FAIL: No INSERT event found in Redis after trigger.")
    else:
        print("SUCCESS: CDC captured INSERT event.")
        # 6. Process the event with consumer's logic (which includes mocking Graph)
        message_id, data = events[0]
        consumer.process_message(message_id, data) # This will mock Graph calls

        # 7. Verify event payload (basic check)
        payload = data[b'payload']
        decoded_event = consumer.decoder.decode(payload)
        if decoded_event and decoded_event.get("type") == "INSERT" and decoded_event.get("data", {}).get("name") == "CDC_TEST_ITEM":
            print("SUCCESS: Event payload decoded and verified (final check).")
        else:
            print(f"FAIL: Event payload verification failed (final check). Decoded: {decoded_event}")

    # Stop CDC Thread gracefully
    print("Signaling CDC Service to stop...")
    stop_event.set()
    cdc_thread.join(timeout=5) # Wait for thread to exit
    if cdc_thread.is_alive():
        print("Warning: CDC thread did not stop gracefully.")

    # Cleanup: Drop slot
    print("Dropping replication slot...")
    db.close()

if __name__ == "__main__":
    test_cdc_flow()
