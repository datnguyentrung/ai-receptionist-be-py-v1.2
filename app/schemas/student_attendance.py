from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from datetime import date
from pydantic.alias_generators import to_camel

from app.enums.operation_enum import AttendanceStatus, EvaluationStatus
from app.schemas.tuition_payment import TuitionStatusResponse

class StudentAttendanceResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)  # ← thêm

    attendance_id: str
    enrollment_id: str
    student_id: UUID
    student_name: str
    tuition_status: TuitionStatusResponse | None = None  # ← thêm Optional
    class_schedule_id: str
    session_date: date
    attendance_status: AttendanceStatus
    check_in_time: str | datetime | None = None
    evaluation_status: EvaluationStatus | None = None   # ← thêm Optional (có thể None)
    note: str | None = None
    evaluated_by_coach_name: str | None = None
    updated_at: datetime