import base64
import json

import httpx
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import numpy as np
import cv2
from starlette.responses import StreamingResponse
import os
from dotenv import load_dotenv

from app.schemas.student_attendance import StudentAttendanceResponse
from app.services.telegram_service import send_checkin_alert

load_dotenv()

from app.db.session import get_db
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.utils.audio_edge_tts import generate_audio_stream
from app.utils.generate_text import generate_receptionist_greeting_stream

router = APIRouter(prefix="/users", tags=["Users"])

headers = {
    "X-API-KEY": os.getenv("JWT_BASE64_SECRET", "default_api_key"),
    "Content-Type": "application/json"
}

@router.post("/check-in")
async def face_check_in(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    # 1. Khai báo biến trước để tránh NameError
    record_obj = None
    text_to_speech = ""

    contents = await file.read()
    parser = np.frombuffer(contents, np.uint8)
    image_np = cv2.imdecode(parser, cv2.IMREAD_COLOR)

    if image_np is None:
        raise HTTPException(status_code=400, detail="Ảnh không hợp lệ.")

    user_service = UserService(db)

    # 2. Nhận diện khuôn mặt
    try:
        user_info = await user_service.check_in_by_face(image_np)
        # Giả định user_info có field full_name, bạn check lại tên field nhé
        student_name = getattr(user_info.user_profile, 'full_name', 'Học viên')
    except Exception:
        raise HTTPException(status_code=400, detail="Không nhận diện được khuôn mặt.")

    # 3. Gọi Java service
    try:
        async with httpx.AsyncClient() as client:
            java_response = await client.post(
                "http://localhost:8080/api/v1/student-attendances/check-in",
                json={"studentId": str(user_info.user_info.user_id)},
                headers=headers,
                timeout=5.0
            )
    except httpx.ConnectTimeout:
        raise HTTPException(status_code=503, detail="Hệ thống Java đang bảo trì.")

    if java_response.status_code != 201:
        # Nếu Java báo 400 (đã điểm danh rồi) hoặc lỗi khác
        raise HTTPException(status_code=java_response.status_code, detail="Học viên đã điểm danh hoặc có lỗi.")

    java_data = java_response.json()

    # 4. PARSE DỮ LIỆU & SINH CÂU CHÀO (Phần quan trọng nhất)
    try:
        # Dùng model_validate để parse an toàn
        record_obj = StudentAttendanceResponse(**java_data)
        text_to_speech = await generate_receptionist_greeting_stream(record_obj)
    except Exception as e:
        # Nếu lỗi parse (do null) hoặc lỗi AI, hãy dùng câu chào mặc định
        print(f"⚠️ Lỗi logic AI/Parse: {e}")
        text_to_speech = f"Xin chào {student_name}, điểm danh thành công."
        # Lúc này record_obj có thể là None hoặc object chưa hoàn thiện

    # 5. XỬ LÝ ÂM THANH
    audio_base64 = ""
    try:
        audio_bytes = b""
        async for chunk in generate_audio_stream(text_to_speech):
            audio_bytes += chunk
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        print(f"❌ Lỗi sinh âm thanh: {e}")

    # 6. CHUẨN BỊ RESPONSE
    response_data = user_info.model_dump(by_alias=True)
    response_data["audio_base64"] = audio_base64

    # 7. GỬI TELEGRAM TRONG BACKGROUND
    # Chỉ gửi nếu parse thành công record_obj, hoặc gửi fallback data
    if record_obj:
        background_tasks.add_task(
            send_checkin_alert,
            record_obj,
            note=text_to_speech
        )

    return response_data

@router.post("/{user_id}/face-embedding")
async def upload_face_image(
        user_id: UUID,
        file: UploadFile = File(...),  # Nhận file từ Form-Data của FE
        db: AsyncSession = Depends(get_db)
):
    # 1. Đọc dữ liệu thô (bytes) từ file gửi lên
    contents = await file.read()

    # 2. Chuyển đổi bytes sang Numpy Array để OpenCV đọc được
    parser = np.frombuffer(contents, np.uint8)
    image_np = cv2.imdecode(parser, cv2.IMREAD_COLOR)

    if image_np is None:
        raise HTTPException(status_code=400, detail="File gửi lên không phải là định dạng ảnh hợp lệ.")

    # 3. Khởi tạo Service và gọi hàm cập nhật embedding
    user_service = UserService(db)

    try:
        await user_service.update_user_face_embedding(user_id, image_np)
        return {"status": "success", "message": "Cập nhật dữ liệu khuôn mặt thành công!"}
    except ValueError as e:
        # Bắt lỗi từ Service (ví dụ: Không tìm thấy mặt) và trả về HTTP 400
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}/face-embedding")
async def delete_face_embedding(
        user_id: UUID,
        db: AsyncSession = Depends(get_db)
):
    # Khởi tạo Service và gọi hàm xóa embedding
    user_service = UserService(db)

    result = await user_service.remove_user_face_embedding(user_id)

    if result == "not_found":
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin võ sinh trong hệ thống.")

    if result == "already_empty":
        # API delete idempotent: vẫn trả success nếu dữ liệu đã rỗng từ trước
        return {"status": "success", "message": "Người dùng chưa có dữ liệu khuôn mặt, không cần xóa."}

    return {"status": "success", "message": "Xóa dữ liệu khuôn mặt thành công!"}
