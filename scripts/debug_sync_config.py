import sys
import os
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load env
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

# Setup DB
from app.db.base import Base
from app.models.core import SyncDefinition, FieldMapping, SyncTarget
from app.models.inventory import SharePointList, SharePointColumn

# Connect
database_url = f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(database_url)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

def inspect_definition(def_id=None):
    if def_id:
        defs = [session.get(SyncDefinition, def_id)]
    else:
        defs = session.query(SyncDefinition).all()

    for d in defs:
        print(f"\n=== Sync Definition: {d.name} ({d.id}) ===")
        print(f"Target List ID (Def): {d.target_list_id}")
        
        # Check SyncTarget
        st = session.execute(select(SyncTarget).where(SyncTarget.sync_def_id == d.id)).scalars().first()
        if st:
            print(f"SyncTarget Record: Found. Target List ID: {st.target_list_id}")
        else:
            print(f"SyncTarget Record: NOT FOUND (Using Fallback?)")

        # Check Inventory List
        if d.target_list_id:
            l = session.get(SharePointList, d.target_list_id)
            if l:
                print(f"Inventory List: {l.display_name} (Status: {l.status})")
                print(f"SharePoint GUID: {l.list_id}")
                
                # Check Columns
                cols = session.execute(select(SharePointColumn).where(SharePointColumn.list_id == l.id)).scalars().all()
                print(f"Inventory Columns ({len(cols)}): {[c.column_name for c in cols]}")
            else:
                print("Inventory List: NOT FOUND")

        # Check Mappings
        mappings = session.execute(select(FieldMapping).where(FieldMapping.sync_def_id == d.id)).scalars().all()
        print(f"\nField Mappings ({len(mappings)}):")
        for m in mappings:
            print(f"  - {m.source_column_name} -> {m.target_column_name} (Type: {m.target_type})")

if __name__ == "__main__":
    # If arg provided
    if len(sys.argv) > 1:
        inspect_definition(sys.argv[1])
    else:
        inspect_definition()
