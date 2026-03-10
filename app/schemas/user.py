from datetime import date

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.enums.security_enum import UserStatus
from app.models.user import Belt

# # 1. Schema Cơ bản (Chứa các trường dùng chung)
# class UserBase(BaseModel):
#     full_name: str
#     national_code: str       # CCCD hoặc Mã định danh võ sinh
#     belt: str                # Cấp đai Taekwondo (VD: "Đai Đỏ", "Đai Đen 1 Đẳng")
#     is_elite: bool = False   # Phân loại lớp Tiêu chuẩn hay Tinh hoa

class UserInfo(BaseModel):
    # Dùng snake_case khi khởi tạo, trả về JSON camelCase cho React
    user_id: str
    role_id: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )


class UserProfile(BaseModel):
    birth_date: date
    is_active: UserStatus
    name: str
    phone: str | None = None  # Nên gán None làm mặc định cho trường Optional
    belt: Belt

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )


class UserResponse(BaseModel):
    user_info: UserInfo
    user_profile: UserProfile

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )
