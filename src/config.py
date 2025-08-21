# src/config.py
# -*- coding: utf-8 -*-
from pathlib import Path

# ===== Paths =====
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ===== CSV =====
CSV_PATH = DATA_DIR / "telegram_group_log.csv"

# ===== Multi-bot tokens =====
# LƯU Ý: Đây là ví dụ theo yêu cầu của bạn; đừng commit token thật lên repo public.
BOT_TOKEN = {
    "BOT_GET_INFO": "7624727793:AAFOTrGlR5ugh_OHX1p5TWFvAJHCvPdSvJ4",  # Bot lắng nghe sự kiện
    "BOT_KSNB":     "8408874559:AAEPj_-PukhDE0CEOEgUzEATxxHTdVuOlMo",  # Bot gửi tin group/channel
    # "BOT_VUNP":     "8409793659:AAEcqLOi7nMgLibvpKn8fKS_op2LIG7khfo",  # Bot ADMIN khác
    # "BOT_TRUONG": "7004201972:AAHUVZBLZ2y5iNO26bJtRH-sJl8qt7qOSj4",
}

# ===== Targets for sending (BOT_KSNB sẽ dùng) =====
GROUP_CHAT_IDS = [
    -4851375268,  # ID group của bạn
]
CHANNEL_ID = -1002961730138  # ví dụ: -1002961730138 hoặc "@public_channel"

# (Legacy/compat – nếu code cũ còn dùng)
GROUP_CHAT_ID = None
ONLY_CHAT_ID  = None  # Chỉ áp dụng cho GROUP/SUPERGROUP, không áp cho channel

# ===== Listening filters (BOT_GET_INFO sẽ dùng) =====
# Chỉ lắng nghe 1 channel duy nhất (None = nghe tất cả channel mà bot là admin)
LISTEN_CHANNEL_ID = None  # ví dụ: -1002961730138


# ===== KCC pipeline =====
KCC_KEYWORD = "KCC"
KCC_CASE_SENSITIVE = False