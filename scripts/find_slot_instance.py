import sys
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import settings
from app.models.core import DatabaseInstance

def find_instance():
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        instance = db.execute(
            select(DatabaseInstance).where(DatabaseInstance.replication_slot_name == 'arcorevector_cdc_slot')
        ).scalars().first()
        
        if instance:
            print(f"FOUND_INSTANCE_ID={instance.id}")
            print(f"FOUND_INSTANCE_LABEL={instance.instance_label}")
            print(f"FOUND_HOST={instance.host}")
        else:
            print("INSTANCE_NOT_FOUND")
            
    finally:
        db.close()

if __name__ == "__main__":
    find_instance()
