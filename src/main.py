# src/main.py
# -*- coding: utf-8 -*-
import argparse, sys, logging
from src.bots.listener_main import main as run_listener

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
    args = p.parse_args()
    try:
        if args.stage in ("listen","b1"): return run_listener() or 0
        if args.stage == "b2": print("B2 paused"); return 0
        if args.stage == "b3": print("B3 not wired"); return 0
        print(f"Unknown stage: {args.stage}"); return 2
    except Exception:
        logging.exception("FATAL in main()"); return 1
    

# === Quiet third-party noisy logs ===
import logging

# Hạ mức log của httpx / httpcore / telegram.request
for noisy in ("httpx", "httpcore", "telegram.request"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

# (tùy chọn) nếu bạn đang dùng basicConfig với level=INFO,
# vẫn giữ INFO cho logger của bạn (vd. "listener-main", "logger-handlers"),
# nhưng các logger trên sẽ chỉ hiện WARNING trở lên.


if __name__ == "__main__":
    sys.exit(main())
