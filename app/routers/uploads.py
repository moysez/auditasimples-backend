from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
import os
import traceback

from app.db import get_session
from app.models import Upload
from app.services.analysis import run_analysis_from_bytes  # mantém seu analisador original

router = APIRouter()

# ============================================================
# 🆕 Registrar caminho local (NÃO faz upload)
# ============================================================
@router.post("/path")
def register_local_path(
    client_id: int = Form(...),
    filename: str = Form(...),
    filepath: str = Form(...),
    db: Session = Depends(get_session)
):
    """
    Registra apenas o caminho local de um arquivo ZIP (não faz upload de bytes).
    """
    if not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="Caminho local não encontrado.")

    new_upload = Upload(client_id=client_id, filename=filename, filepath=filepath)
    db.add(new_upload)
    db.commit()
    db.refresh(new_upload)
    return {"message": "Caminho salvo com sucesso", "upload_id": new_upload.id}


# ============================================================
# 📋 Listar arquivos registrados por cliente
# ============================================================
@router.get("/list")
def list_files(client_id: int, db: Session = Depends(get_session)):
    """
    Lista os uploads registrados para um cliente específico.
    Evita erro de encoding e garante resposta JSON segura.
    """
    try:
        uploads = (
            db.query(Upload)
            .filter(Upload.client_id == client_id)
            .order_by(Upload.uploaded_at.desc())
            .all()
        )

        result = []
        for u in uploads:
            # Corrige nomes de arquivos e caminhos com encoding estranho (Windows / Latin-1)
            safe_filename = (
                u.filename.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
                if isinstance(u.filename, str)
                else str(u.filename)
            )
            safe_path = (
                u.filepath.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
                if isinstance(u.filepath, str)
                else str(u.filepath)
            )

            result.append({
                "id": u.id,
                "filename": safe_filename,
                "uploaded_at": (
                    u.uploaded_at.strftime("%Y-%m-%d %H:%M:%S")
                    if hasattr(u.uploaded_at, "strftime")
                    else None
                ),
                "path": safe_path,
            })

        return result

    except Exception as e:
        print("❌ ERRO EM /api/uploads/list:", e)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao listar uploads: {str(e)}"
        )


# ============================================================
# 🔍 Rodar análise a partir do caminho local
# ============================================================
@router.get("/analyze/{upload_id}")
def analyze_upload(upload_id: int, db: Session = Depends(get_session)):
    """
    Executa a análise fiscal a partir de um arquivo ZIP já registrado.
    """
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    try:
        with open(upload.filepath, "rb") as f:
            zip_bytes = f.read()

        result = run_analysis_from_bytes(zip_bytes)

        # Garante JSON serializável
        safe_summary = result.get("tax_summary") if isinstance(result, dict) else {}
        return {
            "status": "ok",
            "summary": safe_summary,
            "totals": safe_summary
        }

    except UnicodeDecodeError as e:
        # Captura específica de erro de encoding
        print("⚠️ ERRO DE ENCODING:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Erro de codificação (UTF-8 inválido).")

    except Exception as e:
        print("❌ ERRO EM /api/uploads/analyze:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")
