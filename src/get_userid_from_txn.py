# src/get_userid_from_txn.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import time
from typing import Any, Dict, Optional, Tuple

import requests
import src.config as CFG

logger = logging.getLogger(__name__)

# --------- helpers ---------
def _headers(base: str = "tx") -> Dict[str, str]:
    """base='tx' dùng token API giao dịch; base='user' dùng token user API."""
    h = {"Content-Type": "application/json"}
    if base == "user":
        if CFG.USER_API_ACCESS_TOKEN:
            h[CFG.USER_API_AUTH_HEADER_NAME] = CFG.USER_API_ACCESS_TOKEN
    else:
        if CFG.ACCESS_CLIENT_TOKEN:
            h[CFG.API_AUTH_HEADER_NAME] = CFG.ACCESS_CLIENT_TOKEN
    return h

def _extract_by_dotted_path(obj: Any, path: str) -> Any:
    """
    Lấy giá trị theo 'dotted path', hỗ trợ index mảng:
      - "0.to.user.id", "data.0.userId", "data[0].userId"
    Cho phép nhiều fallback path, ngăn cách bằng '|'.
    """
    def _walk(o: Any, single_path: str) -> Any:
        try:
            cur = o
            norm = single_path.replace("[", ".").replace("]", "")
            for key in norm.split("."):
                if key == "":
                    continue
                if isinstance(cur, list) and key.isdigit():
                    idx = int(key)
                    if 0 <= idx < len(cur):
                        cur = cur[idx]
                    else:
                        return None
                elif isinstance(cur, dict):
                    if key in cur:
                        cur = cur[key]
                    else:
                        return None
                else:
                    return None
            return cur
        except Exception:
            return None

    for candidate in (p.strip() for p in str(path).split("|")):
        if not candidate:
            continue
        val = _walk(obj, candidate)
        if val is not None:
            return val
    return None

# --------- TXN resolve (B2A) ---------
def _request_once_txn(vndc_code: str) -> Tuple[bool, Dict[str, Any]]:
    url = f"{CFG.API_BASE_URL}{CFG.API_RESOLVE_PATH}"
    params = {CFG.API_QUERY_PARAM_NAME: vndc_code}
    try:
        if CFG.API_METHOD == "POST":
            resp = requests.post(url, json=params, headers=_headers("tx"), timeout=CFG.API_TIMEOUT)
        else:
            resp = requests.get(url, params=params, headers=_headers("tx"), timeout=CFG.API_TIMEOUT)
        if resp.status_code == 200:
            return True, resp.json()
        safe_params = {CFG.API_QUERY_PARAM_NAME: "***"}
        logger.warning("Resolve API %s %s %s -> %s: %s", CFG.API_METHOD, url, safe_params, resp.status_code, resp.text[:300])
        return False, {"status": resp.status_code, "body": resp.text}
    except Exception as e:
        logger.exception("Resolve API error: %s %s -> %r", CFG.API_METHOD, url, e)
        return False, {"error": str(e)}

def _request_with_retry_txn(vndc_code: str) -> Tuple[bool, Dict[str, Any]]:
    retries = max(1, CFG.API_RETRIES)
    last: Dict[str, Any] = {}
    for attempt in range(1, retries + 1):
        ok, data = _request_once_txn(vndc_code)
        if ok:
            return True, data
        last = data
        time.sleep(CFG.API_RETRY_BACKOFF_SEC * attempt)
    return False, last

def resolve_fields(vndc_code: str) -> Dict[str, Any]:
    """Trả về dict các trường theo CFG.RESOLVE_RESPONSE_PATHS (từ TXN API)."""
    ok, payload = _request_with_retry_txn(vndc_code)
    if not ok:
        return {"__error__": payload.get("error") or payload.get("status") or "http_error"}
    out: Dict[str, Any] = {}
    for field_name, dotted in (CFG.RESOLVE_RESPONSE_PATHS or {}).items():
        out[field_name] = _extract_by_dotted_path(payload, dotted) if dotted else None
    return out

def get_user_id_from_vndc(vndc_code: str) -> Optional[str]:
    fields = resolve_fields(vndc_code)
    if "__error__" in fields:
        return None
    uid = fields.get("user_id")
    return str(uid) if uid is not None else None

# --------- USER lookup (B2B) ---------
def _request_once_user(user_id: str) -> Tuple[bool, Dict[str, Any]]:
    url = f"{CFG.USER_API_BASE_URL}{CFG.USER_API_PATH}"
    # gộp params cố định + usersToInclude=<id>
    params = dict(CFG.USER_API_FIXED_PARAMS or {})
    params[CFG.USER_API_PARAM_USER_IDS] = user_id
    try:
        if CFG.USER_API_METHOD == "POST":
            resp = requests.post(url, json=params, headers=_headers("user"), timeout=CFG.API_TIMEOUT)
        else:
            resp = requests.get(url, params=params, headers=_headers("user"), timeout=CFG.API_TIMEOUT)
        if resp.status_code == 200:
            return True, resp.json()
        logger.warning("User API %s %s -> %s: %s", CFG.USER_API_METHOD, url, resp.status_code, resp.text[:300])
        return False, {"status": resp.status_code, "body": resp.text}
    except Exception as e:
        logger.exception("User API error: %s %s -> %r", CFG.USER_API_METHOD, url, e)
        return False, {"error": str(e)}

def resolve_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Trả về {"username": "...", "vip_level": "...", "document_number": "..."} theo USER_RESPONSE_PATHS.
    Thất bại -> {"__error__": "..."}.
    """
    ok, payload = _request_once_user(user_id)
    if not ok:
        return {"__error__": payload.get("error") or payload.get("status") or "http_error"}
    out: Dict[str, Any] = {}
    for field_name, dotted in (CFG.USER_RESPONSE_PATHS or {}).items():
        out[field_name] = _extract_by_dotted_path(payload, dotted) if dotted else None
    return out

# --------- Hợp nhất (B2A -> B2B) ---------
def resolve_user_all(vndc_code: str) -> Dict[str, Any]:
    """
    Pipeline đầy đủ:
      1) TXN -> lấy {user_id, fullname}
      2) USER -> lấy {username, vip_level, document_number}
    """
    res_txn = resolve_fields(vndc_code)
    if "__error__" in res_txn:
        return res_txn
    user_id = res_txn.get("user_id")
    if not user_id:
        return {"__error__": "resolve_none"}
    res_user = resolve_user_profile(str(user_id))
    if "__error__" in res_user:
        # vẫn trả về thông tin đã có từ TXN để CSV ghi audit
        return {"user_id": str(user_id), "fullname": res_txn.get("fullname"), "__error__": res_user["__error__"]}
    # merge kết quả
    merged = dict(res_txn)
    merged.update(res_user)
    return merged
