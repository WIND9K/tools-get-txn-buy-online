# scripts/seed_from_env.py
from pathlib import Path
import os
from dotenv import load_dotenv
from onusconfig.security.secure_manager import SecureManager

# Các khóa cần seed theo chuẩn Onus Report
REQUIRED_KEYS = [
    "DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME",
    "ACCESS_CLIENT_TOKEN",
]

def main():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        raise SystemExit(f"Không tìm thấy .env tại: {env_path}")
    load_dotenv(env_path)

    missing = [k for k in REQUIRED_KEYS if not os.getenv(k)]
    if missing:
        raise SystemExit(f"Thiếu khóa trong .env: {missing}")

    sm = SecureManager()
    for k in REQUIRED_KEYS:
        sm.set(k, os.getenv(k))

    # Kiểm tra lại 1 khóa quan trọng
    got = sm.get("ACCESS_CLIENT_TOKEN")
    print("Đã seed xong. ACCESS_CLIENT_TOKEN length:", len(got) if got else 0)

if __name__ == "__main__":
    main()
