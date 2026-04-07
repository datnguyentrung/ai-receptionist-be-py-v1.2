import decimal
from pydantic.alias_generators import to_camel

from pydantic import BaseModel, ConfigDict
from uuid import UUID


class TuitionPaymentDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    detail_id: UUID
    enrollment_id: UUID
    schedule_id: str
    for_month: int
    for_year: int
    amount_allocated: decimal.Decimal

class ActiveClassStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    enrollment_id: UUID
    schedule_id: str
    paid: bool
    amount_allocated: decimal.Decimal

class TuitionStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    student_id: UUID
    student_code: str
    full_name: str
    has_paid_current_month: bool
    current_month: int
    current_year: int
    active_classes: list[ActiveClassStatus]  # Danh sách tên lớp đang học
