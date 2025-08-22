import time
import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HttpClient:
    def __init__(self, base_url: str, client_token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.client_token = client_token

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.client_token:
            # Đổi header nếu backend yêu cầu tên khác
            h["Access-Client-Token"] = self.client_token
        return h

    def get_json(self, path: str, params: Dict[str, Any] | None = None, retry: int = 3):
        url = f"{self.base_url}{path}"
        for i in range(1, retry+1):
            try:
                resp = requests.get(url, params=params, headers=self._headers(), timeout=15)
                if resp.status_code == 200:
                    return True, resp.json()
                logger.warning("GET %s -> %s: %s", url, resp.status_code, resp.text)
            except Exception as e:
                logger.exception("GET %s error: %s", url, e)
            time.sleep(0.6 * i)
        return False, {"error": "GET failed"}
