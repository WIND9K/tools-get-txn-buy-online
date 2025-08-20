# -*- coding: utf-8 -*-
"""
get_userid_from_txn.py

Lấy user_id từ mã giao dịch VNDC qua API Wallet.
- Ưu tiên lấy Access-Client-Token thông qua OnusLibs (tương thích dự án Onus Report)
- Fallback lấy từ biến môi trường ACCESS_CLIENT_TOKEN nếu OnusLibs không sẵn.

Dùng như module:
    from src.get_userid_from_txn import get_user_id_from_vndc
    uid = get_user_id_from_vndc("VNDC2610593029")

Chạy CLI:
    python src/get_userid_from_txn.py VNDC2610593029
In ra user_id (hoặc chuỗi rỗng nếu không tìm thấy).
"""

from __future__ import annotations

import os
import sys
import time
import json
from typing import Optional, Any

import requests

DEFAULT_BASE_URL = "https://wallet.vndc.io/api/transactions"
DEFAULT_TIMEOUT = 15.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF = 0.5  # giây, exponential backoff

# ===== Access token resolver (ưu tiên OnusLibs) =====

def _resolve_access_token() -> str:
    token: Optional[str] = None

    # 1) OnusLibs.auth (tuỳ phiên bản/thư mục cài đặt)
    try:
        from OnusLibs.auth import get_access_client_token  # type: ignore
        token = get_access_client_token()
    except Exception:
        pass
    if token:
        return token

    # 2) OnusLibs.config (secrets)
    try:
        from OnusLibs.config import get_secret  # type: ignore
        token = get_secret("ACCESS_CLIENT_TOKEN")
    except Exception:
        pass
    if token:
        return token

    # 3) SecureManager style của OnusReport
    try:
        from onusconfig.security.secure_manager import SecureManager  # type: ignore
        token = SecureManager().get("ACCESS_CLIENT_TOKEN")
    except Exception:
        pass
    if token:
        return token

    # 4) ENV
    token = os.getenv("ACCESS_CLIENT_TOKEN") or os.getenv("ONUS_ACCESS_CLIENT_TOKEN")
    if token:
        return token

    raise RuntimeError("Không tìm thấy ACCESS_CLIENT_TOKEN qua OnusLibs hoặc ENV.")


# ===== JSON extractor =====

_USER_ID_KEYS = (
    "user_id",
    "userId",
    "userid",
    "toUserId",
    "fromUserId",
    "ownerId",
    "customerId",
)


def _extract_user_id(obj: Any) -> Optional