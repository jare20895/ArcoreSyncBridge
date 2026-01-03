import re
from typing import List, Dict, Optional, Any
from app.services.graph import GraphClient
from app.schemas.introspection import ColumnInfo

def sp_safe_internal_name(col_name: str) -> str:
    """
    SharePoint internal column names have practical constraints.
    Keep it conservative: alphanumerics + underscore, leading letter.
    """
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", col_name).strip("_")
    if not cleaned:
        cleaned = "Field"
    if not re.match(r"^[A-Za-z]", cleaned):
        cleaned = f"F_{cleaned}"
    return cleaned[:64]

def map_pg_to_sp_column(col: ColumnInfo) -> Dict[str, Any]:
    """
    Map a subset of Postgres data_type values into Graph columnDefinition payloads.
    """
    t = col.data_type.lower()

    # Text types
    if t in ("character varying", "character", "text", "varchar"):
        return {
            "name": sp_safe_internal_name(col.name),
            "text": {"allowMultipleLines": (t == "text")},
            "required": (not col.is_nullable),
            "enforceUniqueValues": False,
        }

    # Number types
    if t in ("integer", "smallint", "bigint", "numeric", "decimal", "real", "double precision", "int"):
        return {
            "name": sp_safe_internal_name(col.name),
            "number": {"decimalPlaces": "automatic"},
            "required": (not col.is_nullable),
            "enforceUniqueValues": False,
        }

    # Boolean
    if t in ("boolean", "bool"):
        return {
            "name": sp_safe_internal_name(col.name),
            "boolean": {},
            "required": (not col.is_nullable),
            "enforceUniqueValues": False,
        }

    # DateTime
    if t in ("timestamp without time zone", "timestamp with time zone", "date", "timestamp"):
        return {
            "name": sp_safe_internal_name(col.name),
            "dateTime": {"displayAs": "default"},
            "required": (not col.is_nullable),
            "enforceUniqueValues": False,
        }

    # Fallback to text for unknown types (e.g., json, uuid)
    return {
        "name": sp_safe_internal_name(col.name),
        "text": {"allowMultipleLines": True},
        "required": (not col.is_nullable),
        "enforceUniqueValues": False,
    }

class SharePointProvisioner:
    def __init__(self, graph_client: GraphClient):
        self.graph = graph_client

    def get_site(self, hostname: str, site_path: str) -> Dict[str, Any]:
        # site_path example: "/sites/Finance"
        # Graph API format: GET /sites/{hostname}:{server-relative-path}
        # Strip protocol if present (e.g., "https://")
        clean_hostname = hostname.replace("https://", "").replace("http://", "").strip("/")
        return self.graph.request("GET", f"/sites/{clean_hostname}:{site_path}")

    def find_list_by_display_name(self, site_id: str, display_name: str) -> Optional[Dict[str, Any]]:
        lists = self.graph.request("GET", f"/sites/{site_id}/lists")
        for lst in lists.get("value", []):
            if lst.get("displayName") == display_name:
                return lst
        return None

    def create_list(self, site_id: str, display_name: str, description: str = "") -> Dict[str, Any]:
        payload = {
            "displayName": display_name,
            "description": description,
            "list": {"template": "genericList"},
        }
        print(f"[DEBUG] Creating list at site_id: {site_id}")
        print(f"[DEBUG] Payload: {payload}")
        return self.graph.request("POST", f"/sites/{site_id}/lists", json_body=payload)

    def list_columns(self, site_id: str, list_id: str) -> Dict[str, Dict[str, Any]]:
        cols = self.graph.request("GET", f"/sites/{site_id}/lists/{list_id}/columns")
        by_name = {}
        for c in cols.get("value", []):
            by_name[c.get("name")] = c
        return by_name

    def create_column(self, site_id: str, list_id: str, column_def: Dict[str, Any]) -> Dict[str, Any]:
        return self.graph.request("POST", f"/sites/{site_id}/lists/{list_id}/columns", json_body=column_def)

    def provision_table_to_list(
        self,
        site_id: str,
        pg_columns: List[ColumnInfo],
        list_display_name: str,
        description: str = "",
        skip_columns: Optional[List[str]] = None,
        column_configurations: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        skip_columns = set(skip_columns or [])
        column_configurations = column_configurations or {}

        # 1. Ensure List Exists
        lst = self.find_list_by_display_name(site_id, list_display_name)
        if not lst:
            lst = self.create_list(site_id, list_display_name, description)
        
        list_id = lst["id"]

        # 2. Get Existing Columns (to avoid duplicates)
        existing_cols = self.list_columns(site_id, list_id)

        created = []
        skipped = []
        errors = []

        # 3. Create Missing Columns
        for col in pg_columns:
            if col.name in skip_columns:
                skipped.append({"name": col.name, "reason": "user_skipped"})
                continue

            sp_col_def = map_pg_to_sp_column(col)
            
            # Apply user overrides
            if col.name in column_configurations:
                override = column_configurations[col.name]
                # If the override specifies a new type (e.g., 'number' instead of 'text'),
                # we must remove conflicting type keys from the default mapping.
                # Standard Graph column types:
                type_keys = ["text", "number", "boolean", "dateTime", "currency", "choice", "lookup", "personOrGroup"]
                
                # If override has any of these keys, clear existing type keys
                if any(k in override for k in type_keys):
                    for k in type_keys:
                        if k in sp_col_def:
                            del sp_col_def[k]
                
                # Apply the overrides
                sp_col_def.update(override)

            sp_name = sp_col_def["name"]

            # Check if internal name exists
            if sp_name in existing_cols:
                skipped.append({"name": col.name, "reason": "already_exists", "sp_name": sp_name})
                continue
            
            # Check if Title/LinkTitle exists (genericList default)
            # If mapping logic is advanced, we might map a specific PG col to Title.
            # For now, if sp_name happens to conflict with Title, skip or rename.
            # (Note: 'Title' is internal name 'Title')
            if sp_name == "Title":
                 skipped.append({"name": col.name, "reason": "conflict_with_title"})
                 continue

            try:
                result = self.create_column(site_id, list_id, sp_col_def)
                created.append({"pg_name": col.name, "sp_name": sp_name, "id": result.get("id")})
            except Exception as e:
                errors.append({"name": col.name, "error": str(e)})

        return {
            "site_id": site_id,
            "list": {"id": list_id, "displayName": lst.get("displayName")},
            "columns_created": created,
            "columns_skipped": skipped,
            "errors": errors
        }
