# src/get_userid_from_txn.py
# -*- coding: utf-8 -*-
import os, sys, time, json
from typing import Optional, Any, Union, List
import requests

DEFAULT_BASE_URL = "https://wallet.vndc.io/api/transactions"

def _resolve_access_token() -> str:
    """Ưu tiên OnusLibs; fallback ENV ACCESS_CLIENT_TOKEN. Không dùng onusconfig."""
    # 1) OnusLibs (nếu lib của bạn cung cấp hàm này)
    try:
        from OnusLibs.auth import get_access_client_token  # type: ignore
        tok = get_access_client_token()
        if tok:
            return tok
    except Exception:
        pass
    # 2) ENV (có thể set trong phiên venv)
    tok = os.getenv("ACCESS_CLIENT_TOKEN")
    if not tok:
        # (tuỳ chọn) thử nạp .env nếu có python-dotenv, nhưng không bắt buộc
        try:
            from dotenv import load_dotenv  # pip install python-dotenv (nếu muốn)
            load_dotenv()
            tok = os.getenv("ACCESS_CLIENT_TOKEN")
        except Exception:
            pass
    if not tok:
        raise RuntimeError("Thiếu ACCESS_CLIENT_TOKEN. Set ENV hoặc để OnusLibs trả token.")
    return tok

def _deep_get(d: Any, path: list[Union[str, int]]) -> Any:
    cur = d
    for key in path:
        if isinstance(cur, dict) and isinstance(key, str):
            cur = cur.get(key)
        elif isinstance(cur, list) and isinstance(key, int) and 0 <= key < len(cur):
            cur = cur[key]
        else:
            return None
    return cur

def _extract_user_id_recursive(obj: Any) -> Optional[str]:
    keys = ("user_id", "userId", "userid")
    if isinstance(obj, dict):
        if isinstance(obj.get("user"), dict):
            for k in ("id", "user_id", "userId"):
                v = obj["user"].get(k)
                if v not in (None, ""):
                    return str(v)
        for k in keys:
            v = obj.get(k)
            if v not in (None, ""):
                return str(v)
        for v in obj.values():
            uid = _extract_user_id_recursive(v)
            if uid:
                return uid
    elif isinstance(obj, list):
        for it in obj:
            uid = _extract_user_id_recursive(it)
            if uid:
                return uid
    return None

def get_user_id_from_vndc(
    vndc_code: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 15.0,
    max_retries: int = 3,
    backoff: float = 0.5,
) -> Optional[str]:
    """Trả về user_id; ưu tiên to.user.id, rồi from.user.id, rồi dò đệ quy."""
    token = _resolve_access_token()
    params = {"transactionNumber": vndc_code}
    headers = {"Access-Client-Token": token, "Accept": "application/json"}

    last_status = None
    for i in range(max_retries):
        r = requests.get(base_url, params=params, headers=headers, timeout=timeout)
        last_status = r.status_code
        if r.status_code == 200:
            try:
                data = r.json()
            except Exception:
                data = json.loads(r.text)
            tx = data[0] if isinstance(data, list) and data else data
            uid = _deep_get(tx, ["to", "user", "id"]) or _deep_get(tx, ["from", "user", "id"])
            return str(uid) if uid else _extract_user_id_recursive(tx)
        if r.status_code in (401, 403):
            raise PermissionError(f"Không đủ quyền (HTTP {r.status_code}). Kiểm tra token.")
        if r.status_code == 404:
            return None
        time.sleep(backoff * (2 ** i))
    raise RuntimeError(f"API không phản hồi (HTTP {last_status}).")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.get_userid_from_txn <VNDCxxxxxx>")
        sys.exit(2)
    code = sys.argv[1].strip()
    try:
        print(get_user_id_from_vndc(code) or "")
    except Exception:
        print("")
        sys.exit(1)
