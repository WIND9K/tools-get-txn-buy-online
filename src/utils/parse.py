# src/utils/parse.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import Dict

# Ví dụ pattern: KCC-MSB-...-VNDC<digits>-name_bank:...-name_order:...
KCC_RE = re.compile(
    r"""
    \bKCC-[A-Z0-9]+-[A-Z0-9/-]+-VNDC(?P<vndc>\d{6,})     # vndc_code
    (?:-name_bank:(?P<bank>[^-\n\r]+))?                   # name_bank optional
    (?:-name_order:(?P<order>[^-\n\r]+))?                 # name_order optional
    """,
    re.IGNORECASE | re.VERBOSE,
)

def parse_kcc_packet(text: str) -> Dict[str, str] | None:
    if not text:
        return None
    m = KCC_RE.search(text)
    if not m:
        return None
    return {
        "vndc_code": f"VNDC{m.group('vndc')}".strip(),
        "name_bank": (m.group("bank") or "").strip(),
        "name_order": (m.group("order") or "").strip(),
    }

def parse_fields(text: str) -> Dict[str, str]:
    # Fallback cho non-KCC: vẫn trả dict để ghi CSV tối thiểu
    return {
        "vndc_code": "",
        "name_bank": "",
        "name_order": "",
    }
