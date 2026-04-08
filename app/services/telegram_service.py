from datetime import datetime
import logging

import httpx
from app.enums.operation_enum import AttendanceStatus
from app.core.config import settings
from app.schemas.student_attendance import StudentAttendanceResponse

logger = logging.getLogger(__name__)

_TELEGRAM_API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

telegram_client = httpx.AsyncClient(
    base_url=f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}",
    timeout=httpx.Timeout(15.0)
)

from datetime import datetime


async def send_checkin_alert(studentAttendanceInfo: StudentAttendanceResponse, note: str) -> None:
    """Gửi thông báo check-in của võ sinh qua Telegram với đầy đủ thông tin chi tiết."""

    # 1. Trích xuất thông tin từ tuition_status
    student_code = "N/A"
    fee_status = "⚠️ Chưa có dữ liệu"
    current_month = "này"

    if studentAttendanceInfo.tuition_status:
        student_code = studentAttendanceInfo.tuition_status.student_code
        current_month = studentAttendanceInfo.tuition_status.current_month
        is_paid = studentAttendanceInfo.tuition_status.has_paid_current_month
        # Đổi chữ in hoa và icon đỏ/xanh để gây ấn tượng thị giác mạnh hơn
        fee_status = "🟢 ĐÃ ĐÓNG" if is_paid else "❌ CHƯA ĐÓNG"

    # 2. Xử lý định dạng thời gian check-in
    formatted_date = "N/A"
    formatted_time = "N/A"

    try:
        clean_time_str = studentAttendanceInfo.check_in_time.split('.')[0]
        dt_obj = datetime.fromisoformat(clean_time_str)
        formatted_time = dt_obj.strftime("%H:%M:%S")
        formatted_date = dt_obj.strftime("%d/%m/%Y")
    except Exception:
        pass  # Nếu lỗi parse, giữ nguyên giá trị mặc định

    # 3. Xử lý thông tin lịch học từ class_schedule_id
    schedule_id = studentAttendanceInfo.class_schedule_id
    session_label = "Tối" if schedule_id and schedule_id[0] == "P" else "Sáng"

    facility = schedule_id[1] if len(schedule_id) > 1 else "?"
    day_of_week = schedule_id[2] if len(schedule_id) > 2 else "?"
    shift = schedule_id[4] if len(schedule_id) > 4 else "?"

    month_str = f"{current_month:<2}"

    # 4. Main label (Đã sửa lỗi Markdown, dùng dấu gạch ngang '-' thay vì '_')
    if studentAttendanceInfo.attendance_status == AttendanceStatus.PRESENT:
        main_label = f"✅ [BỤT] CÓ MẶT ĐÚNG GIỜ - NGÀY {formatted_date}"
    else:
        main_label = f"⚠️ [BỤT] ĐIỂM DANH MUỘN - NGÀY {formatted_date}"

    text = (
        f"🥋 *{main_label}*\n\n"
        f"```\n"
        f"👤 Võ sinh     : {studentAttendanceInfo.student_name}\n"
        f"🆔 Mã học viên : {student_code}\n"
        f"💰 Học phí T{month_str} : {fee_status}\n"
        f"⏰ Thời gian   : {formatted_time}\n"
        f"```\n"
        f"🏫 Lớp: Cơ sở `{facility}` Thứ `{day_of_week}` Buổi `{session_label}` Ca `{shift}` (`{schedule_id}`)\n"
        f"-------------------------------\n"
        f"🤖 AI Lễ tân: _{note}_"
    )

    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        response = await telegram_client.post("/sendMessage", json=payload)
        response.raise_for_status()
        # ĐÃ SỬA LỖI Ở ĐÂY: Dùng studentAttendanceInfo.student_name thay vì student_name
        logger.info(f"Đã gửi Telegram check-in thành công cho {studentAttendanceInfo.student_name}")
    except httpx.HTTPStatusError as exc:
        logger.error(f"Lỗi Telegram (HTTP {exc.response.status_code}): {exc.response.text}")
    except httpx.RequestError as exc:
        logger.error(f"Lỗi kết nối Telegram (timeout): {exc}")


async def send_welcome_message(chat_id: int) -> None:
    payload = {"chat_id": chat_id, "text": "Chào mừng bạn đến với Taekwondo Văn Quán! 🥋"}
    try:
        # Sử dụng client dùng chung, không dùng 'async with' ở đây nữa
        response = await telegram_client.post("/sendMessage", json=payload)
        response.raise_for_status()
    except httpx.RequestError as exc:
        logger.error(f"Lỗi mạng: {exc}")