from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENV: str = "dev"
    SECRET_KEY: str = "auditasimples-super-secret-key"
    FRONTEND_ORIGIN: str = "https://auditasimples.io"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 👈 ignora variáveis não definidas
