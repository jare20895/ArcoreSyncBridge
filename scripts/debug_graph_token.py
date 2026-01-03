import os
import sys
import base64
import json
from dotenv import load_dotenv

# Ensure we can import from backend
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from app.services.graph import GraphClient

def decode_jwt_payload(token):
    try:
        payload_part = token.split('.')[1]
        payload_part += '=' * (-len(payload_part) % 4)
        decoded = base64.urlsafe_b64decode(payload_part)
        return json.loads(decoded)
    except Exception as e:
        return {"error": str(e)}

def main():
    # Load env from backend
    env_path = os.path.join(os.getcwd(), 'backend', '.env')
    print(f"Loading env from {env_path}")
    load_dotenv(env_path)
    
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    
    if not all([tenant_id, client_id, client_secret]):
        print("Error: Missing AZURE_TENANT_ID, AZURE_CLIENT_ID, or AZURE_CLIENT_SECRET in backend/.env")
        return

    print(f"Authenticating as Client ID: {client_id}")
    
    client = GraphClient(tenant_id, client_id, client_secret)
    try:
        # Force fresh token by bypassing cache logic in this script instance (new instance)
        token = client._get_access_token()
        print("Token acquired successfully.")
        
        claims = decode_jwt_payload(token)
        roles = claims.get('roles', [])
        print("\n--- Token Roles (Permissions) ---")
        print(f"Roles: {roles}")
        
        if "Sites.ReadWrite.All" in roles:
            print("[OK] 'Sites.ReadWrite.All' is present.")
        else:
            print("[CRITICAL] 'Sites.ReadWrite.All' is MISSING. Check Azure Portal > App Registrations.")

        print("\n--- Connectivity Test (Root Site) ---")
        try:
            root = client.request("GET", "/sites/root")
            print(f"Root Site Access: OK. Url: {root.get('webUrl')}")
        except Exception as e:
            print(f"Root Site Access: FAILED. {e}")

        print("\n--- Write Permission Test (AreCoreProjects) ---")
        site_path = "/sites/AreCoreProjects"
        try:
            # 1. Get Site ID
            clean_hostname = "arecorellc.sharepoint.com" # Hardcoded based on logs
            site = client.request("GET", f"/sites/{clean_hostname}:{site_path}")
            site_id = site["id"]
            print(f"Target Site Found. ID: {site_id}")

            # 2. Try to Create a Dummy List
            import random
            dummy_list_name = f"DebugList_{random.randint(1000,9999)}"
            print(f"Attempting to create list: {dummy_list_name}...")
            
            payload = {
                "displayName": dummy_list_name,
                "description": "Temporary debug list created by ArcoreSyncBridge script",
                "list": {"template": "genericList"}
            }
            new_list = client.request("POST", f"/sites/{site_id}/lists", json_body=payload)
            print(f"SUCCESS! List created. ID: {new_list['id']}")
            
            # 3. Cleanup
            print("Cleaning up (deleting list)...")
            client.request("DELETE", f"/sites/{site_id}/lists/{new_list['id']}")
            print("Cleanup successful.")

        except Exception as e:
            print(f"Write Test FAILED: {e}")


    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
