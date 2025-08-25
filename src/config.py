# src/config.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# ===== Paths =====
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ===== Tokens (đọc từ .env) =====
BOT_TOKEN = {
    "BOT_GET_INFO": os.getenv("BOT_GET_INFO", "").strip(),
    "BOT_KSNB": os.getenv("BOT_KSNB", "").strip(),   # dùng cho B2 (notify)
}

# ===== Targets =====
GROUP_CHAT_IDS: list[int] = [-1002799059129]   # group nhận notify B2
CHANNEL_ID: int | str | None = None           # không gửi channel khác

# Chỉ lắng nghe 1 group/channel cụ thể (None = không khóa)
ONLY_CHAT_ID: int | None = None
LISTEN_CHANNEL_ID: int | None = None

# ===== CSV (Step 1 & Step 2) =====
CSV_STEP1_PATH = DATA_DIR / "onus_step1.csv"
CSV_STEP2_PATH = DATA_DIR / "onus_step2_enriched.csv"

# Alias cho code B1 cũ
CSV_PATH = CSV_STEP1_PATH

CSV_PROFILES = {
    "MINIMAL": [
        "date","chat_type","chat_id","chat_title",
        "text","vndc_code","name_bank","name_order",
    ],
    "DEFAULT": [
        "date","chat_title",
        "sender_chat_id","sender_chat_title",
        "text","vndc_code","name_bank","name_order",
    ],
}
CSV_PROFILE = os.getenv("CSV_PROFILE", "DEFAULT")
CSV_COLUMNS = CSV_PROFILES.get(CSV_PROFILE, CSV_PROFILES["DEFAULT"])  # B1 columns

# ===== CSV Step 2 columns (mở rộng) =====
CSV_STEP2_COLUMNS = [
    "date", "vndc_code", "name_order", "fullname",
    "user_id_resolved", "username", "vip_level", "document_number",
    "pipeline_note"
]

# ===== Feature flags =====
ENABLE_B2: bool = True

# ===== Notify: format mới (có thể override qua .env) =====
B2_NOTIFY = {
    "enabled": True,
    # ví dụ tin: VNDC2610..., Mua VNDC KCC, chuyển khoản từ Nguyen Van A cho Huynh...: 5622782729 2b
    "template": "{vndc_code}, Mua VNDC KCC, chuyển khoản từ {name_order} cho {fullname} username: {username}",
    "only_when": ["ok"],  # chỉ gửi khi resolve thành công
}

# ===== Filters cho B1 =====
class FILTERS:
    enabled = True
    require_kcc_packet = False
    log_non_matching = True

# ===== API (Bước 2A: resolve user_id từ transaction) =====
API_BASE_URL: str = os.getenv("API_BASE_URL", "https://wallet.goonus.io").rstrip("/")
API_RESOLVE_PATH: str = os.getenv("API_RESOLVE_PATH", "/api/transactions")
API_METHOD: str = os.getenv("API_METHOD", "GET").upper()
API_QUERY_PARAM_NAME: str = os.getenv("API_QUERY_PARAM_NAME", "transactionNumber")

API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "15"))
API_RETRIES: int = int(os.getenv("API_RETRIES", "3"))
API_RETRY_BACKOFF_SEC: float = float(os.getenv("API_RETRY_BACKOFF_SEC", "0.6"))

API_AUTH_HEADER_NAME: str = os.getenv("API_AUTH_HEADER_NAME", "Access-Client-Token")
ACCESS_CLIENT_TOKEN: str = os.getenv("ACCESS_CLIENT_TOKEN", "").strip()

# Mapping TXN payload -> user_id, fullname (API trả MẢNG ở root)
RESOLVE_RESPONSE_PATHS = {
    "user_id": os.getenv("RESOLVE_PATH_USER_ID", "0.to.user.id|to.user.id"),
    "fullname": os.getenv("RESOLVE_PATH_FULLNAME", "0.to.user.display|to.user.display"),
}
# :contentReference[oaicite:3]{index=3}

# ===== API (Bước 2B: lấy info user theo user_id) =====
USER_API_BASE_URL: str = os.getenv("USER_API_BASE_URL", "https://wallet.vndc.io").rstrip("/")
USER_API_PATH: str = os.getenv("USER_API_PATH", "/api/users")
USER_API_METHOD: str = os.getenv("USER_API_METHOD", "GET").upper()

USER_API_PARAM_USER_IDS: str = os.getenv("USER_API_PARAM_USER_IDS", "usersToInclude")

USER_API_FIXED_PARAMS: dict = {
    "includeGroup": os.getenv("USER_API_INCLUDE_GROUP", "true"),
    "page": os.getenv("USER_API_PAGE", "0"),
    "pageSize": os.getenv("USER_API_PAGESIZE", "1000"),
    "fields": os.getenv("USER_API_FIELDS", "id,username,customValues.vip_level,customValues.document_number"),
    "statuses": os.getenv("USER_API_STATUSES", "active, blocked, disabled"),
}

USER_API_AUTH_HEADER_NAME: str = os.getenv("USER_API_AUTH_HEADER_NAME", API_AUTH_HEADER_NAME)
USER_API_ACCESS_TOKEN: str = os.getenv("USER_API_ACCESS_TOKEN", ACCESS_CLIENT_TOKEN)

# Mapping USER payload (mảng root) -> username, vip_level, document_number
USER_RESPONSE_PATHS = {
    "username": os.getenv("USER_PATH_USERNAME", "0.username|username"),
    "vip_level": os.getenv("USER_PATH_VIP", "0.customValues.vip_level|customValues.vip_level"),
    "document_number": os.getenv("USER_PATH_DOC", "0.customValues.document_number|customValues.document_number"),
}
# :contentReference[oaicite:4]{index=4}
