from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dossier import Dossier
from app.services.FileStorageService import storage
from app.services.ml_service import predict_issue
from app.services.search_service import search_documents

router = APIRouter()
@router.get("/files/{object_name}")
async def get_file_url(object_name: str):
    url = storage.get_presigned_url(object_name)
    return {"url": url, "expires_in": "1h"}
@router.get("/search")
async def search(q: str, limit: int = 10, db: Session = Depends(get_db)):
    results = search_documents(q, limit)
    return {"query": q, "results": results, "total": len(results)}
@router.get("/dossiers/{dossier_id}/predict")
async def get_prediction(dossier_id: int, db: Session = Depends(get_db)):
    dossier = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not dossier:
        raise HTTPException(404, "Dossier non trouvé")
    text = dossier.ocr_texte or dossier.contenu_resume or ""
    pred = predict_issue(text)
    return {"prediction_issue": pred}


@router.get("/analytics/performance")
async def get_analytics(db: Session = Depends(get_db)):
    from sqlalchemy import func, text
    results = db.execute(text("""
        SELECT entites_extraites->>'tribunal_malgache' as tribunal, 
               COUNT(*) as count, 
               AVG(CASE WHEN prediction_issue = 'Favorable' THEN 1 ELSE 0 END) as taux_favorable
        FROM dossiers 
        WHERE entites_extraites ? 'tribunal_malgache' 
        GROUP BY entites_extraites->>'tribunal_malgache'
    """)).fetchall()
    return {"analytics": [{"tribunal": r[0], "count": r[1], "taux_favorable": float(r[2])} for r in results]}

