import sys
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import settings
from app.models.core import DatabaseInstance, SyncDefinition, SyncSource
from app.models.inventory import DatabaseTable

def check_cdc_enabled():
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Find instance
        instance = db.execute(
            select(DatabaseInstance).where(DatabaseInstance.replication_slot_name == 'arcorevector_cdc_slot')
        ).scalars().first()
        
        if not instance:
            print("INSTANCE_NOT_FOUND")
            return

        print(f"Checking CDC for Instance: {instance.instance_label} ({instance.id})")
        
        # 1. Check SyncDefinitions via SyncSource
        stmt_source = select(SyncDefinition).join(SyncSource).where(
            SyncSource.database_instance_id == instance.id,
            SyncSource.role == 'PRIMARY'
        )
        defs_source = db.execute(stmt_source).scalars().all()
        
        # 2. Check SyncDefinitions via DatabaseTable (Inventory)
        # We need to find tables belonging to this instance's database_id
        # Note: DatabaseInstance has database_id (logical database). DatabaseTable has database_id.
        # But wait, DatabaseTable belongs to a Database (logical), which might be hosted on multiple instances.
        # DatabaseInstance is a physical deployment of a Database.
        # If SyncDef points to a Table, we need to know WHICH Instance is active for that Database.
        
        defs_inventory = []
        if instance.database_id:
             stmt_inv = select(SyncDefinition).join(DatabaseTable, SyncDefinition.source_table_id == DatabaseTable.id).where(
                 DatabaseTable.database_id == instance.database_id
             )
             defs_inventory = db.execute(stmt_inv).scalars().all()

        all_defs = list(set(defs_source + defs_inventory))
        
        enabled_count = 0
        for d in all_defs:
            print(f"  SyncDef: {d.id} | Table: {d.source_table_name or 'Inventory:'+str(d.source_table_id)} | CDC Enabled: {d.cdc_enabled}")
            if d.cdc_enabled:
                enabled_count += 1
                
        if enabled_count == 0:
            print("  [WARNING] No SyncDefinitions have CDC enabled for this instance.")
        else:
            print(f"  [OK] Found {enabled_count} SyncDefinitions with CDC enabled.")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_cdc_enabled()
