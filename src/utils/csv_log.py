# -*- coding: utf-8 -*-
import csv
from pathlib import Path

def append_csv(row: dict, csv_path: Path):
    # Đảm bảo schema ổn định: duy trì thứ tự cột theo lần đầu
    header = not csv_path.exists()
    with open(csv_path, mode="a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if header:
            writer.writeheader()
        writer.writerow(row)
