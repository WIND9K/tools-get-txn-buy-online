# src/main.py
# -*- coding: utf-8 -*-
import argparse, sys, logging, os
from src.bots.listener_main import main as run_listener
from src.bots.send_broadcast import broadcast_text

# console-only logging
root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    root.addHandler(ch)

def main() -> int:
    p = argparse.ArgumentParser(description="Onus Process Txn - Orchestrator")
    p.add_argument("--stage", choices=["listen","b1","b2","b3"], default="listen")

    # Tham số cho stage b2
    p.add_argument("--b2-text", help="Nội dung broadcast (ưu tiên nếu truyền)")
    p.add_argument("--b2-file", help="File chứa nội dung broadcast")
    p.add_argument("--b2-targets", help="Chuỗi target cách nhau bởi dấu phẩy (id hoặc @username)")
    p.add_argument("--b2-parse-mode", choices=["Markdown","MarkdownV2","HTML"])
    p.add_argument("--b2-no-preview", action="store_true")
    p.add_argument("--b2-silent", action="store_true")
    p.add_argument("--b2-protect", action="store_true")
    p.add_argument("--b2-reply-to", type=int)
    p.add_argument("--b2-sleep", type=float, default=0.4)
    p.add_argument("--b2-token", help="Override bot token (optional)")

    args = p.parse_args()
    try:
        if args.stage in ("listen", "b1"):
            return run_listener() or 0

        if args.stage == "b2":
            # Lấy nội dung broadcast
            text = args.b2_text
            if not text and args.b2_file:
                text = open(args.b2_file, "r", encoding="utf-8").read()
            if not text:
                text = os.getenv("B2_TEXT", "")

            if not text:
                print("B2: Thiếu nội dung. Truyền --b2-text hoặc --b2-file hoặc đặt biến môi trường B2_TEXT.")
                return 2

            broadcast_text(
                text=text,
                targets=args.b2_targets,
                token=args.b2_token,
                parse_mode=args.b2_parse_mode,
                no_preview=args.b2_no_preview,
                silent=args.b2_silent,
                protect=args.b2_protect,
                reply_to=args.b2_reply_to,
                sleep=args.b2_sleep,
            )
            return 0

        if args.stage == "b3":
            print("B3 not wired")
            return 0

        print(f"Unknown stage: {args.stage}")
        return 2
    except Exception:
        logging.exception("FATAL in main()")
        return 1

# === Quiet third-party noisy logs ===
import logging
for noisy in ("httpx", "httpcore", "telegram.request"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

if __name__ == "__main__":
    sys.exit(main())
