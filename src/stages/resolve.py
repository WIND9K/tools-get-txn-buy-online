# src/stages/resolve.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import csv, time, logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict

from src.config import BASE_DIR, CSV_PATH  # CSV_PATH: data/telegram_group_log.csv
from src.get_userid_from_txn import get_user_id_from_vndc

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now().strftime("%Y%m%d")
RESOLVE_LOG = LOGS_DIR / f"resolve_{STAMP}.log"

logger = logging.getLogger("resolve-stage")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler(RESOLVE_LOG, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

def _iso_now_utc() -> str:
    return datetime.now(tz=timezone.utc).isoformat()

def _read_csv(path: Path) -> List[Dict[str,str]]:
    if not path.exists():
        logger.warning("Input CSV not found: %s", path)
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rdr = csv.DictReader(f)
        return list(rdr)

def _write_csv(rows: List[Dict[str,str]], out_path: Path):
    if not rows:
        with out_path.open("w", encoding="utf-8-sig", newline="") as f:
            csv.writer(f).writerow(["date","chat_type","chat_id","chat_title",
                                    "user_id","user_name","is_bot","sender_chat_id",
                                    "sender_chat_title","via_bot_id","via_bot_username",
                                    "text","vndc_code","name_bank","name_order",
                                    "reply_to","source","user_id_resolved","pipeline_note"])
        return
    cols = list(rows[0].keys())
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

def _needs_resolve(row: Dict[str,str]) -> bool:
    vndc = (row.get("vndc_code") or "").strip()
    if not vndc:
        return False
    uid = (row.get("user_id_resolved") or "").strip()
    if uid:
        return False
    # cho phép re-try nếu trước đó lỗi/none
    note = (row.get("pipeline_note") or "").lower()
    return note in ("", "resolve_none") or note.startswith("resolve_error")

def main() -> int:
    logger.info("B2 resolve started. Input: %s", CSV_PATH)
    rows = _read_csv(CSV_PATH)
    if not rows:
        logger.info("No rows. Exit.")
        return 0

    updated: List[Dict[str,str]] = []
    todo = 0
    ok = 0

    for row in rows:
        # bảo đảm 2 cột có tồn tại
        row.setdefault("user_id_resolved", "")
        row.setdefault("pipeline_note", "")
        if _needs_resolve(row):
            todo += 1
            vndc_code = (row.get("vndc_code") or "").strip()
            try:
                user_id = get_user_id_from_vndc(vndc_code)
                if user_id:
                    row["user_id_resolved"] = str(user_id)
                    row["pipeline_note"] = "ok"
                    ok += 1
                    print(f"[B2] vndc_code={vndc_code} -> user_id={user_id}")
                    logger.info("Resolved: %s -> %s", vndc_code, user_id)
                else:
                    row["pipeline_note"] = "resolve_none"
                    logger.info("Resolve none: %s", vndc_code)
            except Exception as e:
                row["pipeline_note"] = f"resolve_error={e!r}"
                logger.exception("Resolve error for %s", vndc_code)
                time.sleep(0.2)  # nhẹ tay với API
        updated.append(row)

    # Ghi RA FILE MỚI (an toàn với Windows đang mở file gốc)
    out_path = CSV_PATH.with_name("telegram_group_log_enriched.csv")
    _write_csv(updated, out_path)

    logger.info("B2 done. need=%s, resolved=%s. Output: %s", todo, ok, out_path)
    print(f"[B2] done. need={todo}, resolved={ok} -> {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

# src/stages/resolve.py
def resolve_one(vndc_code: str) -> tuple[str, str]:
    """
    Resolve vndc_code -> user_id.
    Return (user_id, pipeline_note).
    """
    if not vndc_code:
        return "", "no_vndc_code"
    try:
        user_id = get_user_id_from_vndc(vndc_code)
        if user_id:
            return str(user_id), "ok"
        return "", "resolve_none"
    except Exception as e:
        return "", f"resolve_error={e!r}"
