from typing import List, Dict, Any, Optional
from uuid import UUID
from psycopg import sql
from sqlalchemy.orm import Session
from app.models.core import DatabaseInstance
from app.services.database import DatabaseClient
from app.services.introspection import PostgresIntrospector, build_dsn

class PublicationService:
    def __init__(self, db: Session):
        self.db = db

    def _get_instance(self, instance_id: UUID) -> DatabaseInstance:
        instance = self.db.get(DatabaseInstance, instance_id)
        if not instance:
            raise ValueError("Database instance not found")
        return instance

    def get_available_tables(self, instance_id: UUID, schema: str = "public") -> List[str]:
        instance = self._get_instance(instance_id)
        dsn = build_dsn(instance)
        introspector = PostgresIntrospector(dsn)
        
        inventory = introspector.get_table_inventory(schema)
        # Return list of "schema.table"
        return [f"{t['schema_name']}.{t['table_name']}" for t in inventory if t['table_type'] == 'BASE']

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

    @staticmethod
    def _qualified_publication_table(table_name: str) -> sql.Composed:
        parts = table_name.split(".")
        if len(parts) == 1 and parts[0]:
            return sql.Identifier(parts[0])
        if len(parts) == 2 and all(parts):
            return sql.SQL(".").join([sql.Identifier(parts[0]), sql.Identifier(parts[1])])
        raise ValueError(f"Invalid table reference: {table_name}")

    def create_publication(self, instance_id: UUID, pub_name: str = "arcore_cdc_pub", for_all_tables: bool = True, tables: List[str] = []) -> None:
        instance = self._get_instance(instance_id)
        client = DatabaseClient(instance)
        
        # Validate inputs
        if not for_all_tables and not tables:
            raise ValueError("Must specify tables if not FOR ALL TABLES")
            
        try:
            if for_all_tables:
                statement = sql.SQL("CREATE PUBLICATION {} FOR ALL TABLES").format(
                    sql.Identifier(pub_name)
                )
            else:
                table_list = sql.SQL(", ").join(
                    self._qualified_publication_table(table_name)
                    for table_name in tables
                )
                statement = sql.SQL("CREATE PUBLICATION {} FOR TABLE {}").format(
                    sql.Identifier(pub_name),
                    table_list,
                )
            client.execute_raw(statement, autocommit=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create publication: {e}")

    def drop_publication(self, instance_id: UUID, pub_name: str = "arcore_cdc_pub") -> None:
        instance = self._get_instance(instance_id)
        client = DatabaseClient(instance)
        
        try:
            statement = sql.SQL("DROP PUBLICATION IF EXISTS {}").format(sql.Identifier(pub_name))
            client.execute_raw(statement, autocommit=True)
        except Exception as e:
            raise RuntimeError(f"Failed to drop publication: {e}")
