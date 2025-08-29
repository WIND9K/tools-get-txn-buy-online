# src/bots/listener_main.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import logging, asyncio, os              # ✅ thêm os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv, find_dotenv   # ✅ thêm dòng này

from src.config import BOT_TOKEN
from src.handlers.logger_handlers import start, whereami, on_message, on_channel_post

logger = logging.getLogger("listener-main")

# Tìm .env theo thư mục đang chạy; ưu tiên cwd để chạy "python -m src.main"
dotenv_path = find_dotenv(usecwd=True)
load_dotenv(dotenv_path=dotenv_path, override=False)



def _get_token():
    # Ưu tiên biến TELEGRAM_BOT_TOKEN; fallback sang key cũ
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN__BOT_GET_INFO")
    if not token:
        # Thêm thông tin debug để dễ dò lỗi
        raise RuntimeError(
            "BOT_TOKEN['BOT_GET_INFO'] is missing. "
            f"Checked .env at: {dotenv_path or '(not found)'}; "
            "please set TELEGRAM_BOT_TOKEN or BOT_TOKEN__BOT_GET_INFO."
        )
    return token

def _identity_banner(app: Application) -> None:
    me = asyncio.get_event_loop().run_until_complete(app.bot.get_me())
    logger.info("LISTENER identity: @%s (id=%s)", me.username, me.id)

def main() -> int:
    token = _get_token()
    app = Application.builder().token(token).build()

    # banner + reset webhook
    _identity_banner(app)
    asyncio.get_event_loop().run_until_complete(app.bot.delete_webhook(drop_pending_updates=True))
    logger.info("Deleted webhook & dropped pending updates.")
    logger.info("Starting listener...")

    # handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("whereami", whereami))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, on_message))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, on_channel_post))

    # run
    app.run_polling(allowed_updates=["message","channel_post"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
