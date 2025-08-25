# src/handlers/logger_handlers.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import threading
from datetime import datetime, timezone
from telegram import Update, Message
from telegram.ext import ContextTypes

import src.config as CFG
from src.utils.parse import parse_kcc_packet, parse_fields
from src.utils.csv_log import append_csv
from src.get_userid_from_txn import resolve_user_all     # ⬅⬅ thay import
from src.utils.notify import send_via_ksnb

logger = logging.getLogger("logger-handlers")

# ==== Đường dẫn & cột CSV theo Step 1/2 ====
CSV_STEP1_PATH = getattr(CFG, "CSV_STEP1_PATH", CFG.CSV_PATH)
CSV_STEP2_PATH = getattr(CFG, "CSV_STEP2_PATH", CFG.CSV_PATH.with_name("onus_step2_enriched.csv"))
CSV_STEP1_COLUMNS = CFG.CSV_COLUMNS
CSV_STEP2_COLUMNS = getattr(
    CFG, "CSV_STEP2_COLUMNS",
    ["date","vndc_code","name_order","fullname","user_id_resolved","username","vip_level","document_number","pipeline_note"]
)

ONLY_CHAT_ID = getattr(CFG, "ONLY_CHAT_ID", None)
LISTEN_CHANNEL_ID = getattr(CFG, "LISTEN_CHANNEL_ID", None)
FILTERS = getattr(
    CFG,
    "FILTERS",
    type("F", (), {"enabled": True, "require_kcc_packet": False, "log_non_matching": True})(),
)
ENABLE_B2 = getattr(CFG, "ENABLE_B2", False)

# ---------- helpers ----------
def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _build_base_row(msg: Message, text: str, fields: dict) -> dict:
    chat = msg.chat
    user = msg.from_user
    sender_chat = getattr(msg, "sender_chat", None)
    via_bot = getattr(msg, "via_bot", None)
    date_iso = _iso_utc_now()
    try:
        if getattr(msg, "date", None):
            date_iso = datetime.fromtimestamp(msg.date.timestamp(), tz=timezone.utc).isoformat()
    except Exception:
        pass
    return {
        "date": date_iso,
        "chat_type": chat.type,
        "chat_id": chat.id,
        "chat_title": getattr(chat, "title", ""),
        "user_id": (user.id if user else ""),
        "user_name": (user.full_name if user else ""),
        "is_bot": (user.is_bot if user else False),
        "sender_chat_id": (sender_chat.id if sender_chat else ""),
        "sender_chat_title": (getattr(sender_chat, "title", getattr(sender_chat, "username", "")) if sender_chat else ""),
        "via_bot_id": (via_bot.id if via_bot else ""),
        "via_bot_username": (getattr(via_bot, "username", "") if via_bot else ""),
        "text": text,
        "vndc_code": fields.get("vndc_code", ""),
        "name_bank": fields.get("name_bank", ""),
        "name_order": fields.get("name_order", ""),
        "reply_to": (msg.reply_to_message.message_id if msg.reply_to_message else ""),
        "source": "sender_chat" if sender_chat else ("bot_user" if (user and user.is_bot) else ("via_bot" if via_bot else "human")),
    }

def _append_step1(row: dict) -> bool:
    try:
        path_written = append_csv(row, CSV_STEP1_PATH, columns=CSV_STEP1_COLUMNS)
        logger.info("STEP1 CSV appended -> %s", path_written)
        return True
    except PermissionError:
        warn = ("⚠️ CẢNH BÁO\n"
                "File CSV Step 1 đang bị mở/khóa (không ghi được).\n"
                f"chat_id={row.get('chat_id','')}, vndc_code={row.get('vndc_code','')}, name_order={row.get('name_order','')}")
        send_via_ksnb(warn)
        logger.error("PermissionError: cannot append Step 1 CSV (locked). Warning sent.")
        return False
    except Exception as e:
        warn = ("⚠️ CẢNH BÁO\n"
                f"Lỗi ghi CSV Step 1: {e!r}\n"
                f"chat_id={row.get('chat_id','')}, vndc_code={row.get('vndc_code','')}, name_order={row.get('name_order','')}")
        send_via_ksnb(warn)
        logger.exception("Append Step 1 CSV error: %s", e)
        return False

def _append_step2(row2: dict) -> bool:
    try:
        path_written = append_csv(row2, CSV_STEP2_PATH, columns=CSV_STEP2_COLUMNS)
        logger.info("STEP2 CSV appended -> %s", path_written)
        return True
    except PermissionError:
        warn = ("⚠️ CẢNH BÁO\n"
                "File CSV Step 2 (enriched) đang bị mở/khóa (không ghi được user_id).\n"
                f"vndc_code={row2.get('vndc_code','')}, fullname={row2.get('fullname','') or row2.get('name_order','')}")
        send_via_ksnb(warn)
        logger.error("PermissionError: cannot append Step 2 CSV (locked). Warning sent.")
        return False
    except Exception as e:
        warn = ("⚠️ CẢNH BÁO\n"
                f"Lỗi ghi CSV Step 2: {e!r}\n"
                f"vndc_code={row2.get('vndc_code','')}, fullname={row2.get('fullname','') or row2.get('name_order','')}")
        send_via_ksnb(warn)
        logger.exception("Append Step 2 CSV error: %s", e)
        return False

# ---------- Telegram command handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg:
        await msg.reply_text("Logger ready. Dùng /whereami để lấy chat_id.")

async def whereami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    info = f"chat_type={chat.type}, chat_id={chat.id}, title={getattr(chat,'title','')}"
    await update.effective_message.reply_text(info)
    logger.info("WHEREAMI: %s", info)

# ---------- Pipeline ----------
async def _process_pipeline(msg: Message):
    text = (msg.text or msg.caption or "").strip()
    pkt = parse_kcc_packet(text)

    # Non-KCC
    if not pkt:
        if not FILTERS.enabled or FILTERS.require_kcc_packet or not FILTERS.log_non_matching:
            return
        fields = parse_fields(text)
        row = _build_base_row(msg, text, fields)
        _append_step1(row)
        return

    # KCC matched
    fields = {
        "vndc_code": pkt["vndc_code"] if isinstance(pkt, dict) else pkt.vndc_code,
        "name_bank": (pkt.get("name_bank", "") if isinstance(pkt, dict) else getattr(pkt, "name_bank", "")) or "",
        "name_order": (pkt.get("name_order", "") if isinstance(pkt, dict) else getattr(pkt, "name_order", "")) or "",
    }
    print(f"[EVENT] KCC matched vndc_code={fields['vndc_code']} | name_order={fields['name_order']}")
    row = _build_base_row(msg, text, fields)

    # Step 1: phải ghi OK mới tiếp tục
    if not _append_step1(row):
        return

    # Step 2: resolve TXN + USER + ghi + notify
    if ENABLE_B2 and getattr(CFG, "B2_NOTIFY", {}).get("enabled", False):
        def _run_b2(vndc_code: str, name_order: str):
            try:
                fields_res = resolve_user_all(vndc_code)  # <-- lấy user_id, fullname, username, vip_level, document_number
                if "__error__" in fields_res:
                    user_id = ""
                    fullname = ""
                    username = ""
                    vip_level = ""
                    document_number = ""
                    note = f"resolve_error={fields_res['__error__']}"
                else:
                    user_id = (fields_res.get("user_id") or "")
                    fullname = (fields_res.get("fullname") or "").strip()
                    username = (fields_res.get("username") or "")
                    vip_level = (fields_res.get("vip_level") or "")
                    document_number = (fields_res.get("document_number") or "")
                    note = "ok" if user_id else "resolve_none"

                row2 = {
                    "date": _iso_utc_now(),
                    "vndc_code": vndc_code,
                    "name_order": name_order,
                    "fullname": fullname,
                    "user_id_resolved": str(user_id) if user_id else "",
                    "username": str(username) if username else "",
                    "vip_level": str(vip_level) if vip_level else "",
                    "document_number": str(document_number) if document_number else "",
                    "pipeline_note": note,
                }
                step2_ok = _append_step2(row2)

                if user_id and note == "ok" and step2_ok:
                    # Format mới theo yêu cầu:
                    # vndc_code, Mua VNDC KCC, chuyển khoản từ name_order cho fullname: username 2b
                    text_msg = CFG.B2_NOTIFY.get(
                        "template",
                        "{vndc_code}, Mua VNDC KCC, chuyển khoản từ {name_order} cho {fullname}: {username} 2b",
                    ).format(
                        vndc_code=vndc_code,
                        name_order=name_order,
                        fullname=(fullname or name_order),
                        username=(username or ""),
                        user_id=user_id,  # vẫn cho phép dùng trong template nếu cần
                    )
                    send_via_ksnb(text_msg)
                    logger.info("[B2] notify sent: %s", text_msg)
            except Exception as e:
                logger.exception("[B2] resolve/notify error: %s", e)
                warn = ("⚠️ CẢNH BÁO\n"
                        "Lỗi ngoài dự kiến trong Step 2 (resolve/notify).\n"
                        f"vndc_code={vndc_code}, name_order={name_order}")
                send_via_ksnb(warn)

        threading.Thread(
            target=_run_b2,
            args=(fields["vndc_code"], fields["name_order"]),
            daemon=True,
        ).start()

# ---------- Telegram update handlers ----------
async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not (msg.chat and msg.chat.type in ("group", "supergroup")):
        return
    if ONLY_CHAT_ID is not None and msg.chat_id != ONLY_CHAT_ID:
        return
    await _process_pipeline(msg)

async def on_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = update.channel_post
    if not post:
        return
    if LISTEN_CHANNEL_ID is not None and post.chat_id != LISTEN_CHANNEL_ID:
        logger.warning("Skip channel_post: LISTEN_CHANNEL_ID=%s, got=%s", LISTEN_CHANNEL_ID, post.chat_id)
        return
    logger.info(
        "CHANNEL_POST recv chat_id=%s title=%s text=%s",
        post.chat_id, getattr(post.chat, "title", ""), (post.text or post.caption or "")[:160]
    )
    await _process_pipeline(post)
