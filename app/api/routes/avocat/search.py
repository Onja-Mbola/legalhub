from typing import Optional  # Pour Optional types

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse

from app.core.auth import get_current_avocat_or_clerk
from app.db.session import get_db
from app.models.dossier import Dossier
from app.models.user import User
from app.services.FileStorageService import storage
from app.services.ml_service import predict_issue
from app.services.search_service import (
    search_documents,
    search_by_nom_dossier,
    search_by_numero_dossier,
    search_combined
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/files/{object_name}")
async def get_file_url(object_name: str):
    url = storage.get_presigned_url(object_name)
    return {"url": url, "expires_in": "1h"}


@router.get("/search")
async def search(
        q: str,
        field: Optional[str] = Query("ocr_texte",
                                     description="Champ de recherche (e.g., 'ocr_texte', 'nom_dossier', 'numero_dossier')"),
        nom_dossier: Optional[str] = Query(None, description="Filtre par nom de dossier (utilise recherche combinée)"),
        numero_dossier: Optional[str] = Query(None,
                                              description="Filtre par numéro de dossier (utilise recherche combinée)"),
        limit: int = Query(10, ge=1, le=100, description="Nombre max de résultats"),
        db: Session = Depends(get_db)
):
    if nom_dossier or numero_dossier:
        results = search_combined(q, nom_dossier=nom_dossier, numero_dossier=numero_dossier, limit=limit)
    else:
        results = search_documents(q, field=field, limit=limit)

    return {"query": q, "field": field, "results": results, "total": len(results)}


@router.get("/search/nom-dossier")
async def search_by_nom(
        nom: str,
        limit: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db)
):
    results = search_by_nom_dossier(nom, limit=limit)
    return {"query_nom": nom, "results": results, "total": len(results)}


@router.get("/search/numero-dossier")
async def search_by_numero(
        numero: str,
        limit: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db)
):
    results = search_by_numero_dossier(numero, limit=limit)
    return {"query_numero": numero, "results": results, "total": len(results)}


@router.get("/dossiers/{dossier_id}/predicts")
async def get_predictions(dossier_id: int, db: Session = Depends(get_db)):
    dossier = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    text = dossier.resume_nlp or ""
    if not text:
        raise HTTPException(status_code=400, detail="Aucun texte disponible pour la prédiction (resume_nlp vide)")

    pred = predict_issue(text)
    if not dossier.prediction_issue:
        dossier.prediction_issue = pred
        db.commit()

    return {"dossier_id": dossier_id, "prediction_issue": pred,
            "texte_utilise": text[:200] + "..." if len(text) > 200 else text}


@router.get("/dossiers/{dossier_id}/predict", response_class=HTMLResponse)
async def get_prediction(request: Request, dossier_id: int, recompute: bool = Query(False)
                         , db: Session = Depends(get_db), user: User = Depends(get_current_avocat_or_clerk)):
    dossier = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    text = dossier.resume_nlp or ""
    if not text:
        text = dossier.commentaire or ""
        if not text:
            raise HTTPException(status_code=400, detail="Aucun texte disponible pour la prédiction")

    if recompute or not dossier.prediction_issue:
        pred = predict_issue(text)
        dossier.prediction_issue = pred
        db.commit()

    if not dossier.prediction_issue:
        pred = predict_issue(text)
        dossier.prediction_issue = pred
        db.commit()
    else:
        pred = dossier.prediction_issue

    text_used = text[:500] + "..." if len(text) > 500 else text

    prediction_class = "bg-success" if pred == "Favorable" else "bg-danger"
    prediction_icon = "fas fa-check-circle" if pred == "Favorable" else "fas fa-times-circle"

    return templates.TemplateResponse(
        "avocat/predict_dossier.html",
        {
            "request": request,
            "dossier": dossier,
            "user": user,
            "prediction_issue": pred,
            "texte_utilise": text_used,
            "prediction_class": prediction_class,
            "prediction_icon": prediction_icon,
            "full_text": text
        }
    )


@router.get("/analytics/performance", response_class=HTMLResponse)
async def get_analytics(request: Request, db: Session = Depends(get_db),  user: User = Depends(get_current_avocat_or_clerk)):
    from sqlalchemy import text

    results = db.execute(text("""
        SELECT 
            COALESCE(entites_extraites->>'tribunal_malgache', 'Inconnu') as tribunal, 
            COUNT(*) as count, 
            AVG(CASE WHEN prediction_issue = 'Favorable' THEN 1.0 ELSE 0.0 END) as taux_favorable,
            COUNT(CASE WHEN prediction_issue = 'Favorable' THEN 1 END) as count_favorable
        FROM dossiers 
        WHERE entites_extraites IS NOT NULL 
        GROUP BY entites_extraites->>'tribunal_malgache'
        ORDER BY count DESC
    """)).fetchall()

    analytics = [
        {
            "tribunal": r[0],
            "count": r[1],
            "taux_favorable": float(r[2]) if r[2] is not None else 0.0,
            "count_favorable": r[3] or 0
        }
        for r in results
    ]

    total_dossiers_analyzed = sum(item['count'] for item in analytics) if analytics else 0
    global_count_favorable = sum(item['count_favorable'] for item in analytics) if analytics else 0
    global_favorable_rate = (
            global_count_favorable / total_dossiers_analyzed * 100) if total_dossiers_analyzed > 0 else 0.0
    average_favorable_rate = (
            sum(item['taux_favorable'] * 100 for item in analytics) / len(analytics)) if analytics else 0.0
    nb_tribunaux = len(analytics)

    analytics_data = {
        "analytics": analytics,
        "total_dossiers": nb_tribunaux
    }

    return templates.TemplateResponse(
        "avocat/dashboard_analytics.html",
        {
            "request": request,
            "analytics_data": analytics_data,
            "total_dossiers_analyzed": total_dossiers_analyzed,
            "global_count_favorable": global_count_favorable,
            "global_favorable_rate": global_favorable_rate,
            "average_favorable_rate": average_favorable_rate,
            "nb_tribunaux": nb_tribunaux,
            "user": user
        }
    )
