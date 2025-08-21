# -*- coding: utf-8 -*-
import logging
import re
import csv
from pathlib import Path
from datetime import datetime
from telegram import Update, Message
from config import *
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, filters
)

# Regex cho các trường cần lấy
RE_VNDC  = re.compile(r"(VNDC\d+)")
RE_BANK  = re.compile(r"name_bank:([^\-\r\n]+)")
RE_ORDER = re.compile(r"name_order:([^\r\n]+)")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("group-logger")
logging.getLogger("httpx").setLevel(logging.WARNING)

# CSV paths
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = DATA_DIR / "telegram_group_log.csv"

def parse_fields(text: str) -> dict:
    txt = text or ""
    vndc = RE_VNDC.search(txt)
    bank = RE_BANK.search(txt)
    order = RE_ORDER.search(txt)

    return {
        "vndc_code": vndc.group(1).strip() if vndc else "",
        "name_bank": bank.group(1).strip() if bank else "",
        "name_order": order.group(1).strip() if order else "",
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Logger ready. Use /whereami to get chat_id."
    if update.message:
        await update.message.reply_text(text)
    elif update.channel_post:
        await update.channel_post.reply_text(text)

async def whereami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    info = f"chat_type={chat.type}, chat_id={chat.id}, title={getattr(chat, 'title', '')}"
    if update.message:
        await update.message.reply_text(info)
    elif update.channel_post:
        await update.channel_post.reply_text(info)
    logger.info("WHEREAMI: %s", info)

def _append_csv(row: dict):
    header = not CSV_PATH.exists()
    with open(CSV_PATH, mode="a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if header:
            writer.writeheader()
        writer.writerow(row)

def _log_from_message(update: Update, msg: Message):
    """Extract and log message from either group/supergroup or channel_post."""
    chat = msg.chat

    if ONLY_CHAT_ID is not None and getattr(chat, "id", None) != ONLY_CHAT_ID:
        return

    user = msg.from_user
    sender_chat = getattr(msg, "sender_chat", None)
    via_bot = getattr(msg, "via_bot", None)

    from_bot_user = bool(user and getattr(user, "is_bot", False))
    from_sender_chat = bool(sender_chat)
    from_via_bot = bool(via_bot)

    if not (from_bot_user or from_sender_chat or from_via_bot):
        return

    text = (msg.text or msg.caption or "").strip()
    if not text:
        return

    fields = parse_fields(text)

    row = {
        "date": (msg.date.isoformat() if msg.date else datetime.now().isoformat()),
        "chat_type": getattr(chat, "type", ""),
        "chat_id": getattr(chat, "id", ""),
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
        "source": ("bot_user" if from_bot_user else ("sender_chat" if from_sender_chat else "via_bot")),
    }

    _append_csv(row)
    logger.info("Logged %s message: user_id=%s sender_chat=%s via_bot=%s",
                row["source"], row["user_id"], row["sender_chat_id"], row["via_bot_id"])

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not (msg.chat and msg.chat.type in ("group", "supergroup")):
        return
    if ONLY_CHAT_ID is not None and msg.chat_id != ONLY_CHAT_ID:
        return

    text = (msg.text or msg.caption or "").strip()
    if not text:
        return

    fields = parse_fields(text)
    chat = msg.chat
    user = msg.from_user

    row = {
        "date": (msg.date.isoformat() if msg.date else datetime.now().isoformat()),
        "chat_type": getattr(chat, "type", ""),
        "chat_id": getattr(chat, "id", ""),
        "chat_title": getattr(chat, "title", ""),
        "user_id": (user.id if user else ""),
        "user_name": (user.full_name if user else ""),
        "is_bot": (user.is_bot if user else False),
        "text": text,
        "vndc_code": fields.get("vndc_code", ""),
        "name_bank": fields.get("name_bank", ""),
        "name_order": fields.get("name_order", ""),
        "reply_to": (msg.reply_to_message.message_id if msg.reply_to_message else ""),
        "source": "bot" if (user and user.is_bot) else "human",
    }

    _append_csv(row)
    logger.info("Logged message: user_id=%s user_name=%s is_bot=%s",
                row["user_id"], row["user_name"], row["is_bot"])

async def on_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = update.channel_post
    if not post:
        return
    try:
        LISTEN_CHANNEL_ID
    except NameError:
        LISTEN_CHANNEL_ID = None  # type: ignore
    if LISTEN_CHANNEL_ID is not None and post.chat_id != LISTEN_CHANNEL_ID:
        return
    _log_from_message(update, post)

def main():
    if not BOT_TOKEN or BOT_TOKEN in {"PUT_NEW_TOKEN_HERE", "PUT_REAL_BOT_TOKEN_HERE"}:
        raise SystemExit("BOT_TOKEN is not configured in src/config.py")

    try:
        import requests as _r
        _r.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook",
            params={"drop_pending_updates": True},
            timeout=10,
        )
        logging.getLogger("main-bot").info("Deleted webhook & dropped pending updates.")
    except Exception as e:
        logging.getLogger("main-bot").warning("deleteWebhook failed (ignored): %s", e)

    logger.info("Starting bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("whereami", whereami))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, on_message))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, on_channel_post))

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.exception("Unhandled exception: %s", context.error)
    app.add_error_handler(error_handler)

    app.run_polling(drop_pending_updates=True, allowed_updates=["message", "channel_post"], timeout=60)

if __name__ == "__main__":
    main()
