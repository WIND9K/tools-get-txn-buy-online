import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.get_userid_from_txn import get_user_id_from_vndc

vndc = input("Nhập vndc_code (ví dụ VNDC2610593029): ").strip()
try:
    uid = get_user_id_from_vndc(vndc)
    print("user_id:", uid or "")
except Exception as e:
    print("Lỗi:", e)
