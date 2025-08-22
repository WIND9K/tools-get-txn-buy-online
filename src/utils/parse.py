# -*- coding: utf-8 -*-
import re

# Ví dụ mẫu:
# KCC-MSB-80000369982-ACQCH01/FT252339KLSN-VNDC2616316617-name_bank:...-name_order:...
RE_KCC = re.compile(
    r"""\b
        KCC-MSB-
        (?P<msb_acc>\d{8,})-
        (?P<trace>[A-Z0-9/]+)-
        VNDC(?P<vndc>\d{6,})
        \b
    """,
    re.I | re.X,
)

RE_VNDC  = re.compile(r"(VNDC\d+)", re.I)
# name_bank lấy tới dấu '-' kế tiếp (trước -name_order)
RE_BANK  = re.compile(r"name_bank:([^- \r\n][^- \r\n].*?)\s*-(?=name_order:)|name_bank:([^\-\r\n]+)", re.I)
RE_ORDER = re.compile(r"name_order:([^\r\n]+)", re.I)

def parse_kcc_packet(text: str) -> dict | None:
    """
    Khớp đúng khuôn 'KCC-MSB-...-VNDC......' và tách các trường chính.
    Trả None nếu không khớp.
    """
    if not text:
        return None
    m = RE_KCC.search(text)
    if not m:
        return None
    vndc_code = f"VNDC{m.group('vndc')}"
    # bank/order (nếu có)
    bank_m  = RE_BANK.search(text)
    order_m = RE_ORDER.search(text)
    return {
        "matched": True,
        "msb_acc": m.group("msb_acc"),
        "trace": m.group("trace"),
        "vndc_code": vndc_code,
        "name_bank": (bank_m.group(1) or bank_m.group(2)).strip() if bank_m else "",
        "name_order": (order_m.group(1)).strip() if order_m else "",
    }

def parse_fields(text: str) -> dict:
    """
    Backward‑compatible: nếu không phải gói KCC chuẩn thì vẫn tách VNDC/name_bank/name_order như cũ.
    """
    pkt = parse_kcc_packet(text)
    if pkt:
        return {
            "vndc_code": pkt["vndc_code"],
            "name_bank": pkt["name_bank"],
            "name_order": pkt["name_order"],
        }
    # Fallback cũ
    txt = text or ""
    vndc = RE_VNDC.search(txt)
    bank = RE_BANK.search(txt)
    order = RE_ORDER.search(txt)
    return {
        "vndc_code": vndc.group(1).strip() if vndc else "",
        "name_bank": (bank.group(1) if bank and bank.group(1) else (bank.group(2) if bank else "")).strip() if bank else "",
        "name_order": order.group(1).strip() if order else "",
    }
