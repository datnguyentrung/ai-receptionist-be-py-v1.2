from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Receptionist API"
    API_V1: str = "/api/v1"

    class Config:
        env_file = ".env"

# Khởi tạo một biến settings để import dùng ở mọi nơi
settings = Settings()