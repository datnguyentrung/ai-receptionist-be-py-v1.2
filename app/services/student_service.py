from typing import Literal

import numpy as np
from sqlalchemy import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.student_repo import StudentRepository
from app.schemas.user import UserResponse, UserInfo, UserProfile
from app.utils.insightface_utils import get_face_embedding


class StudentService:
    def __init__(self, session: AsyncSession):
        self.student_repository = StudentRepository(session)

    async def update_user_face_embedding(self, user_id: UUID, image_np: np.ndarray) -> bool:
        """
        Nhận mảng ảnh, trích xuất khuôn mặt và lưu vào Database.
        """
        # 1. Gọi AI để lấy vector 512 chiều
        embedding = get_face_embedding(image_np)

        if embedding is None:
            # Bắn lỗi nếu ảnh mờ, bị che mặt hoặc không có người
            raise ValueError("Không tìm thấy khuôn mặt trong ảnh, vui lòng thử ảnh khác.")

        # 2. Gọi Repository để lưu vector này xuống Database
        success = await self.student_repository.update_face_embedding(user_id, embedding)

        if not success:
            raise ValueError("Không tìm thấy thông tin võ sinh trong hệ thống.")

        return True

    async def check_in_by_face(self, image_np) -> UserResponse:
        """
        Nhận mảng ảnh, trích xuất khuôn mặt và so sánh với database để điểm danh.
        Trả về thông tin người dùng nếu tìm thấy, ngược lại trả về lỗi.
        """
        embedding = get_face_embedding(image_np)

        if embedding is None:
            raise ValueError("Không tìm thấy khuôn mặt trong ảnh, vui lòng thử ảnh khác.")

        user = await self.student_repository.find_nearest_user_by_embedding(embedding)

        if user is None:
            raise ValueError("Không tìm thấy thông tin võ sinh trong hệ thống.")

        # Chuyển đổi User model thành UserResponse schema để trả về cho FE
        user_response = UserResponse(
            user_info=UserInfo(
                user_id=str(user.user_id),
                role_id=user.role_code
            ),
            user_profile=UserProfile(
                birth_date=user.birth_date,
                is_active=user.status,
                name=user.full_name,
                phone=user.phone_number,
                belt=user.belt
            )
        )

        return user_response

    async def remove_user_face_embedding(self, user_id: UUID) -> Literal["deleted", "already_empty", "not_found"]:
        return await self.student_repository.remove_face_embedding(user_id)
