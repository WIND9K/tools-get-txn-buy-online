# -*- coding: utf-8 -*-
import re

RE_VNDC  = re.compile(r"(VNDC\d+)")
RE_BANK  = re.compile(r"name_bank:([^\-\r\n]+)")
RE_ORDER = re.compile(r"name_order:([^\r\n]+)")

def parse_fields(text: str) -> dict:
    txt = text or ""
    vndc = RE_VNDC.search(txt)
    bank = RE_BANK.search(txt)
    order = RE_ORDER.search(txt)
    return {
        "vndc_code": vndc.group(1).strip() if vndc else "",
        "name_bank": bank.group(1).strip() if bank else "",
        "name_order": order.group(1).strip() if order else "",
    }
