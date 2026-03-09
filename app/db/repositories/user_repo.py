from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
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

    async def update_face_embedding(self, user_id : UUID, embedding: list[float]) -> bool:
        """Cập nhật vector khuôn mặt, trả về True nếu thành công"""
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(face_embedding=embedding)
            .returning(User.user_id)  # <--- Bắt PostgreSQL trả về ID nếu update thành công
        )

        result = await self.session.execute(stmt)
        await self.session.commit()

        # Nếu có ID trả về -> True (Thành công). Nếu ra None -> False (Lỗi/Không tìm thấy)
        updated_id = result.scalar_one_or_none()
        return updated_id is not None