# src/config.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os, re
from pathlib import Path
import os
from dotenv import load_dotenv

# load .env ở thư mục gốc project
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

# ===== Tokens (đa bot) =====
BOT_TOKEN = {
    "BOT_GET_INFO": os.getenv("BOT_GET_INFO", ""),  # cập nhật .env
    "BOT_KSNB":     os.getenv("BOT_KSNB", ""),
}

# ===== Paths =====
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = DATA_DIR / "telegram_group_log.csv"

# ===== Listener filters (optional) =====
# Chỉ lắng nghe một group cụ thể (áp cho group/supergroup). Để None nếu lắng nghe tất cả.
ONLY_CHAT_ID: int | None = None

# Chỉ lắng nghe một channel cụ thể (áp cho channel). Để None nếu lắng nghe tất cả.
LISTEN_CHANNEL_ID: int | None = None        

# ===== Targets =====
GROUP_CHAT_IDS: list[int] = [-4913588089]   # nhóm sẽ nhận tin từ BOT_KSNB
CHANNEL_ID: int | str | None = "-1002961730138"         # nếu cần gửi thêm vào channel thì điền ID hoặc @username


# ===== Filter policy (có thể đọc từ ENV/yaml nếu muốn) =====
@dataclass(frozen=True)
class FilterPolicy:
    enabled: bool
    require_kcc_packet: bool
    case_sensitive: bool
    log_non_matching: bool
    min_text_len: int
    regex_kcc: str
    regex_bank: str
    regex_order: str

    # compiled (runtime)
    re_kcc: re.Pattern
    re_bank: re.Pattern
    re_order: re.Pattern
    re_vndc_fallback: re.Pattern

def _compile_policy(p: FilterPolicy) -> FilterPolicy:
    flags = re.X
    if not p.case_sensitive:
        flags |= re.I
    object.__setattr__(p, "re_kcc", re.compile(p.regex_kcc, flags))
    object.__setattr__(p, "re_bank", re.compile(p.regex_bank, flags))
    object.__setattr__(p, "re_order", re.compile(p.regex_order, flags))
    object.__setattr__(p, "re_vndc_fallback", re.compile(r"(VNDC\d+)", flags))
    return p

# Cách bật/tắt/tinh chỉnh
# Chỉ xử lý gói KCC: FILTERS.require_kcc_packet = True (default).
# Muốn debug mọi tin (kể cả không KCC) ghi CSV:
# require_kcc_packet = False, log_non_matching = True.
# Đổi pattern: sửa regex_kcc, regex_bank, regex_order trong config.py → restart bot.

FILTERS = _compile_policy(FilterPolicy(
    enabled=True,
    require_kcc_packet=True, 
    case_sensitive=False,
    log_non_matching=False,
    min_text_len=10,
    regex_kcc=r"""
        \b
        KCC-
        (?P<msb_acc>\d{8,})-
        (?P<trace>[A-Z0-9/]+)-
        VNDC(?P<vndc>\d{6,})
        \b
    """,
    # name_bank tới “-name_order” hoặc hết dòng
    regex_bank=r"name_bank:([^- \r\n][^- \r\n].*?)\s*-(?=name_order:)|name_bank:([^\-\r\n]+)",
    regex_order=r"name_order:([^\r\n]+)",
    re_kcc=None, re_bank=None, re_order=None, re_vndc_fallback=None,  # will be set by _compile_policy
))

# ===== CSV column profiles =====
CSV_PROFILES = {
    "MINIMAL": [
        "date", "chat_type", "chat_id", "chat_title",
        "text", "vndc_code", "name_order",
    ],
    "DEFAULT": [
        "date", "chat_type", "chat_id", "chat_title",
        "user_id", "user_name", "is_bot",
        "sender_chat_id", "sender_chat_title",
        "via_bot_id", "via_bot_username",
        "text", "vndc_code", "name_bank", "name_order",
        "reply_to", "source",
        "user_id_resolved", "pipeline_note",
    ],
    "EXTENDED": [
        "date", 
        "is_bot",
        "sender_chat_id", "sender_chat_title",
        "via_bot_username",
        "text", "vndc_code", "name_bank", "name_order",
        "source",
        "user_id_resolved", "pipeline_note",
        # có thể bổ sung thêm bất cứ cột mới nào ở đây
    ],
}

# Chọn profile mặc định (đổi ở đây là xong)
CSV_PROFILE = "EXTENDED"

# Danh sách cột thực sự dùng để ghi CSV (đừng sửa tay biến này—sửa CSV_PROFILE ở trên)
CSV_COLUMNS = CSV_PROFILES[CSV_PROFILE]

# ===== B2 notify (nội dung gửi bằng BOT_KSNB) =====
B2_NOTIFY = {
    "enabled": False,  # bật/tắt gửi notify
    # có thể dùng {vndc_code}, {name_bank}, {name_order}, {user_id_resolved}, {pipeline_note}
    "template": "B2 | vndc_code: {vndc_code} | name_bank: {name_bank}",
    # [] = gửi mọi case; hoặc ["ok"] chỉ gửi khi resolve OK
    "only_when": []
}
