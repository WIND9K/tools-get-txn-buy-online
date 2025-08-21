# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timezone
from telegram import Update, Message
from telegram.ext import ContextTypes
from src.config import CSV_PATH, ONLY_CHAT_ID, LISTEN_CHANNEL_ID
from src.utils.csv_log import append_csv
from src.utils.parse import parse_fields

logger = logging.getLogger("logger-handlers")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg:
        await msg.reply_text("Logger ready. Use /whereami to get chat_id.")

async def whereami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    info = f"chat_type={chat.type}, chat_id={chat.id}, title={getattr(chat,'title','')}"
    await update.effective_message.reply_text(info)
    logger.info("WHEREAMI: %s", info)

def _log_from_message(msg: Message):
    chat = msg.chat

    # ONLY_CHAT_ID chỉ áp dụng cho group/supergroup (KHÔNG áp cho channel)
    if chat.type in ("group", "supergroup"):
        if chat.type in ("group", "supergroup") and ONLY_CHAT_ID is not None and chat.id != ONLY_CHAT_ID:
            return

    text = (msg.text or msg.caption or "").strip()
    if not text:
        return

    user = msg.from_user
    sender_chat = getattr(msg, "sender_chat", None)  # channel/anonymous admin
    via_bot = getattr(msg, "via_bot", None)

    # Chấp nhận 3 nguồn: bot user, sender_chat (channel), via inline bot
    from_bot_user    = bool(user and getattr(user, "is_bot", False))
    from_sender_chat = bool(sender_chat)   # quan trọng cho channel_post
    from_via_bot     = bool(via_bot)

    # Nếu muốn log cả user thường trong group, hãy bỏ điều kiện dưới.
    if chat.type in ("group", "supergroup") and not (from_bot_user or from_sender_chat or from_via_bot):
        return

    fields = parse_fields(text)

    # thời gian UTC ISO
    ts = msg.date.timestamp() if msg.date else None
    dt = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else datetime.now(timezone.utc).isoformat()

    row = {
        "date": dt,
        "chat_type": chat.type,
        "chat_id": chat.id,
        "chat_title": getattr(chat, "title", ""),

        # From user (nếu có)
        "user_id": (user.id if user else ""),
        "user_name": (user.full_name if user else ""),
        "is_bot": (user.is_bot if user else False),

        # Sender chat (channel/anonymous admin)
        "sender_chat_id": (sender_chat.id if sender_chat else ""),
        "sender_chat_title": (getattr(sender_chat, "title",
                                  getattr(sender_chat, "username", "")) if sender_chat else ""),

        # Via inline bot
        "via_bot_id": (via_bot.id if via_bot else ""),
        "via_bot_username": (getattr(via_bot, "username", "") if via_bot else ""),

        # Payload
        "text": text,
        "vndc_code": fields.get("vndc_code", ""),
        "name_bank": fields.get("name_bank", ""),
        "name_order": fields.get("name_order", ""),
        "reply_to": (msg.reply_to_message.message_id if msg.reply_to_message else ""),

        "source": ("bot_user" if from_bot_user else ("sender_chat" if from_sender_chat else ("via_bot" if from_via_bot else "human"))),
    }

    append_csv(row, CSV_PATH)
    logger.info("Logged %s: chat=%s user=%s sender_chat=%s",
                row["source"], row["chat_id"], row["user_id"], row["sender_chat_id"])

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not (msg.chat and msg.chat.type in ("group", "supergroup")):
        return
    _log_from_message(msg)

async def on_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = update.channel_post
    if not post:
        return

    # Lọc channel bằng LISTEN_CHANNEL_ID (nếu cấu hình), KHÔNG dùng ONLY_CHAT_ID ở đây
    if LISTEN_CHANNEL_ID is not None and post.chat_id != LISTEN_CHANNEL_ID:
        return

    # Debug dấu vết để chắc chắn handler đang nhận post
    logger.info("CHANNEL_POST recv chat_id=%s title=%s text=%s",
                post.chat_id, getattr(post.chat, "title", ""),
                (post.text or post.caption or "")[:160])

    _log_from_message(post)
