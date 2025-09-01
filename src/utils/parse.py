# src/utils/parse.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import Dict

# Ví dụ pattern:
# KCC-MSB-.../FT...-VNDC<digits>-bank:...-bank_number:...-name_bank:...-name_order:...
KCC_REGEX = re.compile(
    r"(?P<prefix>KCC-[^-]+-[^/]+/[^\s-]+)-"
    r"(?P<vndc_code>VNDC\d+)"
    r"(?:-bank:(?P<bank>[A-Z0-9_]+))?"
    r"(?:-bank_number:(?P<bank_number>\d+))?"
    r"(?:-name_bank:(?P<name_bank>[A-Z0-9_]+))?"
    r"(?:-name_order:(?P<name_order>[^-\n\r]+))?",
    re.IGNORECASE
)

def parse_kcc_packet(text: str) -> dict | None:
    m = KCC_REGEX.search(text or "")
    if not m:
        return None
    g = m.groupdict()
    return {
        "vndc_code": (g.get("vndc_code") or "").strip(),
        "bank": (g.get("bank") or "").strip(),
        "bank_number": (g.get("bank_number") or "").strip(),
        "name_bank": (g.get("name_bank") or "").strip(),
        "name_order": (g.get("name_order") or "").strip(),
    }

def parse_fields(text: str) -> Dict[str, str]:
    # Fallback cho non-KCC: vẫn trả dict để ghi CSV tối thiểu
    return {
        "vndc_code": "",
        "name_bank": "",
        "name_order": "",
    }
