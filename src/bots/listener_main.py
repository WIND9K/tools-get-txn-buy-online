# src/bots/listener_main.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import logging, asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src.config import BOT_TOKEN
from src.handlers.logger_handlers import start, whereami, on_message, on_channel_post

logger = logging.getLogger("listener-main")

def _get_token() -> str:
    tok = BOT_TOKEN.get("BOT_GET_INFO", "")
    if not tok:
        raise RuntimeError("BOT_TOKEN['BOT_GET_INFO'] is missing (check .env)")
    return tok

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
