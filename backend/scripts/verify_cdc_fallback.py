import time
import sys
import os
import requests
from uuid import uuid4
from pathlib import Path

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.models.core import DatabaseInstance, SyncDefinition, SyncSource
from app.models.inventory import Application, Database, DatabaseTable

DB_HOST = os.environ.get("POSTGRES_HOST", "db")
DB_PORT = int(os.environ.get("POSTGRES_PORT", "5465"))
DB_NAME = os.environ.get("POSTGRES_DB", "arcore_syncbridge")
DB_USER = os.environ.get("POSTGRES_USER", "change_me")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "change_me")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8401/api/v1")

def verify_fallback():
    print("Setting up test data for CDC fallback verification...")
    db = SessionLocal()
    
    # 1. Setup Inventory (Application -> Database -> Table)
    app = Application(name="Test App", status="ACTIVE")
    db.add(app)
    db.commit()
    
    database = Database(
        application_id=app.id,
        name="Test DB",
        environment="DEV",
        database_name=DB_NAME,
        status="ACTIVE"
    )
    db.add(database)
    db.commit()
    
    table_id = uuid4()
    table = DatabaseTable(
        id=table_id,
        database_id=database.id,
        schema_name="public",
        table_name="fallback_test_table",
        table_type="BASE"
    )
    db.add(table)
    db.commit()
    
    # 2. Setup Instance linked to Database
    instance_id = uuid4()
    instance = DatabaseInstance(
        id=instance_id,
        database_id=database.id,
        instance_label=f"fallback_test_{uuid4()}",
        host=DB_HOST,
        port=DB_PORT,
        db_name=DB_NAME,
        username=DB_USER,
        password=DB_PASSWORD,
        status="ACTIVE",
        priority=1,
        replication_slot_name="test_slot_fallback" # Must exist or check will fail
    )
    db.add(instance)
    db.commit()
    
    # 3. Setup SyncDefinition using source_table_id (NO SyncSource)
    sync_def_id = uuid4()
    sync_def = SyncDefinition(
        id=sync_def_id,
        name="CDC Fallback Test Sync",
        source_table_id=table_id,
        source_table_name="fallback_test_table",
        source_schema="public",
        sync_mode="ONE_WAY_PUSH",
        key_strategy="PRIMARY_KEY",
        conflict_policy="SOURCE_WINS",
        cursor_strategy="UPDATED_AT",
        cdc_enabled=False, # Initially false
        target_strategy="SINGLE"
    )
    db.add(sync_def)
    db.commit()
    
    print(f"Created Sync Def: {sync_def_id} (No SyncSource)")
    
    # Ensure no SyncSource exists
    existing_source = db.query(SyncSource).filter_by(sync_def_id=sync_def_id).first()
    if existing_source:
        print("Error: SyncSource unexpectedly exists!")
        return

    # 4. Call enable-cdc endpoint
    url = f"{API_BASE_URL}/cdc/{sync_def_id}/enable-cdc"
    print(f"Calling endpoint: {url}")
    
    # Note: We depend on 'cdc_manager' dependency in the endpoint. 
    # If the app is not fully running with cdc_manager initialized, it might fail at the 'start_cdc_for_instance' step.
    # However, we primarily want to check if it passes the "Sync definition has no primary source" check.
    # If it fails with "cdc_manager" related error or "connection" error, it means it PASSED the source check.
    
    try:
        response = requests.post(url)
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: Fallback logic worked! CDC enabled.")
        elif response.status_code == 500:
            # If 500, check if it's because of cdc_manager (which is expected if we run outside full app context)
            if "CDC Manager" in response.text or "start_cdc_for_instance" in response.text:
                 print("SUCCESS (Partial): Fallback logic worked (passed source check), failed at CDC start (expected in test script).")
            else:
                 print("FAILURE: 500 Error unrelated to CDC start.")
        elif response.status_code == 400:
            if "Sync definition has no primary source" in response.text:
                print("FAILURE: Fallback logic FAILED. Still getting 'no primary source' error.")
            else:
                 print(f"FAILURE: 400 Error: {response.text}")
        else:
            print(f"FAILURE: Unexpected status code {response.status_code}")
            
    except Exception as e:
        print(f"Exception during request: {e}")

    # Cleanup
    # db.delete(sync_def)
    # db.delete(instance)
    # db.delete(table)
    # db.delete(database)
    # db.delete(app)
    # db.commit()
    db.close()

if __name__ == "__main__":
    verify_fallback()
