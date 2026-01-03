import sys
from pathlib import Path

# Add backend to path (supports repo root or backend dir execution)
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.services.cdc_consumer import CDCConsumer

def run_consumer():
    db = SessionLocal()
    try:
        consumer = CDCConsumer(db)
        consumer.run()
    except Exception as e:
        print(f"Consumer Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_consumer()
