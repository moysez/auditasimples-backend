from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Ambiente
    ENV: str = "dev"  # dev | production

    # Banco de dados
    DATABASE_URL: str = ""  # vazio = sqlite local

    # Autenticação inicial (admin default)
    ADMIN_USER: str = "admin"
    ADMIN_PASS: str = "admin123"

    # Segurança
    SECRET_KEY: str = "change-me"

    # CORS / Frontend
    FRONTEND_ORIGIN: str = "http://localhost:5500"

    # Storage (para arquivos ZIP / XML)
    STORAGE_BACKEND: str = "local"  # ou "minio"
    LOCAL_STORAGE_DIR: str = "./data"

    # MinIO (se for usar)
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_BUCKET: str = "audita-files"

    # OpenAI (caso use IA futuramente)
    AI_PROVIDER: str = "none"
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
