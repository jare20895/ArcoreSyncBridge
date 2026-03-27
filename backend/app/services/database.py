import psycopg
from psycopg import sql
from psycopg.abc import Query
from typing import Dict, Any, Optional, List
from app.models.core import DatabaseInstance

class DatabaseClient:
    def __init__(self, instance: DatabaseInstance, db_name: str = "postgres"):
        user = instance.username
        password = instance.password
        target_db = instance.db_name or db_name

        if not user:
            raise ValueError(f"Database instance '{instance.instance_label}' is missing a username")
        if not password:
            raise ValueError(f"Database instance '{instance.instance_label}' is missing a password")
        if not target_db:
            raise ValueError(f"Database instance '{instance.instance_label}' is missing a database name")

        host = instance.host
        port = instance.port or 5432

        self.dsn = f"postgresql://{user}:{password}@{host}:{port}/{target_db}"

    @staticmethod
    def _qualified_table(schema: str, table: str) -> sql.Composed:
        return sql.SQL(".").join([sql.Identifier(schema), sql.Identifier(table)])

    def fetch_row(self, schema: str, table: str, pk_col: str, pk_val: Any) -> Optional[Dict[str, Any]]:
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                query = sql.SQL("SELECT * FROM {} WHERE {} = %s").format(
                    self._qualified_table(schema, table),
                    sql.Identifier(pk_col),
                )
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
        val_str = ", ".join(placeholders)

        query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
            self._qualified_table(schema, table),
            sql.SQL(", ").join(sql.Identifier(col) for col in cols),
            sql.SQL(val_str),
        )
        
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

        set_clause = sql.SQL(", ").join(
            sql.SQL("{} = %s").format(sql.Identifier(col))
            for col in data.keys()
        )

        query = sql.SQL("UPDATE {} SET {} WHERE {} = %s RETURNING *").format(
            self._qualified_table(schema, table),
            set_clause,
            sql.Identifier(pk_col),
        )
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
        query = sql.SQL("DELETE FROM {} WHERE {} = %s").format(
            self._qualified_table(schema, table),
            sql.Identifier(pk_col),
        )
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (pk_val,))
                return cur.rowcount > 0
            conn.commit()

    def fetch_changed_rows(self, schema: str, table: str, cursor_col: str, cursor_val: Optional[Any] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        where_clause = ""
        params = []
        if cursor_val is not None:
            where_clause = sql.SQL("WHERE {} > %s").format(sql.Identifier(cursor_col))
            params.append(cursor_val)
        else:
            where_clause = sql.SQL("")

        query = sql.SQL("SELECT * FROM {} {} ORDER BY {} ASC LIMIT {}").format(
            self._qualified_table(schema, table),
            where_clause,
            sql.Identifier(cursor_col),
            sql.Literal(limit),
        )

        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                
                if cur.description is None:
                    return []
                    
                col_names = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                return [dict(zip(col_names, row)) for row in rows]

    def execute_raw(self, query: Query, params: Optional[tuple] = None, autocommit: bool = False) -> List[tuple]:
        """Executes a raw query and returns all rows as tuples."""
        with psycopg.connect(self.dsn, autocommit=autocommit) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    return cur.fetchall()
                return []
