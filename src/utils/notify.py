# src/utils/notify.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import logging, time, requests
from typing import Any, Dict, List, Tuple
from src.config import BOT_TOKEN, GROUP_CHAT_IDS, CHANNEL_ID

logger = logging.getLogger("notify")

def _send_one(token: str, chat_id: int | str, text: str, retries: int = 2) -> Tuple[bool, str]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=15)
            ok = r.ok and r.json().get("ok") is True
            if ok:
                return True, "ok"
            try:
                j = r.json()
                desc = j.get("description") or r.text
                err_code = j.get("error_code")
            except Exception:
                desc, err_code = r.text, r.status_code

            if err_code == 429 and attempt < retries:
                retry_after = j.get("parameters", {}).get("retry_after", 2)
                time.sleep(int(retry_after))
                continue
            return False, f"{err_code}: {desc}"
        except Exception as e:
            if attempt < retries:
                time.sleep(1.0)
                continue
            return False, f"exception: {e!r}"
    return False, "unknown"

def send_via_ksnb(text: str) -> Dict[str, Any]:
    """
    Gửi text tới tất cả GROUP_CHAT_IDS và (nếu có) CHANNEL_ID bằng BOT_KSNB.
    Trả dict kết quả theo từng đích.
    """
    token = BOT_TOKEN.get("BOT_KSNB") or ""
    if not token:
        logger.error("BOT_KSNB token missing")
        return {"error": "missing_token"}

    targets: List[int | str] = []
    targets.extend(GROUP_CHAT_IDS or [])
    if CHANNEL_ID:
        targets.append(CHANNEL_ID)

    results: Dict[str, Any] = {"sent": [], "failed": []}
    if not targets:
        logger.warning("No targets configured (GROUP_CHAT_IDS/CHANNEL_ID empty)")
        return results

    for chat in targets:
        ok, msg = _send_one(token, chat, text)
        key = str(chat)
        if ok:
            logger.info("KSNB sent -> %s", key)
            results["sent"].append(key)
        else:
            logger.error("KSNB send FAIL -> %s | %s", key, msg)
            results["failed"].append({"chat": key, "error": msg})
    return results
