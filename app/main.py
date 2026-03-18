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

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(set_url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                if data.get("ok"):
                    print(f"✅ Webhook đã đăng ký: {webhook_url}")
                else:
                    print(f"❌ Telegram từ chối Webhook: {data}")
            except httpx.RequestError as exc:
                print(f"❌ Lỗi kết nối khi đăng ký Webhook ({type(exc).__name__}): {exc}")
                print(f"   → Kiểm tra lại NGROK_URL trong .env: {settings.NGROK_URL}")
            except httpx.HTTPStatusError as exc:
                print(f"❌ Lỗi HTTP khi đăng ký Webhook: {exc.response.status_code} - {exc.response.text}")

    yield

    from app.services.telegram_service import telegram_client
    await telegram_client.aclose()


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
