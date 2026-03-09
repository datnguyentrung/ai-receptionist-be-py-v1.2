from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import numpy as np
import cv2

from app.db.session import get_db
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


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

    # 3. Chuyển xuống Service xử lý
    user_service = UserService(db)
    try:
        await user_service.update_user_face_embedding(user_id, image_np)
        return {"status": "success", "message": "Cập nhật dữ liệu khuôn mặt thành công!"}
    except ValueError as e:
        # Bắt lỗi từ Service (ví dụ: Không tìm thấy mặt) và trả về HTTP 400
        raise HTTPException(status_code=400, detail=str(e))