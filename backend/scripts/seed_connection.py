import sys
import os
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.session import SessionLocal
from app.models.core import SharePointConnection

def seed_connection():
    db = SessionLocal()
    try:
        tenant_id = "dae01a42-ccfe-4ad1-a451-c4474736ca3c"
        client_id = "afd34488-e880-43c4-b400-e65b9b61263c"
        # The user provided IDs but not the Secret (Client credentials: "Add a certificate or secret").
        # I will use a placeholder or ask the user to update it via UI.
        client_secret = "PLACEHOLDER_UPDATE_ME_IN_SETTINGS"
        
        print(f"Checking for existing connection for Tenant {tenant_id}...")
        existing = db.query(SharePointConnection).filter(
            SharePointConnection.tenant_id == tenant_id,
            SharePointConnection.client_id == client_id
        ).first()
        
        if existing:
            print("Connection already exists. Updating...")
            existing.status = "ACTIVE"
            # Don't overwrite secret if it might be valid
            if existing.client_secret == "PLACEHOLDER_SECRET_NEED_VAULT":
                 existing.client_secret = client_secret
        else:
            print("Creating new connection...")
            conn = SharePointConnection(
                id=uuid4(),
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
                authority_host="https://login.microsoftonline.com",
                scopes=["https://graph.microsoft.com/.default"],
                status="ACTIVE"
            )
            db.add(conn)
        
        db.commit()
        print("Seed completed successfully.")
        
    except Exception as e:
        print(f"Error seeding connection: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_connection()
