import sys
import os
import psycopg2
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from uuid import UUID

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import settings
from app.models.core import DatabaseInstance

def get_db_session():
    # Use the SQLAlchemy URL (likely includes +psycopg for v3, but we might need to adjust if using v2 engine)
    # The project config uses +psycopg, so let's stick to it for the engine.
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def fix_slots():
    print("Starting replication slot inspection and fix...")
    db = get_db_session()
    
    # 1. Get all configured instances with CDC enabled (replication_slot_name is set)
    instances = db.execute(
        select(DatabaseInstance).where(DatabaseInstance.replication_slot_name.isnot(None))
    ).scalars().all()
    
    print(f"Found {len(instances)} instances with configured replication slots.")
    
    # 2. For each instance, check if the slot exists in the DB
    for instance in instances:
        print(f"Checking instance {instance.instance_label} ({instance.host}:{instance.port})...")
        
        # Connection params (assuming superuser/replication user is available via env or same as app)
        # Note: In docker-compose, host 'db' is reachable as 'localhost' mapped port if running outside
        # But here we are likely running inside or with access. 
        # Using the instance.host might fail if running from host machine and instance.host is 'db'
        # We'll try to connect using the App's DB connection string if it points to the same DB
        
        # Simplify: We assume all instances point to the MAIN database for this prototype context
        # In real world, we'd connect to each instance.host.
        
        # Construct DSN for psycopg2 (standard postgresql:// scheme)
        dsn = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        
        try:
            with conn.cursor() as cur:
                # Check exist
                cur.execute("SELECT slot_name, active FROM pg_replication_slots WHERE slot_name = %s", (instance.replication_slot_name,))
                row = cur.fetchone()
                
                if row:
                    print(f"  [OK] Slot '{instance.replication_slot_name}' exists. Active: {row[1]}")
                else:
                    print(f"  [MISSING] Slot '{instance.replication_slot_name}' configured but NOT found in DB.")
                    
                    # Fix: If it looks like a test slot (starts with test_slot_), clear it.
                    # Or if it's supposed to be persistent, create it.
                    # Given the error logs show 'does not exist', let's recreate it if it seems valid, or clear it if it seems like junk.
                    
                    if instance.replication_slot_name.startswith("test_slot_"):
                        print(f"  [FIX] Clearing test slot configuration from DB instance record.")
                        instance.replication_slot_name = None
                        db.add(instance)
                        db.commit()
                    else:
                        print(f"  [FIX] Recreating missing persistent slot '{instance.replication_slot_name}'...")
                        try:
                            # Create slot
                            # output_plugin = 'pgoutput'
                            cur.execute(f"SELECT pg_create_logical_replication_slot('{instance.replication_slot_name}', 'pgoutput');")
                            print("  [SUCCESS] Slot created.")
                        except Exception as e:
                            print(f"  [ERROR] Failed to create slot: {e}")

        except Exception as e:
            print(f"  [ERROR] Check failed: {e}")
        finally:
            conn.close()

    # 3. Clean up orphaned slots in DB (Optional, but good for hygiene)
    # We won't do this blindly to avoid deleting slots used by others.
    
    print("Done.")

if __name__ == "__main__":
    fix_slots()
