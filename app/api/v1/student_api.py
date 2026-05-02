import httpx
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import numpy as np
import cv2
import os
from dotenv import load_dotenv

from app.exceptions.app_exception import AppException
from app.exceptions.error_code import ErrorCode
from app.schemas.response import CheckInResponse, AudioSignal
from app.schemas.student_attendance import StudentAttendanceResponse

load_dotenv()

from app.db.session import get_db
from app.services.student_service import StudentService
router = APIRouter(prefix="/students", tags=["Students"])

headers = {
    "X-API-KEY": os.getenv("JWT_BASE64_SECRET", "default_api_key"),
    "Content-Type": "application/json"
}


@router.post("/check-in", response_model=CheckInResponse)
async def face_check_in(
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    # 1. Đọc và giải mã ảnh
    contents = await file.read()
    parser = np.frombuffer(contents, np.uint8)
    image_np = cv2.imdecode(parser, cv2.IMREAD_COLOR)

    if image_np is None:
        raise AppException(ErrorCode.INVALID_IMAGE)  # <-- DÙNG APP EXCEPTION

    student_service = StudentService(db)

    # 2. Nhận diện khuôn mặt
    try:
        user_info = await student_service.check_in_by_face(image_np)
    except ValueError as e:
        # Nhận diện fail thì trả về audio báo lỗi ngay cho FE
        return CheckInResponse(
            audio_signal=AudioSignal.FACE_NOT_RECOGNIZED,
            status=False,
            user=None
        )
    except Exception as e:
        raise AppException(ErrorCode.AI_SYSTEM_ERROR, detail_message=str(e))  # <-- DÙNG APP EXCEPTION

    # 3. Gọi sang BE Java để xử lý nghiệp vụ điểm danh
    try:
        async with httpx.AsyncClient() as client:
            java_response = await client.post(
                "http://localhost:8080/api/v1/student-attendances/check-in",
                json={"studentId": str(user_info.user_info.user_id)},
                headers=headers,
                timeout=5.0
            )
    except httpx.ConnectTimeout:
        raise AppException(ErrorCode.JAVA_TIMEOUT)  # <-- DÙNG APP EXCEPTION
    except Exception as e:
        raise AppException(ErrorCode.JAVA_SYSTEM_ERROR, detail_message=str(e))  # <-- DÙNG APP EXCEPTION

    # 4. PARSE DỮ LIỆU & SINH TÍN HIỆU AUDIO CHO FE
    status_code = java_response.status_code

    if status_code == 201:
        java_data = java_response.json()
        try:
            record_obj = StudentAttendanceResponse(**java_data)
            return CheckInResponse(
                audio_signal=AudioSignal.CHECKIN_SUCCESS,
                status=True,
                user=user_info,
                attendance_record=record_obj
            )
        except Exception:
            raise AppException(ErrorCode.JAVA_SYSTEM_ERROR, detail_message="Lỗi parse JSON")  # <-- DÙNG APP EXCEPTION

    # Nếu Java trả mã lỗi (409 đã fix ở bước trước, hoặc 404 không có ca)
    elif status_code == 409:
        return CheckInResponse(
            audio_signal=AudioSignal.ALREADY_CHECKED_IN,
            status=False,
            user=user_info
        )

    elif status_code == 404:
        return CheckInResponse(
            audio_signal=AudioSignal.NO_VALID_SESSION,
            status=False,
            user=user_info
        )

    else:
        # Nếu ra một mã lỗi lạ lùng nào đó từ Java (vd: 500)
        raise AppException(ErrorCode.UNCATEGORIZED_EXCEPTION, detail_message=f"Java trả về status: {status_code}")

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
    student_service = StudentService(db)

    try:
        await student_service.update_user_face_embedding(user_id, image_np)
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
    student_service = StudentService(db)

    result = await student_service.remove_user_face_embedding(user_id)

    if result == "not_found":
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin võ sinh trong hệ thống.")

    if result == "already_empty":
        # API delete idempotent: vẫn trả success nếu dữ liệu đã rỗng từ trước
        return {"status": "success", "message": "Người dùng chưa có dữ liệu khuôn mặt, không cần xóa."}

    return {"status": "success", "message": "Xóa dữ liệu khuôn mặt thành công!"}
