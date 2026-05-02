from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from datetime import date
from pydantic.alias_generators import to_camel

from app.enums.operation_enum import AttendanceStatus, EvaluationStatus


class StudentAttendanceResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    attendance_id: UUID  # Để UUID luôn cho chuẩn với Java
    enrollment_id: UUID
    student_id: UUID
    student_name: str

    class_schedule_id: str
    session_date: date
    attendance_status: AttendanceStatus  # Hoặc dùng Enum AttendanceStatus của bạn

    # Các field có thể null từ Java
    check_in_time: datetime | None = None
    recorded_by_coach_name: str | None = None  # Java có trả về cái này

    evaluation_status: EvaluationStatus | None = None
    note: str | None = None
    evaluated_by_coach_name: str | None = None

    updated_at: datetime