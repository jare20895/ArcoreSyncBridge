from typing import Dict, Any, Optional
from app.services.graph import GraphClient

class SharePointContentService:
    def __init__(self, graph_client: GraphClient):
        self.graph = graph_client

    def create_item(self, site_id: str, list_id: str, fields: Dict[str, Any]) -> str:
        """
        Creates an item in the specified list.
        Returns the SharePoint Item ID (usually an integer as string).
        """
        # Graph API: POST /sites/{site-id}/lists/{list-id}/items
        # Payload: { "fields": { ... } }
        payload = {"fields": fields}
        response = self.graph.request("POST", f"/sites/{site_id}/lists/{list_id}/items", json_body=payload)
        return response.get("id")

    def delete_item(self, site_id: str, list_id: str, item_id: str) -> None:
        """
        Deletes an item from the specified list.
        """
        # Graph API: DELETE /sites/{site-id}/lists/{list-id}/items/{item-id}
        self.graph.request("DELETE", f"/sites/{site_id}/lists/{list_id}/items/{item_id}")

    def update_item(self, site_id: str, list_id: str, item_id: str, fields: Dict[str, Any]) -> None:
        """
        Updates an item in the specified list.
        """
        # Graph API: PATCH /sites/{site-id}/lists/{list-id}/items/{item-id}/fields
        # Note: Updating 'fields' endpoint is often safer for preserving metadata than updating 'items' directly
        self.graph.request("PATCH", f"/sites/{site_id}/lists/{list_id}/items/{item_id}/fields", json_body=fields)

    def get_item(self, site_id: str, list_id: str, item_id: str) -> Dict[str, Any]:
        """
        Retrieves an item and its fields.
        """
        # Graph API: GET /sites/{site-id}/lists/{list-id}/items/{item-id}?expand=fields
        return self.graph.request("GET", f"/sites/{site_id}/lists/{list_id}/items/{item_id}?expand=fields")

    def get_list_changes(
        self, 
        site_id: str, 
        list_id: str, 
        delta_link: Optional[str] = None,
        callback: Optional[callable] = None
    ) -> tuple[list[Dict[str, Any]], str]:
        """
        Fetches changes from the list using Graph Delta Query.
        Returns (list_of_changes, new_delta_link).
        Handles pagination. 
        If callback is provided, calls callback(items) for each page and returns ([], new_delta_link) to save memory.
        """
        items = []
        
        # If we have a stored delta link, use it directly.
        if delta_link:
            if "graph.microsoft.com/v1.0" in delta_link:
                path = delta_link.split("graph.microsoft.com/v1.0")[1]
            else:
                path = delta_link
        else:
            path = f"/sites/{site_id}/lists/{list_id}/items/delta?expand=fields"

        while True:
            response = self.graph.request("GET", path)
            
            page_items = response.get("value", [])
            
            if callback:
                if page_items:
                    callback(page_items)
            else:
                items.extend(page_items)
            
            if "@odata.nextLink" in response:
                next_link = response["@odata.nextLink"]
                if "graph.microsoft.com/v1.0" in next_link:
                    path = next_link.split("graph.microsoft.com/v1.0")[1]
                else:
                    path = next_link
            elif "@odata.deltaLink" in response:
                return items, response["@odata.deltaLink"]
            else:
                # Should not happen in Delta Query flow unless empty or error
                break
                
        return items, ""
