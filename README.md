# AuditaSimples Backend (FastAPI)

## Rodar local
pip install -r requirements.txt
uvicorn app.main:app --reload

## Variáveis sugeridas (Render)
ENV=prod
FRONTEND_ORIGIN=https://auditasimples.io
ADMIN_USER=admin
ADMIN_PASS=admin123
ADMIN_EMAIL=admin@auditasimples.io
SECRET_KEY=<chave-secreta>
DATABASE_URL=sqlite:///./auditasimples.db

# SMTP (opcional)
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_SERVER=
MAIL_PORT=587
MAIL_TLS=true
MAIL_SSL=false
