import time
import requests
import msal
from typing import Optional, Tuple, Dict, Any

class GraphClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, authority_host: str = "https://login.microsoftonline.com"):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.authority = f"{authority_host}/{tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]
        
        self._app = msal.ConfidentialClientApplication(
            client_id=client_id,
            authority=self.authority,
            client_credential=client_secret,
        )
        self._token_cache: Optional[Tuple[str, float]] = None

    def _get_access_token(self) -> str:
        # Check in-memory cache
        if self._token_cache:
            token, exp = self._token_cache
            # Buffer of 60 seconds
            if time.time() < (exp - 60):
                return token

        # Acquire new token
        result = self._app.acquire_token_for_client(scopes=self.scopes)
        if "access_token" not in result:
            error_desc = result.get('error_description') or result.get('error') or str(result)
            raise RuntimeError(f"Graph token acquisition failed: {error_desc}")
            
        token = result["access_token"]
        # MSAL usually returns 'expires_in' (seconds)
        exp = time.time() + int(result.get("expires_in", 3599))
        self._token_cache = (token, exp)
        return token

    def request(self, method: str, path: str, params: Optional[Dict] = None, json_body: Optional[Dict] = None) -> Any:
        url = f"https://graph.microsoft.com/v1.0{path}"
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        print(f"[DEBUG] Graph API Request: {method} {url}")
        if json_body:
            print(f"[DEBUG] Request Body: {json_body}")

        # Basic retry logic for throttling (429) or temporary server errors (503)
        max_retries = 3
        for attempt in range(max_retries):
            resp = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=30
            )

            print(f"[DEBUG] Response Status: {resp.status_code}")
            if resp.status_code >= 400:
                print(f"[DEBUG] Error Response: {resp.text}")

            if resp.status_code in (429, 503):
                retry_after = int(resp.headers.get("Retry-After", 5))
                time.sleep(min(retry_after, 30))
                continue

            if resp.status_code == 403:
                raise RuntimeError(
                    f"Graph {method} {path} failed [403] - Access Denied. "
                    "Ensure the App Registration has 'Sites.ReadWrite.All' (Application) permission "
                    "and Admin Consent is granted. See docs/guides/admin/sharepoint_setup.md."
                )

            if resp.status_code >= 400:
                raise RuntimeError(f"Graph {method} {path} failed [{resp.status_code}]: {resp.text}")
            
            # Return JSON if content exists, else empty dict
            return resp.json() if resp.content else {}
            
        raise RuntimeError(f"Graph request failed after {max_retries} retries: {method} {path}")
