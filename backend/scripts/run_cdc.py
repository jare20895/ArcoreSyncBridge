import sys
from uuid import UUID
from pathlib import Path

# Add backend to path (supports repo root or backend dir execution)
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.models.core import DatabaseInstance
from app.services.cdc import CDCService

def run_cdc_for_instance(instance_id_str):
    db = SessionLocal()
    try:
        instance_id = UUID(instance_id_str)
        service = CDCService(db, instance_id)
        service.run()
    except Exception as e:
        print(f"CDC Worker Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Auto-discover primary instance
        db = SessionLocal()
        instance = db.query(DatabaseInstance).filter(DatabaseInstance.status == "ACTIVE").first()
        db.close()
        if instance:
            print(f"Auto-detected Instance: {instance.id}")
            run_cdc_for_instance(str(instance.id))
        else:
            print("Usage: python run_cdc.py <instance_id>")
            sys.exit(1)
    else:
        run_cdc_for_instance(sys.argv[1])
