from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.inventory import SharePointSite, SharePointList
from app.models.core import SharePointConnection
from app.services.graph import GraphClient

class SharePointDiscoveryService:
    def __init__(self, db: Session, graph_client: GraphClient):
        self.db = db
        self.graph = graph_client

    def extract_sites(self, connection_id: UUID, query: str = "*") -> List[SharePointSite]:
        """
        Search for SharePoint sites using Graph API and persist them to inventory.
        """
        # Graph API Search
        # Note: 'search=*' returns relevant sites.
        resp = self.graph.request("GET", "/sites", params={"search": query})
        
        sites_data = resp.get("value", [])
        results = []

        conn = self.db.get(SharePointConnection, connection_id)
        if not conn:
             raise ValueError("Connection not found")

        for site_item in sites_data:
            # Graph returns 'siteCollection' and 'webUrl'
            # id is usually 'hostname,s-uuid,w-uuid'
            
            # Skip if not a proper site (some results might be odd)
            if "webUrl" not in site_item:
                continue
                
            web_url = site_item["webUrl"]
            hostname = site_item.get("siteCollection", {}).get("hostname")
            
            # If hostname missing in payload, try parsing from webUrl or id
            if not hostname:
                from urllib.parse import urlparse
                hostname = urlparse(web_url).hostname

            # Site Path
            path = urlparse(web_url).path
            if not path:
                path = "/"

            graph_site_id = site_item["id"]

            # Upsert
            existing = self.db.execute(
                select(SharePointSite).where(
                    SharePointSite.connection_id == connection_id,
                    SharePointSite.site_id == graph_site_id
                )
            ).scalar_one_or_none()

            if existing:
                existing.web_url = web_url
                existing.hostname = hostname
                existing.site_path = path
                site_obj = existing
            else:
                site_obj = SharePointSite(
                    connection_id=connection_id,
                    tenant_id=conn.tenant_id,
                    hostname=hostname,
                    site_path=path,
                    site_id=graph_site_id,
                    web_url=web_url,
                    status="ACTIVE"
                )
                self.db.add(site_obj)
            
            results.append(site_obj)
        
        self.db.commit()
        return results

    def extract_lists(self, site_db_id: UUID) -> List[SharePointList]:
        """
        Fetch lists for a specific persisted SharePointSite.
        """
        site = self.db.get(SharePointSite, site_db_id)
        if not site:
            raise ValueError("Site not found")

        # 1. Fetch current lists from Graph
        resp = self.graph.request("GET", f"/sites/{site.site_id}/lists")
        lists_data = resp.get("value", [])
        
        # 2. Get all existing lists from DB
        existing_lists = self.db.execute(
            select(SharePointList).where(SharePointList.site_id == site_db_id)
        ).scalars().all()
        
        existing_map = {l.list_id: l for l in existing_lists}
        
        # Track seen IDs from Graph
        seen_list_ids = set()
        results = []

        # 3. Upsert present lists
        for list_item in lists_data:
            list_id_guid = list_item.get("id") # The GUID
            seen_list_ids.add(list_id_guid)
            
            display_name = list_item.get("displayName")
            description = list_item.get("description", "")
            template = list_item.get("list", {}).get("template", "genericList")
            
            if list_id_guid in existing_map:
                list_obj = existing_map[list_id_guid]
                list_obj.display_name = display_name
                list_obj.description = description
                list_obj.template = template
                list_obj.status = "ACTIVE" # Ensure it is active if found
            else:
                list_obj = SharePointList(
                    site_id=site_db_id,
                    list_id=list_id_guid,
                    display_name=display_name,
                    description=description,
                    template=template,
                    is_provisioned=False,
                    status="ACTIVE"
                )
                self.db.add(list_obj)
            
            results.append(list_obj)

        # 4. Mark missing lists as DELETED
        for list_id, list_obj in existing_map.items():
            if list_id not in seen_list_ids:
                list_obj.status = "DELETED"

        self.db.commit()
        return results
