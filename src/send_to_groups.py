# send_to_groups.py
# -*- coding: utf-8 -*-
"""
Broadcast a message from your bot to one or more Telegram group chats.

Usage examples:
--------------
# 1) Use message from CLI and groups from config.py
python send_to_groups.py --text "Hello groups!"

# 2) Override target groups on CLI (comma-separated list: IDs or @usernames)
python send_to_groups.py --text "Hi" --groups "-1001234567890,@my_public_group"

# 3) Read message content from a text file
python send_to_groups.py --file message.txt
"""

import argparse
import json
import logging
import time
from typing import List, Optional, Sequence, Tuple, Union
import requests

# Lấy token & group config từ config.py
try:
    from config import BOT_TOKEN  # bắt buộc
except Exception as e:
    raise SystemExit("Missing BOT_TOKEN in config.py") from e

# Tuỳ chọn group config
try:
    from config import GROUP_CHAT_IDS  # danh sách group
except Exception:
    GROUP_CHAT_IDS = None

try:
    from config import GROUP_CHAT_ID  # 1 group
except Exception:
    GROUP_CHAT_ID = None
try:
    from config import CHANNEL_ID
except Exception:
    CHANNEL_ID = None
try:
    from config import ONLY_CHAT_ID  # legacy
except Exception:
    ONLY_CHAT_ID = None

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _coerce_groups(groups: Optional[Union[str, Sequence[Union[str, int]]]]) -> List[Union[str, int]]:
    """Chuyển chuỗi/sequence thành list các group id/@username"""
    if groups is None:
        return []
    if isinstance(groups, str):
        parts = [p.strip() for p in groups.split(",") if p.strip()]
        out: List[Union[str, int]] = []
        for p in parts:
            if p.startswith("@"):
                out.append(p)
            else:
                try:
                    out.append(int(p))
                except ValueError:
                    out.append(p)
        return out
    out2: List[Union[str, int]] = []
    for g in groups:
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


def discover_default_groups() -> List[Union[str, int]]:
    """Lấy group/channel từ config.py"""
    targets = []
    if GROUP_CHAT_IDS:
        targets.extend(GROUP_CHAT_IDS)
    if CHANNEL_ID is not None:
        targets.append(CHANNEL_ID)
    if GROUP_CHAT_ID is not None:
        targets.append(GROUP_CHAT_ID)
    if ONLY_CHAT_ID is not None:
        targets.append(ONLY_CHAT_ID)
    return targets


def tg_send_message(
    chat_id: Union[str, int],
    text: str,
    parse_mode: Optional[str] = None,
    disable_web_page_preview: Optional[bool] = True,
    disable_notification: Optional[bool] = False,
    protect_content: Optional[bool] = False,
    reply_to_message_id: Optional[int] = None,
) -> Tuple[bool, dict]:
    """Gửi 1 message. Tự xử lý rate limit 429"""
    url = API_BASE + "/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if disable_web_page_preview is not None:
        payload["disable_web_page_preview"] = disable_web_page_preview
    if disable_notification is not None:
        payload["disable_notification"] = disable_notification
    if protect_content is not None:
        payload["protect_content"] = protect_content
    if reply_to_message_id is not None:
        payload["reply_to_message_id"] = reply_to_message_id

    r = requests.post(url, json=payload, timeout=30)
    try:
        data = r.json()
    except Exception:
        data = {"ok": False, "status_code": r.status_code, "text": r.text}

    # handle rate limit
    if r.status_code == 429:
        retry_after = data.get("parameters", {}).get("retry_after") or data.get("retry_after")
        if retry_after:
            time.sleep(float(retry_after) + 0.5)
            r2 = requests.post(url, json=payload, timeout=30)
            try:
                data = r2.json()
            except Exception:
                data = {"ok": False, "status_code": r2.status_code, "text": r2.text}
            return bool(data.get("ok")), data

    return bool(data.get("ok")), data


def broadcast(
    text: str,
    groups: Optional[Sequence[Union[str, int]]] = None,
    parse_mode: Optional[str] = None,
    disable_web_page_preview: Optional[bool] = True,
    disable_notification: Optional[bool] = False,
    protect_content: Optional[bool] = False,
    reply_to_message_id: Optional[int] = None,
    sleep_between: float = 0.4,
) -> None:
    """Gửi tin nhắn tới nhiều group"""
    targets = _coerce_groups(groups) if groups is not None else discover_default_groups()
    if not targets:
        raise SystemExit("No target groups specified. Provide --groups or set GROUP_CHAT_IDS / GROUP_CHAT_ID in config.py")

    for gid in targets:
        label = "CHANNEL" if (isinstance(gid, str) and gid.startswith("@")) or (isinstance(gid, int) and str(gid).startswith("-100")) else "GROUP"
        ok, resp = tg_send_message(chat_id=gid, text=text, parse_mode=parse_mode,
                                disable_web_page_preview=disable_web_page_preview,
                                disable_notification=disable_notification,
                                protect_content=protect_content,
                                reply_to_message_id=reply_to_message_id)
        status = "OK" if ok else "FAIL"
        print(f"[{label}][{status}] sent to {gid} -> {json.dumps(resp, ensure_ascii=False)[:500]}")
        time.sleep(sleep_between)


def main():
    parser = argparse.ArgumentParser(description="Broadcast a message to Telegram group(s) using your bot token.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="Message text to send")
    src.add_argument("--file", help="Path to a UTF-8 text file containing the message")

    parser.add_argument("--groups", help="Comma-separated group IDs or @usernames. If omitted, uses config.py default")
    parser.add_argument("--parse-mode", choices=["Markdown", "MarkdownV2", "HTML"], default=None)
    parser.add_argument("--no-preview", action="store_true", help="Disable link preview")
    parser.add_argument("--silent", action="store_true", help="Send silently (no notification)")
    parser.add_argument("--protect", action="store_true", help="Protect content from forwarding/saving")
    parser.add_argument("--reply-to", type=int, default=None, help="Reply to a specific message id")
    parser.add_argument("--sleep", type=float, default=0.4, help="Seconds to sleep between sends")

    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.text or ""

    groups = _coerce_groups(args.groups) if args.groups else None

    broadcast(
        text=text,
        groups=groups,
        parse_mode=args.parse_mode,
        disable_web_page_preview=not args.no_preview,
        disable_notification=args.silent,
        protect_content=args.protect,
        reply_to_message_id=args.reply_to,
        sleep_between=args.sleep,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()
