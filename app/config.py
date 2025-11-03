from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Ambiente
    ENV: str = "dev"  # dev | production

    # Segurança
    # 👉 troque depois se quiser, mas assim já funciona
    SECRET_KEY: str = "auditasimples-super-secret-key"

    # CORS / Frontend
    FRONTEND_ORIGIN: str = "https://auditasimples.io"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
