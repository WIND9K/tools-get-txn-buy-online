# src/utils/csv_log.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import csv, time
from pathlib import Path
from datetime import datetime

def _ensure_header_compatible(csv_path: Path, columns: list[str]) -> tuple[Path, bool]:
    """
    Trả về (path để ghi, header_needed)
    - Nếu file chưa tồn tại -> header_needed=True.
    - Nếu đã tồn tại nhưng header khác -> tạo file mới kèm timestamp (tránh lệch cột).
    """
    p = Path(csv_path)
    if not p.exists():
        return p, True
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            header = f.readline().strip("\r\n")
            current = [c.strip() for c in header.split(",")] if header else []
            if current == [c.strip() for c in columns]:
                return p, False
    except Exception:
        pass
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    newp = p.with_name(f"{p.stem}_{ts}{p.suffix}")
    return newp, True

def append_csv(row: dict, csv_path: Path, columns: list[str], retries: int = 3, delay: float = 0.5) -> Path:
    target_path, header_needed = _ensure_header_compatible(csv_path, columns)
    row_out = {col: (row.get(col, "") if row.get(col, "") is not None else "") for col in columns}

    for _ in range(retries):
        try:
            with target_path.open("a", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=columns)
                if header_needed:
                    w.writeheader()
                    header_needed = False
                w.writerow(row_out)
            return target_path
        except PermissionError:
            time.sleep(delay)
    raise
