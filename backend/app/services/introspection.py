import psycopg
from typing import List, Dict, Any, Optional
from app.schemas.introspection import TableInfo, ColumnInfo, SchemaSnapshot
from app.models.core import DatabaseInstance

def build_dsn(instance: DatabaseInstance, database_name: Optional[str] = None) -> str:
    user = instance.username or "arcore"
    password = instance.password or "arcore_password"
    db_name = database_name or instance.db_name or instance.database_name_override or "postgres"
    return f"postgresql://{user}:{password}@{instance.host}:{instance.port}/{db_name}"

class PostgresIntrospector:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def _get_table_inventory(self, cur, schema: str) -> List[Dict[str, Any]]:
        cur.execute(
            """
            SELECT
                t.table_schema,
                t.table_name,
                t.table_type,
                c.reltuples::bigint AS row_estimate
            FROM information_schema.tables t
            LEFT JOIN pg_namespace n
                ON n.nspname = t.table_schema
            LEFT JOIN pg_class c
                ON c.relname = t.table_name
                AND c.relnamespace = n.oid
            WHERE t.table_schema = %s
                AND t.table_type IN ('BASE TABLE', 'VIEW')
            ORDER BY t.table_name
            """,
            (schema,),
        )
        inventory = []
        for row in cur.fetchall():
            table_type = "VIEW" if row[2] == "VIEW" else "BASE"
            inventory.append(
                {
                    "schema_name": row[0],
                    "table_name": row[1],
                    "table_type": table_type,
                    "row_estimate": row[3],
                }
            )
        return inventory

    def get_table_inventory(self, schema: str = "public") -> List[Dict[str, Any]]:
        try:
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    return self._get_table_inventory(cur, schema)
        except Exception as e:
            raise RuntimeError(f"Introspection failed: {str(e)}")

    def _get_table_constraints(self, cur, schema: str, table_name: str) -> List[Dict[str, Any]]:
        cur.execute(
            """
            SELECT
                con.conname AS constraint_name,
                con.contype AS constraint_type,
                pg_get_constraintdef(con.oid) AS definition,
                array_remove(array_agg(att.attname ORDER BY arr.ordinality), NULL) AS columns,
                frel.relname AS referenced_table
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            LEFT JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS arr(attnum, ordinality) ON TRUE
            LEFT JOIN pg_attribute att
                ON att.attrelid = rel.oid
                AND att.attnum = arr.attnum
            LEFT JOIN pg_class frel ON frel.oid = con.confrelid
            WHERE nsp.nspname = %s AND rel.relname = %s
            GROUP BY con.conname, con.contype, definition, frel.relname
            """,
            (schema, table_name),
        )
        type_map = {
            "p": "PRIMARY_KEY",
            "f": "FOREIGN_KEY",
            "u": "UNIQUE",
            "c": "CHECK",
            "x": "EXCLUSION",
        }
        constraints = []
        for row in cur.fetchall():
            columns = row[3] or []
            constraints.append(
                {
                    "constraint_name": row[0],
                    "constraint_type": type_map.get(row[1], "OTHER"),
                    "definition": row[2],
                    "columns": columns,
                    "referenced_table": row[4],
                }
            )
        return constraints

    def _get_table_indexes(self, cur, schema: str, table_name: str) -> List[Dict[str, Any]]:
        cur.execute(
            """
            SELECT
                i.relname AS index_name,
                ix.indisunique AS is_unique,
                am.amname AS index_method,
                array_remove(array_agg(att.attname ORDER BY arr.ordinality), NULL) AS columns,
                pg_get_indexdef(ix.indexrelid) AS definition
            FROM pg_index ix
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_namespace nsp ON nsp.oid = t.relnamespace
            JOIN pg_am am ON i.relam = am.oid
            LEFT JOIN LATERAL unnest(ix.indkey) WITH ORDINALITY AS arr(attnum, ordinality) ON TRUE
            LEFT JOIN pg_attribute att
                ON att.attrelid = t.oid
                AND att.attnum = arr.attnum
            WHERE nsp.nspname = %s AND t.relname = %s
            GROUP BY i.relname, ix.indisunique, am.amname, ix.indexrelid
            """,
            (schema, table_name),
        )
        indexes = []
        for row in cur.fetchall():
            columns = row[3] or []
            indexes.append(
                {
                    "index_name": row[0],
                    "is_unique": row[1],
                    "index_method": row[2],
                    "columns": columns,
                    "definition": row[4],
                }
            )
        return indexes

    def _get_table_columns(
        self,
        cur,
        schema: str,
        table_name: str,
        primary_keys: set,
        unique_keys: set,
    ) -> List[Dict[str, Any]]:
        cur.execute(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                ordinal_position,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            (schema, table_name),
        )
        columns = []
        for row in cur.fetchall():
            default_value = row[4]
            identity_marker = (default_value or "").lower()
            is_identity = "identity" in identity_marker or "nextval" in identity_marker
            column_name = row[0]
            columns.append(
                {
                    "column_name": column_name,
                    "data_type": row[1],
                    "is_nullable": row[2] == "YES",
                    "ordinal_position": row[3],
                    "default_value": default_value,
                    "is_identity": is_identity,
                    "is_primary_key": column_name in primary_keys,
                    "is_unique": column_name in unique_keys,
                }
            )
        return columns

    def get_table_details(self, schema: str, table_name: str) -> Dict[str, Any]:
        try:
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    constraints = self._get_table_constraints(cur, schema, table_name)
                    primary_keys = {
                        col
                        for constraint in constraints
                        if constraint["constraint_type"] == "PRIMARY_KEY"
                        for col in constraint["columns"]
                    }
                    unique_keys = {
                        col
                        for constraint in constraints
                        if constraint["constraint_type"] in ("PRIMARY_KEY", "UNIQUE")
                        for col in constraint["columns"]
                    }
                    columns = self._get_table_columns(cur, schema, table_name, primary_keys, unique_keys)
                    indexes = self._get_table_indexes(cur, schema, table_name)
                    return {
                        "columns": columns,
                        "constraints": constraints,
                        "indexes": indexes,
                    }
        except Exception as e:
            raise RuntimeError(f"Introspection failed: {str(e)}")

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
                        cur.execute(
                            """
                            SELECT
                                column_name,
                                data_type,
                                is_nullable,
                                ordinal_position,
                                column_default
                            FROM information_schema.columns
                            WHERE table_schema = %s AND table_name = %s
                            ORDER BY ordinal_position
                            """,
                            (schema, t_name),
                        )
                        
                        cols = []
                        for row in cur.fetchall():
                            default_value = row[4]
                            identity_marker = (default_value or "").lower()
                            is_identity = "identity" in identity_marker or "nextval" in identity_marker
                            cols.append(ColumnInfo(
                                name=row[0],
                                data_type=row[1],
                                is_nullable=(row[2] == 'YES'),
                                ordinal_position=row[3],
                                default_value=default_value,
                                is_identity=is_identity
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
    dsn = build_dsn(instance)
    introspector = PostgresIntrospector(dsn)
    tables = introspector.get_tables(schema)
    
    return SchemaSnapshot(
        instance_id=str(instance.id),
        tables=tables
    )
