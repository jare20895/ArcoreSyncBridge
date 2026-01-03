import sys
import os
from app.db.session import SessionLocal
from app.services.cdc_consumer import CDCConsumer

# Add backend to path
sys.path.append(os.getcwd())

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
