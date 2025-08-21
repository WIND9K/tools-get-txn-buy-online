# src/main.py
# -*- coding: utf-8 -*-
"""
Main entry for the bot runtime.

- Kết nối các handler đã triển khai trong get_txn_buy_oln.py:
  + /start, /whereami
  + on_message (group/supergroup)
  + on_channel_post (channel)
- Mở allowed_updates=["message","channel_post"] để nhận bài từ channel.
- Xoá webhook trước khi polling để tránh backlog.

Yêu cầu: python-telegram-bot >= 21.x
"""

import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from config import BOT_TOKEN

# Import các handler có sẵn trong get_txn_buy_oln.py
# (những hàm này phụ trách parse + ghi CSV)
from get_txn_buy_oln import (
    start,
    whereami,
    on_message,
    on_channel_post,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("main-bot")


def main():
    if not BOT_TOKEN or BOT_TOKEN in {"PUT_NEW_TOKEN_HERE", "PUT_REAL_BOT_TOKEN_HERE"}:
        raise SystemExit("BOT_TOKEN is not configured in src/config.py")

    # Xoá webhook để dùng polling (và drop backlog nếu có)
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook",
            params={"drop_pending_updates": True},
            timeout=10,
        )
        logger.info("Deleted webhook & dropped pending updates.")
    except Exception as e:
        logger.warning("deleteWebhook failed (ignored): %s", e)

    # Khởi tạo app
    logger.info("Starting bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Lệnh tiện ích
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("whereami", whereami))

    # Lắng nghe tin từ group/supergroup
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, on_message))

    # Lắng nghe bài đăng từ channel
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, on_channel_post))

    # Error handler (giữ bot không crash, log stacktrace)
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
