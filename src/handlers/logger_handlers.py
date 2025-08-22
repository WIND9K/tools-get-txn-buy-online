# src/handlers/logger_handlers.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import threading
from datetime import datetime, timezone
from telegram import Update, Message
from telegram.ext import ContextTypes

import src.config as CFG
from src.utils.parse import parse_kcc_packet, parse_fields
from src.utils.csv_log import append_csv

# Bước 2: resolve + notify
from src.stages.resolve import resolve_one
from src.utils.notify import send_via_ksnb

logger = logging.getLogger("logger-handlers")

# Config với giá trị mặc định an toàn
CSV_PATH = CFG.CSV_PATH
CSV_COLUMNS = CFG.CSV_COLUMNS
ONLY_CHAT_ID = getattr(CFG, "ONLY_CHAT_ID", None)
LISTEN_CHANNEL_ID = getattr(CFG, "LISTEN_CHANNEL_ID", None)
FILTERS = getattr(
    CFG,
    "FILTERS",
    type("F", (), {"enabled": True, "require_kcc_packet": False, "log_non_matching": True})(),
)
ENABLE_B2 = getattr(CFG, "ENABLE_B2", False)  # bật/tắt Bước 2 qua config

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg:
        await msg.reply_text("Logger ready. Use /whereami to get chat_id.")

async def whereami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    info = f"chat_type={chat.type}, chat_id={chat.id}, title={getattr(chat,'title','')}"
    await update.effective_message.reply_text(info)
    logger.info("WHEREAMI: %s", info)

def _iso_utc(dt) -> str:
    try:
        return datetime.fromtimestamp(dt.timestamp(), tz=timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()

def _build_base_row(msg: Message, text: str, fields: dict) -> dict:
    chat = msg.chat
    user = msg.from_user
    sender_chat = getattr(msg, "sender_chat", None)
    via_bot = getattr(msg, "via_bot", None)
    return {
        "date": _iso_utc(getattr(msg, "date", None)) if getattr(msg, "date", None) else datetime.now(timezone.utc).isoformat(),
        "chat_type": chat.type,
        "chat_id": chat.id,
        "chat_title": getattr(chat, "title", ""),
        "user_id": (user.id if user else ""),
        "user_name": (user.full_name if user else ""),
        "is_bot": (user.is_bot if user else False),
        "sender_chat_id": (sender_chat.id if sender_chat else ""),
        "sender_chat_title": (getattr(sender_chat, "title", getattr(sender_chat, "username", "")) if sender_chat else ""),
        "via_bot_id": (via_bot.id if via_bot else ""),
        "via_bot_username": (getattr(via_bot, "username", "") if via_bot else ""),
        "text": text,
        "vndc_code": fields.get("vndc_code", ""),
        "name_bank": fields.get("name_bank", ""),
        "name_order": fields.get("name_order", ""),
        "reply_to": (msg.reply_to_message.message_id if msg.reply_to_message else ""),
        "source": "sender_chat" if sender_chat else ("bot_user" if (user and user.is_bot) else ("via_bot" if via_bot else "human")),
    }

def _append(row: dict):
    path_written = append_csv(row, CSV_PATH, columns=CSV_COLUMNS)
    logger.info("CSV appended -> %s", path_written)

async def _process_pipeline(msg: Message):
    text = (msg.text or msg.caption or "").strip()
    pkt = parse_kcc_packet(text)

    # Non-KCC (Bước 1 giữ nguyên)
    if not pkt:
        if not FILTERS.enabled: return
        if FILTERS.require_kcc_packet: return
        if not FILTERS.log_non_matching: return
        fields = parse_fields(text)
        row = _build_base_row(msg, text, fields)
        _append(row)
        return

    # KCC matched
    fields = {
        "vndc_code": pkt["vndc_code"] if isinstance(pkt, dict) else pkt.vndc_code,
        "name_bank": (pkt.get("name_bank", "") if isinstance(pkt, dict) else getattr(pkt, "name_bank", "")) or "",
        "name_order": (pkt.get("name_order", "") if isinstance(pkt, dict) else getattr(pkt, "name_order", "")) or "",
    }
    print(f"[EVENT] KCC matched vndc_code={fields['vndc_code']} | name_order={fields['name_order']}")
    row = _build_base_row(msg, text, fields)
    _append(row)  # ✅ Bước 1: ghi CSV trước, không thay đổi logic cũ

    # ✅ Bước 2: resolve + notify (chỉ chạy sau khi đã append CSV; chạy nền để không block handler)
    if ENABLE_B2 and getattr(CFG, "B2_NOTIFY", {}).get("enabled", False):
        def _run_b2(vndc_code: str, name_order: str):
            try:
                user_id, note = resolve_one(vndc_code)   # -> (uid, "ok") hoặc ("", "resolve_none/resolve_error=...")
                if user_id and note == "ok":
                    text_msg = CFG.B2_NOTIFY.get(
                        "template",
                        "B2 | vndc_code: {vndc_code} | user_id: {user_id} | name_order: {name_order}",
                    ).format(vndc_code=vndc_code, user_id=user_id, name_order=name_order)
                    send_via_ksnb(text_msg)
                    logger.info("[B2] notify sent: %s", text_msg)
                else:
                    logger.info("[B2] resolve skip: vndc_code=%s note=%s", vndc_code, note)
            except Exception:
                logger.exception("[B2] resolve/notify error")

        threading.Thread(
            target=_run_b2,
            args=(fields["vndc_code"], fields["name_order"]),
            daemon=True,
        ).start()

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not (msg.chat and msg.chat.type in ("group", "supergroup")):
        return
    if ONLY_CHAT_ID is not None and msg.chat_id != ONLY_CHAT_ID:
        return
    await _process_pipeline(msg)

async def on_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = update.channel_post
    if not post: return
    if LISTEN_CHANNEL_ID is not None and post.chat_id != LISTEN_CHANNEL_ID:
        logger.warning("Skip channel_post: LISTEN_CHANNEL_ID=%s, got=%s", LISTEN_CHANNEL_ID, post.chat_id)
        return
    logger.info(
        "CHANNEL_POST recv chat_id=%s title=%s text=%s",
        post.chat_id, getattr(post.chat, "title", ""), (post.text or post.caption or "")[:160]
    )
    await _process_pipeline(post)
