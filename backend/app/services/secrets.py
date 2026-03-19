import os

from fastapi import HTTPException

from app.models.core import SharePointConnection


def resolve_sharepoint_client_secret(connection: SharePointConnection) -> str:
    if connection.client_secret:
        return connection.client_secret

    env_client_id = os.environ.get("AZURE_CLIENT_ID")
    env_client_secret = os.environ.get("AZURE_CLIENT_SECRET")

    if env_client_id and env_client_secret and connection.client_id == env_client_id:
        return env_client_secret

    raise HTTPException(status_code=400, detail="SharePoint connection secret is missing")
