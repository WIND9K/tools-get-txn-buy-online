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
    "BOT_KSNB": os.getenv("BOT_KSNB", "").strip(),   # bật dùng cho B2 (notify)
}

# ===== Targets (B1 không gửi, chỉ lắng nghe) =====
GROUP_CHAT_IDS: list[int] = [-1002799059129]   # group nhận notify B2 theo yêu cầu
CHANNEL_ID: int | str | None = None           # không gửi kênh khác

# Chỉ lắng nghe 1 group/channel cụ thể (None = không khóa)
ONLY_CHAT_ID: int | None = None
LISTEN_CHANNEL_ID: int | None = None

# ===== CSV (gộp & đúng thứ tự) =====
CSV_PATH = DATA_DIR / "telegram_group_log.csv"
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
CSV_COLUMNS = CSV_PROFILES.get(CSV_PROFILE, CSV_PROFILES["DEFAULT"])  # fallback an toàn

# ===== Feature flags =====
ENABLE_B2: bool = True
B2_NOTIFY = {
    "enabled": True,
    "template": "B2 | vndc_code: {vndc_code} | user_id: {user_id} | name_order: {name_order}",
    "only_when": ["ok"],  # chỉ gửi khi resolve thành công
}

# ===== Filters cho B1 =====
class FILTERS:
    enabled = True
    require_kcc_packet = False     # False: non-KCC vẫn ghi (hữu ích khi debug/onboard)
    log_non_matching = True
