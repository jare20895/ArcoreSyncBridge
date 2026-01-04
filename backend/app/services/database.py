import psycopg
from typing import Dict, Any, Optional, List
from app.models.core import DatabaseInstance

class DatabaseClient:
    def __init__(self, instance: DatabaseInstance, db_name: str = "postgres"):
        # Prioritize Instance credentials if available
        # Fallback to dev defaults only if missing
        
        user = instance.username or "arcore"
        password = instance.password or "arcore_password" # TODO: Decrypt if encrypted
        
        target_db = instance.db_name or db_name
        
        # Ensure host/port
        host = instance.host
        port = instance.port or 5432
        
        self.dsn = f"postgresql://{user}:{password}@{host}:{port}/{target_db}"

    def fetch_row(self, schema: str, table: str, pk_col: str, pk_val: Any) -> Optional[Dict[str, Any]]:
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                query = f"SELECT * FROM {schema}.{table} WHERE {pk_col} = %s"
                cur.execute(query, (pk_val,))
                
                if cur.description is None:
                    return None
                    
                col_names = [desc[0] for desc in cur.description]
                row = cur.fetchone()
                
                if row:
                    return dict(zip(col_names, row))
                return None

    def insert_row(self, schema: str, table: str, data: Dict[str, Any]) -> Any:
        # Returns PK if possible, or just confirms success
        cols = list(data.keys())
        if not cols:
            return None
            
        placeholders = ["%s"] * len(cols)
        col_str = ", ".join(cols)
        val_str = ", ".join(placeholders)
        
        query = f"INSERT INTO {schema}.{table} ({col_str}) VALUES ({val_str}) RETURNING *"
        
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, list(data.values()))
                # Return the full inserted row (including defaults/IDs generated)
                if cur.description:
                    col_names = [desc[0] for desc in cur.description]
                    row = cur.fetchone()
                    if row:
                        return dict(zip(col_names, row))
            conn.commit()
            return None

    def update_row(self, schema: str, table: str, pk_col: str, pk_val: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not data:
            return None
            
        set_clauses = [f"{k} = %s" for k in data.keys()]
        set_str = ", ".join(set_clauses)
        
        query = f"UPDATE {schema}.{table} SET {set_str} WHERE {pk_col} = %s RETURNING *"
        values = list(data.values()) + [pk_val]
        
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                if cur.description:
                    col_names = [desc[0] for desc in cur.description]
                    row = cur.fetchone()
                    if row:
                        return dict(zip(col_names, row))
            conn.commit()
            return None

    def delete_row(self, schema: str, table: str, pk_col: str, pk_val: Any) -> bool:
        query = f"DELETE FROM {schema}.{table} WHERE {pk_col} = %s"
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (pk_val,))
                return cur.rowcount > 0
            conn.commit()

    def fetch_changed_rows(self, schema: str, table: str, cursor_col: str, cursor_val: Optional[Any] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        where_clause = ""
        params = []
        if cursor_val is not None:
            where_clause = f"WHERE {cursor_col} > %s"
            params.append(cursor_val)

        query = f"SELECT * FROM {schema}.{table} {where_clause} ORDER BY {cursor_col} ASC LIMIT {limit}"
        print(f"[DEBUG] DatabaseClient SQL: {query}")
        print(f"[DEBUG] DatabaseClient Params: {params}")

        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                
                if cur.description is None:
                    return []
                    
                col_names = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                return [dict(zip(col_names, row)) for row in rows]

    def execute_raw(self, query: str, params: Optional[tuple] = None, autocommit: bool = False) -> List[tuple]:
        """Executes a raw query and returns all rows as tuples."""
        with psycopg.connect(self.dsn, autocommit=autocommit) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    return cur.fetchall()
                return []
