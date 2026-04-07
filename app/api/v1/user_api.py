import base64

import httpx
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import numpy as np
import cv2
from starlette.responses import StreamingResponse
import os
from dotenv import load_dotenv

from app.schemas.student_attendance import StudentAttendanceResponse

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

    # 3. Khởi tạo Service và gọi hàm check-in
    user_service = UserService(db)

    # 4. Nhận diện khuôn mặt
    try:
        user_info = await user_service.check_in_by_face(image_np)
        # return user_info.model_dump(by_alias=True)  # Trả về JSON với camelCase
    except Exception as e:
        # Bắt lỗi từ Service (ví dụ: Không tìm thấy mặt hoặc không khớp) và trả về HTTP 400
        raise HTTPException(status_code=400, detail="Không nhận diện được khuôn mặt. Vui lòng thử lại!")

    # 5. Gọi Java service để điểm danh
    try:
        async with httpx.AsyncClient() as client:
            java_response = await client.post(
                "http://localhost:8080/api/v1/student-attendances/check-in",
                json={"studentId": str(user_info.user_info.user_id)},  # Gửi user_id dưới dạng string
                headers=headers,
                timeout=5.0  # Đặt timeout để tránh chờ quá lâu nếu Java service gặp sự cố
            )
    except httpx.ConnectTimeout:
        raise HTTPException(status_code=503,detail="Hệ thống điểm danh đang bảo trì.")

    if java_response.status_code != 201:
        raise HTTPException(status_code=java_response.status_code, detail="Lỗi từ hệ thống điểm danh.")

    java_data = java_response.json()

    print("Dữ liệu chuẩn bị parse vào Pydantic:", java_data)

    try:
        # 2. Ép kiểu dictionary sang Pydantic Model
        # Nếu class AttendanceRecord của bạn chưa cấu hình cho phép CamelCase,
        # bạn có thể cần thêm alias hoặc sửa lại java_data như dưới đây:
        record_obj = StudentAttendanceResponse(**java_data)

        # 3. Gọi hàm SINH CÂU CHÀO (Bỏ chữ await vì hàm này là def thường)
        text_to_speech = await generate_receptionist_greeting_stream(record_obj)

    except Exception as e:
        print(f"Lỗi khi xử lý AI Agent: {e}")
        # In ra chi tiết lỗi để biết là lỗi do sai lệch field hay lỗi Gemini
        import traceback
        traceback.print_exc()
        text_to_speech = f"Xin chào {user_info.user_profile.name}, điểm danh thành công."

    # return StreamingResponse(
    #     generate_audio_stream(text_to_speech),
    #     media_type="audio/mpeg"
    # )
    # 1. Hứng toàn bộ stream âm thanh thành dạng bytes
    audio_bytes = b""
    async for chunk in generate_audio_stream(text_to_speech):
        audio_bytes += chunk

    # 2. Mã hóa bytes âm thanh sang chuỗi Base64
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    # 3. Chuẩn bị JSON Response: Gộp chung thông tin user và file audio
    response_data = user_info.model_dump(by_alias=True)  # Dữ liệu user cũ
    response_data["audio_base64"] = audio_base64  # Kẹp thêm audio vào

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
