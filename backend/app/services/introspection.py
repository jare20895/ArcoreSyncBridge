import psycopg
from typing import List
from uuid import UUID
from app.schemas.introspection import TableInfo, ColumnInfo, SchemaSnapshot
from app.models.core import DatabaseInstance

class PostgresIntrospector:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def get_tables(self, schema: str = "public") -> List[TableInfo]:
        # Connect and query information_schema
        # Note: In a real implementation, we might need to handle connection pooling or use the app's engine if compatible
        # For now, using direct psycopg connection as per reference design for isolation
        
        tables = []
        try:
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    # 1. Get Tables
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s AND table_type = 'BASE TABLE'
                    """, (schema,))
                    table_names = [r[0] for r in cur.fetchall()]
                    
                    for t_name in table_names:
                        # 2. Get Columns
                        cur.execute("""
                            SELECT 
                                column_name, 
                                data_type, 
                                is_nullable,
                                ordinal_position
                            FROM information_schema.columns
                            WHERE table_schema = %s AND table_name = %s
                            ORDER BY ordinal_position
                        """, (schema, t_name))
                        
                        cols = []
                        for row in cur.fetchall():
                            cols.append(ColumnInfo(
                                name=row[0],
                                data_type=row[1],
                                is_nullable=(row[2] == 'YES'),
                                ordinal_position=row[3]
                            ))
                        
                        # 3. Identify PKs (Basic)
                        # A more robust query would join kcu/tco
                        cur.execute("""
                            SELECT kcu.column_name
                            FROM information_schema.key_column_usage kcu
                            JOIN information_schema.table_constraints tco 
                                ON kcu.constraint_name = tco.constraint_name
                                AND kcu.table_schema = tco.table_schema
                            WHERE tco.constraint_type = 'PRIMARY KEY'
                                AND kcu.table_schema = %s 
                                AND kcu.table_name = %s
                        """, (schema, t_name))
                        pks = {r[0] for r in cur.fetchall()}
                        
                        for c in cols:
                            if c.name in pks:
                                c.is_primary_key = True
                                
                        tables.append(TableInfo(
                            schema_name=schema,
                            table_name=t_name,
                            columns=cols
                        ))
        except Exception as e:
            # Re-raise or handle
            raise RuntimeError(f"Introspection failed: {str(e)}")
            
        return tables

def introspect_database(instance: DatabaseInstance, schema: str = "public") -> SchemaSnapshot:
    # Construct DSN from instance details
    user = instance.username or "arcore"
    password = instance.password or "arcore_password"
    db_name = instance.db_name or "postgres" # Fallback
    
    dsn = f"postgresql://{user}:{password}@{instance.host}:{instance.port}/{db_name}"
    
    introspector = PostgresIntrospector(dsn)
    tables = introspector.get_tables(schema)
    
    return SchemaSnapshot(
        instance_id=str(instance.id),
        tables=tables
    )
