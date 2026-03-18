import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TELEGRAM_API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

telegram_client = httpx.AsyncClient(
    base_url=f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}",
    timeout=httpx.Timeout(15.0)
)

async def send_checkin_alert(student_name: str, belt: str, status: str = "Thành công") -> None:
    """Gửi thông báo check-in của võ sinh qua Telegram."""
    text = (
        f"🥋 *[DOJO KIOSK] THÔNG BÁO CHECK-IN*\n"
        f"👤 Võ sinh: *{student_name}*\n"
        f"🎗 Đai: {belt}\n"
        f"✅ Trạng thái: {status}"
    )
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{_TELEGRAM_API}/sendMessage", json=payload)
            response.raise_for_status()
            logger.info("Đã gửi Telegram check-in cho %s", student_name)
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Lỗi gửi Telegram check-in (HTTP %s): %s",
                exc.response.status_code,
                exc.response.text,
            )
        except httpx.RequestError as exc:
            logger.error("Lỗi gửi Telegram check-in (network): %s", exc)


async def send_welcome_message(chat_id: int) -> None:
    payload = {"chat_id": chat_id, "text": "Chào mừng bạn đến với Taekwondo Văn Quán! 🥋"}
    try:
        # Sử dụng client dùng chung, không dùng 'async with' ở đây nữa
        response = await telegram_client.post("/sendMessage", json=payload)
        response.raise_for_status()
    except httpx.RequestError as exc:
        logger.error(f"Lỗi mạng: {exc}")