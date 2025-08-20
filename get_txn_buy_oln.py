# pip install "python-telegram-bot>=21.9,<23" pandas

import logging
import re
from pathlib import Path
import pandas as pd
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, filters
)

# ========== CONFIG ==========
BOT_TOKEN = "8310498174:AAGQ8k_FPMevH9bYwWypAJupU_BLwqe22Og"   # ⚠️ thay bằng token mới
CSV_PATH = Path(__file__).with_name("telegram_group_log.csv")
ONLY_CHAT_ID = None  # điền chat_id group cụ thể nếu cần
# ===========================

# Regex
RE_VNDC  = re.compile(r"(VNDC\d+)")
RE_BANK  = re.compile(r"name_bank:([^\-\r\n]+)")
RE_ORDER = re.compile(r"name_order:([^\r\n]+)")
RE_KCC   = re.compile(r"^\s*KCC", re.IGNORECASE)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("group-logger")
logging.getLogger("httpx").setLevel(logging.WARNING)

def parse_fields(text: str) -> dict:
    vndc = RE_VNDC.search(text)
    bank = RE_BANK.search(text)
    order = RE_ORDER.search(text)
    return {
        "vndc_code": vndc.group(1).strip() if vndc else "",
        "name_bank": bank.group(1).strip() if bank else "",
        "name_order": order.group(1).strip() if order else "",
    }

def append_row(row: dict):
    header = not CSV_PATH.exists()
    pd.DataFrame([row]).to_csv(CSV_PATH, mode="a", header=header, index=False, encoding="utf-8-sig")
    logger.info(">>> Đã ghi 1 dòng vào: %s", CSV_PATH.resolve())

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot logger sẵn sàng!")

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return
    if ONLY_CHAT_ID is not None and msg.chat_id != ONLY_CHAT_ID:
        return

    text = (msg.text or msg.caption or "").strip()
    if not text or not RE_KCC.search(text):
        return

    fields = parse_fields(text)
    row = {
        "date": msg.date.isoformat() if msg.date else "",
        "text": text,
        "vndc_code": fields["vndc_code"],
        "name_bank": fields["name_bank"],
        "name_order": fields["name_order"],
        "reply_to": (msg.reply_to_message.message_id if msg.reply_to_message else ""),
    }
    append_row(row)

# Main
if __name__ == "__main__":
    logger.info("CSV path: %s", CSV_PATH.resolve())
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, on_message))

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message"],
        timeout=60,
    )
