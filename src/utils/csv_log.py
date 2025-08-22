# src/utils/csv_log.py
# -*- coding: utf-8 -*-
import csv, time
from pathlib import Path
from datetime import datetime

def _ensure_header_compatible(csv_path: Path, columns: list[str]) -> Path:
    """
    Nếu file chưa tồn tại -> dùng csv_path.
    Nếu tồn tại nhưng header khác -> tạo file mới kèm dấu thời gian để không ghi sai cột.
    """
    if not csv_path.exists():
        return csv_path
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            first = f.readline().strip("\n\r")
            # so sánh thô: tên cột ngăn bởi dấu phẩy
            current = first.split(",")
            if [c.strip() for c in current] == [c.strip() for c in columns]:
                return csv_path
    except Exception:
        # nếu đọc lỗi, fallback mở file mới
        pass
    # tạo file mới với hậu tố thời gian
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_path = csv_path.with_name(f"{csv_path.stem}_{ts}{csv_path.suffix}")
    return new_path

def append_csv(row: dict, csv_path: Path, columns: list[str], retries: int = 3, delay: float = 0.6) -> Path:
    """
    Ghi 1 dòng CSV theo thứ tự cột 'columns'.
    - Nếu header file đang có không khớp columns -> tự tạo file mới với hậu tố thời gian.
    - Trả về path file thực sự đã ghi (hữu ích để log).
    """
    target_path = _ensure_header_compatible(Path(csv_path), columns)
    header_needed = not target_path.exists()

    # lọc/điền đủ cột theo cấu hình
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
    # nếu vẫn lỗi -> ném ra để caller log
    raise
