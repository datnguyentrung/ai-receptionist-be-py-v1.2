from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import Literal
from uuid import UUID
from app.models.user import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: UUID) -> User:
        result = await self.session.execute(select(User).where(User.user_id == user_id))
        return result.scalars().first()

    async def get_user_by_national_code(self, national_code: str) -> User:
        result = await self.session.execute(select(User).where(User.national_code == national_code))
        return result.scalars().first()

    async def create_user(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_user(self, user_id: UUID, **kwargs) -> User:
        await self.session.execute(update(User).where(User.user_id == user_id).values(**kwargs))
        await self.session.commit()
        return await self.get_user_by_id(user_id)

    async def update_face_embedding(self, user_id : UUID, embedding: list[float] | None) -> bool:
        """Cập nhật vector khuôn mặt, trả về True nếu thành công"""
        query = (
            update(User)
            .where(User.user_id == user_id)
            .values(face_embedding=embedding)
            .returning(User.user_id)  # <--- Bắt PostgreSQL trả về ID nếu update thành công
        )

        result = await self.session.execute(query)
        await self.session.commit()

        # Nếu có ID trả về -> True (Thành công). Nếu ra None -> False (Lỗi/Không tìm thấy)
        updated_id = result.scalar_one_or_none()
        return updated_id is not None

    async def remove_face_embedding(self, user_id: UUID) -> Literal["deleted", "already_empty", "not_found"]:
        """Xoa face_embedding va tra ve trang thai de tang do ro nghiep vu."""
        user = await self.get_user_by_id(user_id)
        if user is None:
            return "not_found"

        if user.face_embedding is None:
            return "already_empty"

        await self.session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(face_embedding=None)
        )
        await self.session.commit()
        return "deleted"

    async def find_nearest_user_by_embedding(self, embedding_vector: list[float], threshold=0.7) -> User | None:
        """
        Tìm người dùng có khuôn mặt khớp nhất, lọc ngưỡng trực tiếp bằng pgvector.

        GIẢI THÍCH VỀ NGƯỠNG (THRESHOLD) KHOẢNG CÁCH COSINE:
        - pgvector tính KHOẢNG CÁCH (Distance), tức là độ sai lệch giữa 2 khuôn mặt.
        - Công thức toán học: Khoảng cách (Distance) = 1 - Độ tương đồng (Similarity).
        - Khoảng cách càng NHỎ (tiến về 0) -> Khuôn mặt càng GIỐNG NHAU.

        VÍ DỤ THỰC TẾ:
        - Giả sử hệ thống yêu cầu độ tương đồng (Similarity) tối thiểu là 60% (0.6) để xác nhận đúng người.
        - Ta sẽ thiết lập ngưỡng khoảng cách là: Threshold = 1 - 0.6 = 0.4.
        - Điều kiện `distance < 0.4` sẽ đảm bảo chỉ nhận diện những khuôn mặt giống nhau từ 60% trở lên.
        """
        # Khai báo biểu thức tính khoảng cách Cosine từ database
        distance_expr = User.face_embedding.cosine_distance(embedding_vector)

        query = (
            select(User)
            .where(User.face_embedding.is_not(None))  # Bỏ qua những user chưa có dữ liệu khuôn mặt trong DB

            # BẮT BUỘC: Lọc chặt chẽ những người thỏa mãn điều kiện khoảng cách nhỏ hơn ngưỡng
            # (Ví dụ: distance < 0.4 đồng nghĩa với similarity > 0.6)
            .where(distance_expr < threshold)

            # Sắp xếp khoảng cách tăng dần (người có khoảng cách nhỏ nhất / độ tương đồng cao nhất sẽ lên đầu)
            .order_by(distance_expr)

            .limit(1)  # Chỉ lấy đúng 1 người khớp nhất
        )

        result = await self.session.execute(query)
        # Trả về user đầu tiên tìm được, hoặc trả về None nếu toàn bộ db đều bị loại bởi điều kiện threshold
        return result.scalars().first()