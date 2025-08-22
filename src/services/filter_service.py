# src/services/filter_service.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from src.config import FILTERS

@dataclass(frozen=True)
class KccPacket:
    msb_acc: str
    trace: str
    vndc_code: str
    name_bank: str
    name_order: str

class FilterService:
    def __init__(self):
        self.p = FILTERS

    def match_kcc(self, text: str) -> Optional[KccPacket]:
        if not text or len(text) < self.p.min_text_len:
            return None
        m = self.p.re_kcc.search(text)
        if not m:
            return None
        bank_m  = self.p.re_bank.search(text)
        order_m = self.p.re_order.search(text)
        name_bank = (bank_m.group(1) or bank_m.group(2) or "").strip() if bank_m else ""
        name_order = (order_m.group(1).strip() if order_m else "")
        return KccPacket(
            msb_acc=m.group("msb_acc"),
            trace=m.group("trace"),
            vndc_code=f"VNDC{m.group('vndc')}",
            name_bank=name_bank,
            name_order=name_order,
        )

    def fallback_fields(self, text: str) -> dict:
        if not text:
            return {"vndc_code": "", "name_bank": "", "name_order": ""}
        v = self.p.re_vndc_fallback.search(text)
        b = self.p.re_bank.search(text)
        o = self.p.re_order.search(text)
        return {
            "vndc_code": (v.group(1).strip() if v else ""),
            "name_bank": ((b.group(1) or b.group(2)).strip() if b else ""),
            "name_order": (o.group(1).strip() if o else ""),
        }

# singleton nhẹ
FILTER_SVC = FilterService()
