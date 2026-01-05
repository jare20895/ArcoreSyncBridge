from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.core import DatabaseInstance
from app.services.database import DatabaseClient

class PublicationService:
    def __init__(self, db: Session):
        self.db = db

    def _get_instance(self, instance_id: UUID) -> DatabaseInstance:
        instance = self.db.get(DatabaseInstance, instance_id)
        if not instance:
            raise ValueError("Database instance not found")
        return instance

    def get_publication_status(self, instance_id: UUID, pub_name: str = "arcore_cdc_pub") -> Dict[str, Any]:
        instance = self._get_instance(instance_id)
        client = DatabaseClient(instance)
        
        # Check if publication exists
        check_query = "SELECT pubname, puballtables FROM pg_publication WHERE pubname = %s"
        try:
            rows = client.execute_raw(check_query, (pub_name,))
            if not rows:
                return {"exists": False, "all_tables": False, "tables": []}
            
            pub_all_tables = rows[0][1]
            
            tables = []
            if not pub_all_tables:
                # Fetch tables in publication
                # pg_publication_tables view: pubname, schemaname, tablename
                tables_query = "SELECT schemaname, tablename FROM pg_publication_tables WHERE pubname = %s"
                table_rows = client.execute_raw(tables_query, (pub_name,))
                tables = [f"{r[0]}.{r[1]}" for r in table_rows]
                
            return {
                "exists": True, 
                "all_tables": pub_all_tables, 
                "tables": tables
            }
        except Exception as e:
            raise RuntimeError(f"Failed to check publication status: {e}")

    def create_publication(self, instance_id: UUID, pub_name: str = "arcore_cdc_pub", for_all_tables: bool = True, tables: List[str] = []) -> None:
        instance = self._get_instance(instance_id)
        client = DatabaseClient(instance)
        
        # Validate inputs
        if not for_all_tables and not tables:
            raise ValueError("Must specify tables if not FOR ALL TABLES")
            
        sql = f"CREATE PUBLICATION {pub_name} "
        if for_all_tables:
            sql += "FOR ALL TABLES"
        else:
            # Sanitize table names? Assuming trusted input for now, but should ideally quote.
            # Simple quoting
            quoted_tables = [f'"{t.split(".")[0]}"."{t.split(".")[1]}"' if "." in t else f'"{t}"' for t in tables]
            sql += f"FOR TABLE {', '.join(quoted_tables)}"
            
        try:
            # CREATE PUBLICATION cannot run inside a transaction block in some versions/contexts, 
            # but usually fine. Autocommit needed?
            client.execute_raw(sql, autocommit=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create publication: {e}")

    def drop_publication(self, instance_id: UUID, pub_name: str = "arcore_cdc_pub") -> None:
        instance = self._get_instance(instance_id)
        client = DatabaseClient(instance)
        
        try:
            client.execute_raw(f"DROP PUBLICATION IF EXISTS {pub_name}", autocommit=True)
        except Exception as e:
            raise RuntimeError(f"Failed to drop publication: {e}")
