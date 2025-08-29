# src/bots/send_broadcast.py
# -*- coding: utf-8 -*-
"""
Gửi tin tới nhiều group + 1 channel bằng BOT_KSNB.
CLI:
  python -m src.bots.send_broadcast --text "Hello"
  python -m src.bots.send_broadcast --text "Hi" --targets "-4851375268,-1002961730138,@public_channel"
"""
import argparse, json, time, logging, requests, os
from typing import List, Optional, Sequence, Union
from datetime import datetime, timezone
from dotenv import load_dotenv, find_dotenv

# ⚠️ Import module config thay vì import cứng từng biến (để tránh ImportError khi thiếu)
from src import config as cfg
from src.utils.parse import parse_fields
from src.utils.csv_log import append_csv

# logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logging.basicConfig(level=logging.CRITICAL)  # chỉ in lỗi nghiêm trọng
logger = logging.getLogger("send-broadcast")

# Luôn nạp .env để có biến BOT_TOKEN__BOT_KSNB / TELEGRAM_BOT_TOKEN
load_dotenv(find_dotenv(usecwd=True))

# ===== Helpers lấy config an toàn =====
def _cfg(name, default=None):
    return getattr(cfg, name, default)

# Các giá trị config lấy an toàn (có default)
BOT_TOKEN = _cfg("BOT_TOKEN", {}) or {}
CSV_PATH  = _cfg("CSV_PATH", "logs/sent_broadcast.csv")

# ===== Targets helpers =====
def _coerce_targets(targets: Optional[Union[str, Sequence[Union[str,int]]]]) -> List[Union[str,int]]:
    if targets is None:
        return []
    if isinstance(targets, str):
        parts = [p.strip() for p in targets.split(",") if p.strip()]
        out: List[Union[str,int]] = []
        for p in parts:
            if p.startswith("@"):
                out.append(p)
            else:
                try:
                    out.append(int(p))
                except ValueError:
                    out.append(p)
        return out
    out2: List[Union[str,int]] = []
    for g in targets:
        if isinstance(g, int):
            out2.append(g)
        elif isinstance(g, str) and g.startswith("@"):
            out2.append(g)
        else:
            try:
                out2.append(int(g))
            except Exception:
                out2.append(str(g))
    return out2

def discover_default_targets() -> List[Union[str,int]]:
    """Ghép targets từ config, có gì dùng nấy (không đòi hỏi đủ hết)."""
    targets: List[Union[str,int]] = []
    group_ids  = _cfg("GROUP_CHAT_IDS", []) or []
    channel_id = _cfg("CHANNEL_ID", None)
    group_id   = _cfg("GROUP_CHAT_ID", None)   # có thể không tồn tại
    only_id    = _cfg("ONLY_CHAT_ID", None)    # có thể không tồn tại
    if group_ids:
        targets.extend(group_ids)
    if channel_id is not None:
        targets.append(channel_id)
    if group_id is not None:
        targets.append(group_id)
    if only_id is not None:
        targets.append(only_id)
    return targets

# ===== CSV logging =====
def _append_csv_from_send_result(resp: dict, text: str):
    """Ghi CSV dựa trên response sendMessage (khi bot tự gửi)."""
    if not (isinstance(resp, dict) and resp.get("ok")):
        return
    msg = resp.get("result", {}) or {}
    chat = msg.get("chat", {}) or {}
    from_user = msg.get("from", {}) or {}
    fields = parse_fields(text)

    # ✅ dùng UTC timezone-aware (thay cho utcfromtimestamp - deprecated)
    ts = msg.get("date", int(datetime.now().timestamp()))
    iso_ts = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    row = {
        "date": iso_ts,
        "chat_type": chat.get("type", ""),
        "chat_id": chat.get("id", ""),
        "chat_title": chat.get("title", ""),
        "user_id": from_user.get("id", ""),
        "user_name": from_user.get("first_name", ""),
        "is_bot": from_user.get("is_bot", False),
        "sender_chat_id": "",
        "sender_chat_title": "",
        "via_bot_id": "",
        "via_bot_username": "",
        "text": text,
        "vndc_code": fields.get("vndc_code", ""),
        "name_bank": fields.get("name_bank", ""),
        "name_order": fields.get("name_order", ""),
        "reply_to": "",
        "source": "self_channel_post" if chat.get("type") == "channel" else "self_group_post",
    }

    # ✅ append_csv của bạn yêu cầu 'columns' -> truyền vào để cố định schema
    columns = [
        "date",
        "chat_type",
        "chat_id",
        "chat_title",
        "user_id",
        "user_name",
        "is_bot",
        "sender_chat_id",
        "sender_chat_title",
        "via_bot_id",
        "via_bot_username",
        "text",
        "vndc_code",
        "name_bank",
        "name_order",
        "reply_to",
        "source",
    ]
    append_csv(row, CSV_PATH, columns)


# ===== Telegram send =====
def tg_send_message(token: str, chat_id: Union[str,int], text: str, **kwargs) -> dict:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    payload.update({k: v for k, v in kwargs.items() if v is not None})
    r = requests.post(url, json=payload, timeout=30)
    try:
        return r.json()
    except Exception:
        return {"ok": False, "status_code": r.status_code, "text": r.text}

def _resolve_ksnb_token(explicit_token: Optional[str] = None) -> str:
    """
    Lấy token cho BOT_KSNB theo thứ tự ưu tiên:
      1) Tham số truyền vào (explicit_token)
      2) Biến môi trường TELEGRAM_BOT_TOKEN
      3) Biến môi trường BOT_TOKEN__BOT_KSNB
      4) cfg.BOT_TOKEN["BOT_KSNB"]
    """
    if explicit_token:
        return explicit_token
    env_token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN__BOT_KSNB")
    if env_token:
        return env_token
    cfg_token = BOT_TOKEN.get("BOT_KSNB") if isinstance(BOT_TOKEN, dict) else None
    if cfg_token:
        return cfg_token
    raise RuntimeError("Missing bot token for KSNB. Set TELEGRAM_BOT_TOKEN or BOT_TOKEN__BOT_KSNB in .env")

# ===== Public API =====
def broadcast_text(
    text: str,
    targets: Optional[Union[str, Sequence[Union[str,int]]]] = None,
    *,
    token: Optional[str] = None,
    parse_mode: Optional[str] = None,
    no_preview: bool = False,
    silent: bool = False,
    protect: bool = False,
    reply_to: Optional[int] = None,
    sleep: float = 0.4,
) -> None:
    """
    Hàm dùng lại được từ orchestrator (main.py) hoặc script khác.
    """
    token = _resolve_ksnb_token(token)
    tlist = _coerce_targets(targets) if targets is not None else discover_default_targets()
    if not tlist:
        raise SystemExit("No targets. Set GROUP_CHAT_IDS/CHANNEL_ID in config hoặc truyền targets.")
    for t in tlist:
        resp = tg_send_message(
            token=token,
            chat_id=t,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=not no_preview,
            disable_notification=silent,
            protect_content=protect,
            reply_to_message_id=reply_to,
        )
        if bool(resp.get("ok")):
            _append_csv_from_send_result(resp, text)
        time.sleep(sleep)

# ===== CLI =====
def main():
    parser = argparse.ArgumentParser(description="Broadcast message via BOT_KSNB")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--text")
    src.add_argument("--file")
    parser.add_argument("--targets", help="Comma-separated IDs or @usernames")
    parser.add_argument("--parse-mode", choices=["Markdown","MarkdownV2","HTML"])
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument("--silent", action="store_true")
    parser.add_argument("--protect", action="store_true")
    parser.add_argument("--reply-to", type=int)
    parser.add_argument("--sleep", type=float, default=0.4)
    parser.add_argument("--token", help="Override bot token (optional)")
    args = parser.parse_args()

    text = open(args.file, "r", encoding="utf-8").read() if args.file else (args.text or "")
    broadcast_text(
        text=text,
        targets=args.targets,
        token=args.token,
        parse_mode=args.parse_mode,
        no_preview=args.no_preview,
        silent=args.silent,
        protect=args.protect,
        reply_to=args.reply_to,
        sleep=args.sleep,
    )

if __name__ == "__main__":
    main()
