# BAO CAO TIEN DO TUAN - AI RECEPTIONIST BACKEND
**Ky bao cao:** 09/03/2026 - 15/03/2026  
**Module:** Backend Python (AI Agent Service)  
**Vai tro:** AI/Machine Learning Engineer

---

## 1. XU LY AI & COMPUTER VISION

### Da thuc hien trong tuan
- Tich hop InsightFace (`buffalo_s`) chay CPU va khoi tao model 1 lan toan cuc trong `app/utils/insightface_utils.py`.
- Xay dung ham `get_face_embedding()` de trich xuat vector 512 chieu tu khuon mat lon nhat trong anh.
- Tich hop luu/so khop embedding voi PostgreSQL + `pgvector` trong `app/db/repositories/user_repo.py`.
- Hoan thanh luong TTS streaming bang Edge TTS trong `app/utils/audio_edge_tts.py`.
- Ket noi LLM Gemini de tao cau chao ngan trong `app/utils/generate_text.py`, co fallback khi loi.

### Su thay doi trong tuan
- Bo sung luong nhan dien khuon mat hoan chinh: anh upload -> trich embedding -> tim nguoi khop nhat theo cosine distance.
- Chuyen tu cach xu ly audio gom toan bo sang stream theo chunk, giup phat am thanh som hon.
- Them fallback cho LLM de dam bao van co cau chao khi API bi rong/loi.

### Tien trinh
- **Dau tuan:** Hoan thien utility AI (face embedding + text generation).
- **Giua tuan:** Noi luong TTS streaming vao API.
- **Cuoi tuan:** Chot luong end-to-end cho greeting (LLM -> TTS -> response stream).

---

## 2. TICH HOP BOT & LLM AGENT

### Da thuc hien trong tuan
- Tich hop Telegram Bot API trong `app/services/telegram_service.py` voi 2 ham chinh:
  - `send_checkin_alert(...)`
  - `send_welcome_message(...)`
- Tao webhook endpoint `POST /api/v1/telegram/webhook` trong `app/api/v1/telegram_api.py`.
- Cau hinh dang ky webhook luc khoi dong app trong `app/main.py` (lifespan + `NGROK_URL`).
- Tich hop LLM cho muc dich tao cau chao real-time trong luong TTS.

### Su thay doi trong tuan
- He thong co them kenh thong bao real-time qua Telegram khi co su kien check-in.
- Tuong tac bot co xu ly lenh `/start` va gui welcome message.
- LLM da duoc dua vao runtime flow de tao noi dung dong truoc khi phat loa.

### Tien trinh
- **Pha 1:** Tao service gui tin nhan Telegram.
- **Pha 2:** Mo endpoint webhook nhan update tu Telegram.
- **Pha 3:** Tu dong hoa dang ky webhook khi backend start.

> Luu y pham vi tuan nay: Chua ghi nhan implementation thuc te cho luong "LLM tong hop bao cao gui Gmail" trong code hien tai.

---

## 3. API/WORKER SERVICE

### Da thuc hien trong tuan
- Hoan thanh cac endpoint FastAPI phuc vu 3 luong chinh:
  - `POST /api/v1/users/check-in` (nhan dien khuon mat)
  - `POST /api/v1/users/{user_id}/face-embedding` (cap nhat embedding)
  - `GET /api/v1/tts/greeting` (stream audio chao)
  - `POST /api/v1/telegram/webhook` (nhan su kien bot)
- Dong bo cau truc layered: API -> Service -> Repository/Utils.
- Su dung SQLAlchemy async session (`app/db/session.py`) cho truy cap DB bat dong bo.

### Su thay doi trong tuan
- Tu cho chua co API dong bo, da hinh thanh bo endpoint hoat dong cho check-in, TTS va Telegram webhook.
- Nghiep vu AI duoc tach ro trong service va utility, giam logic trong controller.

### Tien trinh
- **Dau tuan:** Dung skeleton API va DB session.
- **Giua tuan:** Day du endpoint nhan dien va upload embedding.
- **Cuoi tuan:** Hoan tat endpoint TTS va Telegram webhook de chay thong suot.

---

## 4. BUG FIXES & TOI UU

### Da xu ly trong tuan
- Toi uu viec nap model khuon mat bang global singleton (`face_app`) de tranh nap lai moi request.
- Bo sung xu ly loi khi anh khong hop le/khong tim thay khuon mat trong `user_api.py` va `user_service.py`.
- Bo sung fallback noi dung khi Gemini tra ve rong hoac gap exception.
- Cai thien gui Telegram voi `AsyncClient` dung chung de giam chi phi tao ket noi lap lai.

### Tac dong thay doi
- Luong check-in on dinh hon khi gap input xau.
- Luong greeting it bi gian doan khi LLM loi.
- Thoi gian phat TTS nhanh hon nho stream theo chunk.

### Tien trinh
- **Fix 1:** On dinh hoa luong CV (xu ly mat mo/khong co mat).
- **Fix 2:** On dinh hoa luong LLM (fallback).
- **Fix 3:** Toi uu luong mang Telegram/TTS.

---

## 5. TOM TAT TIEN DO (1-2 CAU)

Trong tuan 09/03-15/03, backend Python da hoan thanh cac luong chinh dang chay duoc: nhan dien khuon mat check-in, tao cau chao + TTS streaming, va thong bao Telegram webhook. Thay doi lon nhat trong tuan la chuyen he thong tu muc utility rieng le sang luong API end-to-end co xu ly loi va toi uu runtime ro rang.
