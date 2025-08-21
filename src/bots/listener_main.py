# -*- coding: utf-8 -*-
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from src.config import BOT_TOKEN
from src.handlers.logger_handlers import start, whereami, on_message, on_channel_post

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("listener-main")

def main():
    token = BOT_TOKEN.get("BOT_GET_INFO")
    if not token or token.startswith("PUT_"):
        raise SystemExit("BOT_TOKEN['BOT_GET_INFO'] is missing in config.py")

    # Xoá webhook để dùng polling
    try:
        import requests
        who = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10).json()
        if not who.get("ok"):
            raise SystemExit(f"[FATAL] Invalid BOT_GET_INFO token: {who}")
        logger.info("LISTENER identity: @%s (id=%s)",
                    who["result"].get("username", ""), who["result"].get("id", ""))

        requests.post(
            f"https://api.telegram.org/bot{token}/deleteWebhook",
            params={"drop_pending_updates": True},
            timeout=10,
        )
        logger.info("Deleted webhook & dropped pending updates.")
    except Exception as e:
        logger.warning("deleteWebhook/getMe issue (ignored): %s", e)

    logger.info("Starting listener...")
    app = ApplicationBuilder().token(token).build()

    # Lệnh tiện ích
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("whereami", whereami))

    # Lắng nghe group/supergroup
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, on_message))

    # Lắng nghe channel_post (bài đăng ở channel – kể cả do bot khác đăng)
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, on_channel_post))

    # Error handler
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.exception("Unhandled exception: %s", context.error)
    app.add_error_handler(error_handler)

    # Quan trọng: mở cả message & channel_post
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "channel_post"],
        timeout=60
    )

if __name__ == "__main__":
    main()
