import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.db.session import Base
from app.enums.core_enum import Belt
from app.enums.security_enum import UserStatus


class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "security"}

    user_id = Column(UUID(as_uuid=True), primary_key = True, default = uuid.uuid4)
    national_code = Column(String(50), unique=True, nullable=True)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String, nullable=False)

    status = Column(Enum(UserStatus, name="user_status_enum", schema="security"), nullable=False,default=UserStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))

    role_code = Column(String, ForeignKey("security.role.role_code"), nullable=False)

    phone_number = Column(String(10))
    birth_date = Column(Date, nullable=False)
    belt = Column(Enum(Belt, name="belt_enum", schema="security"), default=Belt.C10, nullable=False)

    # Vector 512 chiều cho Face Embedding
    face_embedding = Column(Vector(512))
