import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Date, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Lưu ý: Cần cài đặt thư viện pgvector để dùng kiểu Vector (pip install pgvector)
from pgvector.sqlalchemy import Vector

from app.db.session import Base
from app.enums.security_enum import UserStatus


# Giả định bạn đã có các Enum này, hãy import chúng
# from app.enums.core_enum import StudentStatus, Belt

class User(Base):
    __tablename__ = "user"

    # Định nghĩa Schema và Indexes cho bảng User
    __table_args__ = (
        Index("idx_user_phone", "phone_number"),
        Index("idx_user_role", "role_code"),
        {"schema": "security"}
    )

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(100), nullable=False)

    # Java là Boolean object (cho phép null), nên nullable=True
    gender = Column(Boolean, nullable=True)

    password_hash = Column(String, nullable=False)

    status = Column(Enum(UserStatus, name="user_status_enum", schema="security"), nullable=False,
                    default=UserStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))

    role_code = Column(String, ForeignKey("security.role.role_code"), nullable=False)

    # Đổi thành String(20) theo đúng cấu hình bên Java
    phone_number = Column(String(20))
    birth_date = Column(Date, nullable=False)

    # Cấu hình Joined Table Inheritance cho SQLAlchemy
    __mapper_args__ = {
        "polymorphic_identity": "user",
        # Không cần 'polymorphic_on' nếu không có cột DTYPE cụ thể,
        # SQLAlchemy tự động nhận diện qua Foreign Key ở bảng con.
    }