# file: app/api/v1/__init__.py
from fastapi import APIRouter

# Import các router
from .user_api import router as users_router

api_router = APIRouter()

# Nhúng thẳng router vào, KHÔNG truyền thêm prefix hay tags nữa
# vì bên trong users.py đã khai báo đầy đủ rồi!
api_router.include_router(users_router)

# Sau này có thêm file attendance hay classes, bạn cũng làm tương tự:
# api_router.include_router(attendance.router)
# api_router.include_router(classes.router)