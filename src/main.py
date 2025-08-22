# src/main.py
# -*- coding: utf-8 -*-
import argparse
import sys
import logging

# B1 – listener
from src.bots.listener_main import main as run_listener

# === Console-only logging (không ghi file) ===
logger_root = logging.getLogger()
logger_root.setLevel(logging.INFO)
if not logger_root.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger_root.addHandler(ch)

def main() -> int:
    parser = argparse.ArgumentParser(description="Onus Process Txn - Orchestrator")
    parser.add_argument("--stage", choices=["listen", "b1", "b2", "b3"], default="listen")
    args = parser.parse_args()

    try:
        if args.stage in ("listen", "b1"):
            return run_listener() or 0
        elif args.stage == "b2":
            print("B2 is paused"); return 0
        elif args.stage == "b3":
            print("B3 is not wired"); return 0
        print(f"Unknown stage: {args.stage}"); return 2
    except Exception:
        logging.exception("FATAL in main()")
        return 1

if __name__ == "__main__":
    sys.exit(main())
