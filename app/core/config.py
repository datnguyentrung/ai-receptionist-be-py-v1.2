from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Receptionist API"
    API_V1: str = "/api/v1"
    DATABASE_URL: str = "postgresql+asyncpg://root:31102005@localhost:5433/version_4"

    class Config:
        env_file = ".env"
        extra = "ignore"

# Khởi tạo một biến settings để import dùng ở mọi nơi
settings = Settings()