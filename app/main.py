from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings


# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1}/openapi.json"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1)

# Endpoint test cơ bản
@app.get("/")
async def root():
    return {"message": "Welcome to AI Receptionist Agent API!"}

if __name__ == "__main__":
    import uvicorn
    # Chạy server với chế độ reload tự động cập nhật khi sửa code
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)