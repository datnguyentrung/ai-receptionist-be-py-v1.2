from fastapi import FastAPI
from app.core.config import settings

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1}/openapi.json"
)

# Endpoint test cơ bản
@app.get("/")
async def root():
    return {"message": "Welcome to AI Receptionist Agent API!"}

if __name__ == "__main__":
    import uvicorn
    # Chạy server với chế độ reload tự động cập nhật khi sửa code
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)