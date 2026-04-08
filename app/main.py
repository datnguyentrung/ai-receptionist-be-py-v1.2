import asyncio
from contextlib import asynccontextmanager
import logging

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Đăng ký Telegram Webhook khi server khởi động
    if not settings.NGROK_URL:
        print("⚠️  NGROK_URL chưa được cấu hình — bỏ qua đăng ký Webhook.")
    else:
        webhook_url = f"{settings.NGROK_URL}{settings.API_V1}/telegram/webhook"
        set_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"

        max_retries = 3
        retry_delay = 5  # giây

        async with httpx.AsyncClient() as client:
            for attempt in range(1, max_retries + 1):
                try:
                    print(f"🔄 Đang đăng ký Webhook (Lần {attempt}/{max_retries})...")
                    resp = await client.get(set_url, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()

                    if data.get("ok"):
                        print(f"✅ Webhook đã đăng ký thành công: {webhook_url}")
                        break  # Thoát vòng lặp khi thành công
                    else:
                        print(f"❌ Telegram từ chối: {data}")
                        # Nếu Telegram từ chối (ví dụ sai URL), thường retry cũng không ích gì nên có thể break luôn hoặc đợi retry
                        break

                except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                    print(f"❌ Lỗi đăng ký Webhook (Lần {attempt}): {type(exc).__name__}")

                    if attempt < max_retries:
                        print(f"   → Thử lại sau {retry_delay} giây...")
                        await asyncio.sleep(retry_delay)
                    else:
                        print(f"‼️ Đã thử {max_retries} lần nhưng thất bại. Vui lòng kiểm tra NGROK hoặc Internet.")

    yield  # Server bắt đầu chạy tại đây

    # --- PHẦN ĐÓNG (SHUTDOWN) ---
    from app.services.telegram_service import telegram_client
    await telegram_client.aclose()
    print("🛑 Đã đóng kết nối Telegram Client.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1)


@app.get("/", tags=["Health"])
async def root():
    return {"message": "AI Receptionist API is running."}
