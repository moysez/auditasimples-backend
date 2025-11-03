from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ============================================================
    # 🌎 AMBIENTE
    # ============================================================
    ENV: str = "dev"  # opções: dev | production

    # ============================================================
    # 🔐 SEGURANÇA
    # ============================================================
    SECRET_KEY: str = "auditasimples-super-secret-key"  # troque depois se quiser

    # ============================================================
    # 🌐 CORS / FRONTEND
    # ============================================================
    FRONTEND_ORIGIN: str = "https://auditasimples.io"

    # ============================================================
    # ⚙️ CONFIGURAÇÃO PADRÃO DO Pydantic
    # ============================================================
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 👈 ignora variáveis extras (ex: DATABASE_URL, LOCAL_STORAGE_DIR)


# Instância única usada pelo app inteiro
settings = Settings()
