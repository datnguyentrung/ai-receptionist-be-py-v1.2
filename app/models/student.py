from sqlalchemy import Column, String, ForeignKey, Enum, Date, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.enums.core_enum import Belt, StudentStatus
from app.models.user import User


class Student(User):
    __tablename__ = "student"

    # Định nghĩa Schema và Indexes cho bảng Student
    __table_args__ = (
        Index("idx_student_status", "student_status"),
        Index("idx_student_branch", "branch_id"),
        Index("idx_student_parent", "parent_user_id"),
        {"schema": "core"}
    )

    # BẮT BUỘC TRONG JOINED INHERITANCE: Khóa chính đồng thời là khóa ngoại trỏ về bảng cha
    user_id = Column(UUID(as_uuid=True), ForeignKey("security.user.user_id"), primary_key=True)

    student_code = Column(String(50), nullable=False, unique=True)
    start_date = Column(Date, nullable=False, default=func.current_date())

    student_status = Column(Enum(StudentStatus),nullable=False, default="ACTIVE")  # Cần thay bằng Enum class thực tế của bạn

    # Giả định branch_id là UUID, tùy chỉnh lại kiểu dữ liệu nếu Branch dùng ID kiểu khác
    branch_id = Column(UUID(as_uuid=True), ForeignKey("core.branch.branch_id"), nullable=False)

    belt = Column(Enum(Belt), nullable=False, default=Belt.C10)  # Cần thay bằng Enum class thực tế của bạn

    # Vector column cho face embedding (yêu cầu pgvector extension trên PostgreSQL)
    face_embedding = Column(Vector(512))

    # ForeignKey trỏ về bảng User để lưu parent (Người bảo hộ/Coach)
    parent_user_id = Column(UUID(as_uuid=True), ForeignKey("security.user.user_id"), nullable=True)

    national_code = Column(String(50), unique=True)

    # --- Relationships ---
    # Thiết lập relationship giúp dễ dàng truy xuất object thay vì chỉ có ID
    parent = relationship("User", foreign_keys=[parent_user_id], backref="children_students")

    # Bạn có thể thêm relationship cho Role, Branch nếu cần
    # branch = relationship("Branch", foreign_keys=[branch_id])

    # Định danh class con cho Polymorphism
    __mapper_args__ = {
        "polymorphic_identity": "student",
        # Chỉ định rõ SQLAlchemy phải dùng cột user_id để JOIN kế thừa,
        # giúp nó bỏ qua sự nhầm lẫn với cột parent_user_id
        "inherit_condition": user_id == User.user_id
    }