# Onus procesc user - get txn onus buy online


Bot Telegram lưu tin nhắn **bắt đầu bằng `KCC`** trong group vào CSV, kèm các trường đã tách: `vndc_code`, `name_bank`, `name_order`.


## 1) Chuẩn bị
- Cài Python 3.12+ (khuyến nghị 3.12 hoặc 3.13).
- Tạo bot qua @BotFather và **revoke** token cũ nếu đã lộ.
- @BotFather → `/setprivacy` → **Disable** để bot nhận tin nhắn thường trong group.
- Thêm bot vào group cần lấy dữ liệu.


## 2) Cài đặt
```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
# source .venv/bin/activate


pip install -r requirements.txt
cp .env.example .env # (Windows: copy .env.example .env)