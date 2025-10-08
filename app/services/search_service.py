import os
from typing import List, Dict

import whoosh
from sqlalchemy.orm import Session
from whoosh.fields import Schema, TEXT, ID, KEYWORD
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

from app.models.dossier import Dossier  # Adaptez

# Schéma index (adapté à vos champs anonymisés)
schema = Schema(
    id=ID(stored=True),  # ID dossier ou echange
    numero_dossier=KEYWORD(stored=True),  # Pour filtre exact
    ocr_texte=TEXT(stored=True, analyzer=whoosh.analysis.StemmingAnalyzer()),  # Full-text avec stemming français
    contenu_resume=TEXT(stored=True),
    entites_extraites=TEXT(stored=True),  # JSON comme texte (query sur "tribunal_malgache:Antananarivo")
    prediction_issue=KEYWORD(stored=True)  # Filtre par issue
)

# Dossier index (créé auto)
INDEX_DIR = "whoosh_index"
if not os.path.exists(INDEX_DIR):
    os.mkdir(INDEX_DIR)
    ix = create_in(INDEX_DIR, schema)
else:
    ix = open_dir(INDEX_DIR)


def index_document(doc_type: str, doc_id: int, numero_dossier: str, ocr_texte: str, contenu_resume: str, entites: Dict,
                   prediction: str):
    """Indexe un document (dossier ou echange) après OCR/NLP."""
    writer = ix.writer()
    entites_text = " ".join([f"{k}:{v}" for k, vs in entites.items() for v in vs])  # e.g., "article_code:Article 123"
    writer.add_document(
        id=f"{doc_type}_{doc_id}",
        numero_dossier=numero_dossier,
        ocr_texte=ocr_texte,
        contenu_resume=contenu_resume or "",
        entites_extraites=entites_text,
        prediction_issue=prediction
    )
    writer.commit()


def search_documents(query_str: str, limit: int = 10) -> List[Dict]:
    """Recherche full-text (e.g., "loi malgache tribunal"). Retourne résultats anonymisés."""
    with ix.searcher() as searcher:
        query = QueryParser("ocr_texte", ix.schema).parse(query_str)  # Priorité sur ocr_texte
        results = searcher.search(query, limit=limit)
        hits = []
        for hit in results:
            hits.append({
                "id": hit["id"],
                "numero_dossier": hit["numero_dossier"],
                "score": hit.score,
                "contenu_resume": hit["contenu_resume"][:200] + "...",  # Snippet anonymisé
                "entites": hit["entites_extraites"][:200]  # Aperçu
            })
        return hits


def get_all_dossier_texts(db: Session) -> List[str]:
    """Pour recommandations : Récupère tous contenus_resume anonymisés."""
    dossiers = db.query(Dossier).all()
    return [d.contenu_resume or d.ocr_texte or "" for d in dossiers if d.contenu_resume or d.ocr_texte]

# Exemple d'index après création (appelez dans services)
# index_document("dossier", 1, "DOS-001", ocr_text, resume, entites, "Favorable")
