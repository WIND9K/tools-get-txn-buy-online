# src/config.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv


# =========================================================
# A) CẤU HÌNH CHUNG
# =========================================================
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Tokens/Secrets (đặt trong .env)
# - BOT_GET_INFO: token bot lắng nghe (Step 1)
# - BOT_KSNB:     token bot gửi notify (Step 2)
BOT_TOKEN = {
    "BOT_GET_INFO": os.getenv("BOT_GET_INFO", "").strip(),
    "BOT_KSNB": os.getenv("BOT_KSNB", "").strip(),
}

# Bật/Tắt toàn bộ Step 2 (resolve + notify)
ENABLE_B2: bool = True

# =========================================================
# B) STEP 1 — LẮNG NGHE / GHI CSV THÔ
# =========================================================
# Đích đến: nhóm nhận notify (B2) và channel (nếu dùng cho Step 1)
GROUP_CHAT_IDS: list[int] = [-1002799059129]   # nhóm nhận notify B2
CHANNEL_ID: int | str | None = None            # không gửi channel khác cho B1

# Giới hạn nguồn nghe (để None khi không khóa)
ONLY_CHAT_ID: int | None = None                # khóa group cụ thể nếu cần
LISTEN_CHANNEL_ID: int | None = None           # khóa channel cụ thể nếu cần

# CSV Step 1 (giữ alias CSV_PATH cho compatibility)
CSV_STEP1_PATH = DATA_DIR / "onus_step1.csv"
CSV_PATH = CSV_STEP1_PATH

# Hồ sơ cột cho B1
CSV_PROFILES = {
    "MINIMAL": [
        "date", "chat_type", "chat_id", "chat_title",
        "text", "vndc_code", "name_bank", "name_order",
    ],
    "DEFAULT": [
        "date", "chat_title",
        "sender_chat_id", "sender_chat_title",
        "text", "vndc_code", "name_bank", "name_order",
    ],
}
CSV_PROFILE = os.getenv("CSV_PROFILE", "DEFAULT")
CSV_COLUMNS = CSV_PROFILES.get(CSV_PROFILE, CSV_PROFILES["DEFAULT"])

# Lọc/ghi log B1
class FILTERS:
    enabled = True
    # True = chỉ ghi khi match KCC; False = ghi cả non-KCC để audit
    require_kcc_packet = True
    # Khi require_kcc_packet=False, cờ này quyết định có ghi non-KCC hay không
    log_non_matching = True

# (Tùy chọn) Template Step 1 nếu sau này muốn gửi channel/group từ B1
# Hiện mặc định B1 không gửi notify để tránh nhiễu
B1_NOTIFY_TEMPLATE = os.getenv(
    "B1_NOTIFY_TEMPLATE",
    ""  # để rỗng: không gửi từ Step 1
)

# =========================================================
# C) STEP 2A — API GIAO DỊCH → user_id, fullname, authorizationStatus
# =========================================================
# Endpoint chuẩn (theo yêu cầu): GET https://wallet.goonus.io/api/transactions?transactionNumber=...
API_BASE_URL: str = os.getenv("API_BASE_URL", "https://wallet.goonus.io").rstrip("/")
API_RESOLVE_PATH: str = os.getenv("API_RESOLVE_PATH", "/api/transactions")
API_METHOD: str = os.getenv("API_METHOD", "GET").upper()
API_QUERY_PARAM_NAME: str = os.getenv("API_QUERY_PARAM_NAME", "transactionNumber")

# Timeout/retry
API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "15"))
API_RETRIES: int = int(os.getenv("API_RETRIES", "3"))
API_RETRY_BACKOFF_SEC: float = float(os.getenv("API_RETRY_BACKOFF_SEC", "0.6"))

# Auth header + token
API_AUTH_HEADER_NAME: str = os.getenv("API_AUTH_HEADER_NAME", "Access-Client-Token")
ACCESS_CLIENT_TOKEN: str = os.getenv("ACCESS_CLIENT_TOKEN", "").strip()

# Mapping TXN payload (mảng root) -> các trường cần lấy
# Dotted path hỗ trợ nhiều fallback ngăn cách bằng '|'
RESOLVE_RESPONSE_PATHS = {
    # [ { ..., "to": { "user": { "id": "...", "display": "..." } } } ]
    "user_id": os.getenv("RESOLVE_PATH_USER_ID", "0.to.user.id|to.user.id"),
    "fullname": os.getenv("RESOLVE_PATH_FULLNAME", "0.to.user.display|to.user.display"),
    # Trạng thái ủy quyền của giao dịch (để audit/điều kiện mở rộng)
    "authorizationStatus": os.getenv("RESOLVE_PATH_AUTH_STATUS", "0.authorizationStatus|authorizationStatus"),
}



# =========================================================
# D) STEP 2B — API USER → username, vip_level, document_number
# =========================================================
# Endpoint: GET https://wallet.vndc.io/api/users?usersToInclude=<user_id>&...
USER_API_BASE_URL: str = os.getenv("USER_API_BASE_URL", "https://wallet.vndc.io").rstrip("/")
USER_API_PATH: str = os.getenv("USER_API_PATH", "/api/users")
USER_API_METHOD: str = os.getenv("USER_API_METHOD", "GET").upper()

# Tên param chứa danh sách user id (API hiện dùng usersToInclude)
USER_API_PARAM_USER_IDS: str = os.getenv("USER_API_PARAM_USER_IDS", "usersToInclude")

# Các tham số cố định khi gọi User API
USER_API_FIXED_PARAMS: dict = {
    "includeGroup": os.getenv("USER_API_INCLUDE_GROUP", "true"),
    "page": os.getenv("USER_API_PAGE", "0"),
    "pageSize": os.getenv("USER_API_PAGESIZE", "1000"),
    "fields": os.getenv("USER_API_FIELDS", "id,username,customValues.vip_level,customValues.document_number"),
    "statuses": os.getenv("USER_API_STATUSES", "active, blocked, disabled"),
}

# Auth (mặc định dùng chung token/header với TXN; có thể override riêng)
USER_API_AUTH_HEADER_NAME: str = os.getenv("USER_API_AUTH_HEADER_NAME", API_AUTH_HEADER_NAME)
USER_API_ACCESS_TOKEN: str = os.getenv("USER_API_ACCESS_TOKEN", ACCESS_CLIENT_TOKEN)

# Mapping USER payload (mảng root) -> các trường cần lấy
# [ { "id": "...", "username": "...", "customValues": { "vip_level": "...", "document_number": "..." } } ]
USER_RESPONSE_PATHS = {
    "username": os.getenv("USER_PATH_USERNAME", "0.username|username"),
    "vip_level": os.getenv("USER_PATH_VIP", "0.customValues.vip_level|customValues.vip_level"),
    "document_number": os.getenv("USER_PATH_DOC", "0.customValues.document_number|customValues.document_number"),
}



# =========================================================
# E) CSV STEP 2 — LƯU KẾT QUẢ ENRICHED
# =========================================================
CSV_STEP2_PATH = DATA_DIR / "onus_step2_enriched.csv"
CSV_STEP2_COLUMNS = [
    "date", "vndc_code", "name_order", "fullname",
    "user_id_resolved", "username", "vip_level", "document_number",
    "pipeline_note",
]



# =========================================================
# F) NOTIFY (B2) — TEMPLATE GỬI NHÓM/CHANNEL
# =========================================================
# Tin nhắn Step 2 theo format yêu cầu:
#   "{vndc_code}, Mua VNDC KCC, chuyển khoản từ {name_order} cho {fullname} username: {username}"
B2_NOTIFY = {
    "enabled": True,
    # ví dụ:
    # VNDC2630477368 - đã duyệt, Mua VNDC KCC, chuyển khoản từ A cho B username: 123456
    "template": os.getenv(
        "B2_NOTIFY_TEMPLATE",
        "{vndc_code} - {status_vi}, Mua VNDC KCC, chuyển khoản từ {name_bank} cho {fullname} username: {username}"
    ),
    "only_when": ["ok"],
}
