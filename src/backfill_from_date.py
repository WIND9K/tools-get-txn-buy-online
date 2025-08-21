# src/backfill_from_date.py
# -*- coding: utf-8 -*-
"""
Backfill lịch sử chat từ START_DATE trong config.py đến hiện tại.
"""

import asyncio
import re
from datetime import timezone
from dateutil import parser as dtparser, tz
import pandas as pd
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto

from src import config
from src.get_userid_from_txn import get_user_id_from_vndc

# Regex tách trường
RE_VNDC  = re.compile(r"(VNDC\d+)")
RE_BANK  = re.compile(r"name_bank:([^\-\r\n]+)")
RE_ORDER = re.compile(r"name_order:([^\r\n]+)")

def parse_fields(text: str) -> dict:
    vndc = RE_VNDC.search(text or "")
    bank = RE_BANK.search(text or "")
    order = RE_ORDER.search(text or "")
    return {
        "vndc_code": vndc.group(1).strip() if vndc else "",
        "name_bank": bank.group(1).strip() if bank else "",
        "name_order": order.group(1).strip() if order else "",
    }

def append_rows(rows: list[dict]):
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    header = not config.CSV_PATH.exists()
    pd.DataFrame(rows).to_csv(
        config.CSV_PATH,
        mode="a",
        header=header,
        index=False,
        encoding="utf-8-sig"
    )

def safe_text(msg) -> str:
    text = msg.message or ""
    if not text and isinstance(msg.media, (MessageMediaPhoto, MessageMediaDocument)):
        text = msg.message or ""
    return (text or "").strip()

def parse_start_date(s: str):
    dt = dtparser.parse(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz.gettz("Asia/Ho_Chi_Minh"))
    return dt

async def run():
    start_dt = parse_start_date(config.START_DATE)
    client = TelegramClient("session_backfill", config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH)
    await client.start()

    # Cho phép truyền id số hoặc username
    entity = int(config.TARGET_CHAT) if config.TARGET_CHAT.lstrip("-").isdigit() else config.TARGET_CHAT
    chat = await client.get_entity(entity)

    print(f"> Backfill từ {start_dt.isoformat()} cho chat: {config.TARGET_CHAT}")
    rows_buffer, count = [], 0

    async for msg in client.iter_messages(chat, offset_date=None, reverse=True):
        msg_dt = msg.date.replace(tzinfo=timezone.utc)
        if msg_dt < start_dt.astimezone(timezone.utc):
            continue
        if msg.message is None and not msg.media:
            continue

        text = safe_text(msg)
        if not text:
            continue

        fields = parse_fields(text)
        user_id = ""
        if config.FETCH_USER_ID and fields["vndc_code"]:
            try:
                user_id = get_user_id_from_vndc(fields["vndc_code"]) or ""
            except Exception:
                user_id = ""

        rows_buffer.append({
            "date": msg_dt.isoformat(),
            "text": text,
            "vndc_code": fields["vndc_code"],
            "name_bank": fields["name_bank"],
            "name_order": fields["name_order"],
            "reply_to": (msg.reply_to.reply_to_msg_id if getattr(msg, "reply_to", None) else ""),
            "user_id": user_id,
        })

        if len(rows_buffer) >= 200:
            append_rows(rows_buffer)
            count += len(rows_buffer)
            print(f"...đã ghi {count} dòng")
            rows_buffer.clear()

    if rows_buffer:
        append_rows(rows_buffer)
        count += len(rows_buffer)
        print(f"> Hoàn tất. Tổng ghi: {count} dòng vào {config.CSV_PATH.resolve()}")

if __name__ == "__main__":
    asyncio.run(run())
