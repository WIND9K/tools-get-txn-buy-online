# src/config/access_token.py
import os
from dotenv import load_dotenv, find_dotenv

# luôn nạp .env để đảm bảo có biến môi trường
load_dotenv(find_dotenv(usecwd=True))

def get_access_client_token() -> str:
    token = os.getenv("ACCESS_CLIENT_TOKEN")
    if not token:
        raise RuntimeError(
            "ACCESS_CLIENT_TOKEN is missing. Điền token vào file .env (ACCESS_CLIENT_TOKEN=...)"
        )
    return token

def auth_headers() -> dict:
    return {"Access-Client-Token": get_access_client_token()}
