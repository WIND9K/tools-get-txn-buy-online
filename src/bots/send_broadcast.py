# src/bots/send_broadcast.py
# -*- coding: utf-8 -*-
"""
Gửi tin tới nhiều group + 1 channel bằng BOT_KSNB.
CLI:
  python -m bots.send_broadcast --text "Hello"
  python -m bots.send_broadcast --text "Hi" --targets "-4851375268,-1002961730138,@public_channel"
"""
import argparse, json, time, logging, requests
from typing import List, Optional, Sequence, Union
from datetime import datetime
from src.config import BOT_TOKEN, GROUP_CHAT_IDS, GROUP_CHAT_ID, CHANNEL_ID, ONLY_CHAT_ID, CSV_PATH
from src.utils.parse import parse_fields
from src.utils.csv_log import append_csv

# logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logging.basicConfig(level=logging.CRITICAL)  # chỉ in lỗi nghiêm trọng, các INFO sẽ im
logger = logging.getLogger("send-broadcast")

def _coerce_targets(targets: Optional[Union[str, Sequence[Union[str,int]]]]) -> List[Union[str,int]]:
    if targets is None:
        return []
    if isinstance(targets, str):
        parts = [p.strip() for p in targets.split(",") if p.strip()]
        out: List[Union[str,int]] = []
        for p in parts:
            if p.startswith("@"): out.append(p)
            else:
                try: out.append(int(p))
                except ValueError: out.append(p)
        return out
    out2: List[Union[str,int]] = []
    for g in targets:
        if isinstance(g,int): out2.append(g)
        elif isinstance(g,str) and g.startswith("@"): out2.append(g)
        else:
            try: out2.append(int(g))
            except: out2.append(str(g))
    return out2

def discover_default_targets() -> List[Union[str,int]]:
    targets: List[Union[str,int]] = []
    if GROUP_CHAT_IDS: targets.extend(GROUP_CHAT_IDS)
    if CHANNEL_ID is not None: targets.append(CHANNEL_ID)
    if GROUP_CHAT_ID is not None: targets.append(GROUP_CHAT_ID)
    if ONLY_CHAT_ID is not None: targets.append(ONLY_CHAT_ID)
    return targets

def _append_csv_from_send_result(resp: dict, text: str):
    """Ghi CSV dựa trên response sendMessage (khi bot tự gửi)."""
    if not (isinstance(resp, dict) and resp.get("ok")):
        return
    msg = resp.get("result", {}) or {}
    chat = msg.get("chat", {}) or {}
    from_user = msg.get("from", {}) or {}
    fields = parse_fields(text)
    row = {
        "date": datetime.utcfromtimestamp(msg.get("date", int(datetime.now().timestamp()))).isoformat(),
        "chat_type": chat.get("type",""),
        "chat_id": chat.get("id",""),
        "chat_title": chat.get("title",""),
        "user_id": from_user.get("id",""),
        "user_name": from_user.get("first_name",""),
        "is_bot": from_user.get("is_bot", False),
        "sender_chat_id": "", "sender_chat_title": "",
        "via_bot_id": "", "via_bot_username": "",
        "text": text,
        "vndc_code": fields.get("vndc_code",""),
        "name_bank": fields.get("name_bank",""),
        "name_order": fields.get("name_order",""),
        "reply_to": "",
        "source": "self_channel_post" if chat.get("type")=="channel" else "self_group_post",
    }
    append_csv(row, CSV_PATH)

def tg_send_message(token: str, chat_id: Union[str,int], text: str, **kwargs) -> dict:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    payload.update({k:v for k,v in kwargs.items() if v is not None})
    r = requests.post(url, json=payload, timeout=30)
    try:
        return r.json()
    except Exception:
        return {"ok": False, "status_code": r.status_code, "text": r.text}

def main():
    token = BOT_TOKEN.get("BOT_KSNB")
    if not token or token.startswith("PUT_"):
        raise SystemExit("BOT_TOKEN['BOT_KSNB'] is missing in config.py")

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
    args = parser.parse_args()

    text = open(args.file,"r",encoding="utf-8").read() if args.file else (args.text or "")
    targets = _coerce_targets(args.targets) if args.targets else discover_default_targets()
    if not targets:
        raise SystemExit("No targets. Set GROUP_CHAT_IDS/CHANNEL_ID in config or pass --targets.")

    for t in targets:
        label = "CHANNEL" if (isinstance(t,str) and t.startswith("@")) or (isinstance(t,int) and str(t).startswith("-100")) else "GROUP"
        resp = tg_send_message(
            token=token,
            chat_id=t,
            text=text,
            parse_mode=args.parse_mode,
            disable_web_page_preview=not args.no_preview,
            disable_notification=args.silent,
            protect_content=args.protect,
            reply_to_message_id=args.reply_to,
        )
        ok = bool(resp.get("ok"))
        # print(f"[{label}][{'OK' if ok else 'FAIL'}] sent to {t} -> {json.dumps(resp, ensure_ascii=False)[:500]}")
        if ok:
            _append_csv_from_send_result(resp, text)
        time.sleep(args.sleep)

if __name__ == "__main__":
    main()
