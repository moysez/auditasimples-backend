from pydantic import BaseSettings

class Settings(BaseSettings):
    ENV: str = "dev"
    FRONTEND_ORIGIN: str = "http://localhost:5500"
    ADMIN_USER: str = "admin"
    ADMIN_PASS: str = "admin123"
    SECRET_KEY: str = "change-me"
    DATABASE_URL: str = ""  # postgres://user:pass@host:5432/db or empty for sqlite
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_DIR: str = "./data"
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_BUCKET: str = "audita-files"
    AI_PROVIDER: str = "none"
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
