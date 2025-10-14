import os
import shutil  # Pour réindexation optionnelle
from typing import List, Dict

import whoosh
from sqlalchemy.orm import Session
from whoosh.fields import Schema, TEXT, ID, KEYWORD
from whoosh.index import create_in, open_dir, exists_in
from whoosh.qparser import QueryParser
from whoosh.query import Or  # Pour recherches combinées (optionnel)
from whoosh.analysis import StemmingAnalyzer  # Pour stemming français

from app.models.dossier import Dossier  # Adaptez le chemin si nécessaire

# Schéma index mis à jour (ajout de nom_dossier comme TEXT avec stemming français)
schema = Schema(
    id=ID(stored=True),  # ID dossier ou echange
    numero_dossier=KEYWORD(stored=True),  # Pour filtre exact
    nom_dossier=TEXT(stored=True, analyzer=StemmingAnalyzer("fr")),  # Full-text sur nom_dossier avec stemming français
    ocr_texte=TEXT(stored=True, analyzer=StemmingAnalyzer("fr")),  # Full-text avec stemming français
    contenu_resume=TEXT(stored=True),
    entites_extraites=TEXT(stored=True),  # JSON comme texte (query sur "tribunal_malgache:Antananarivo")
    prediction_issue=KEYWORD(stored=True)  # Filtre par issue
)

# Dossier index (créé auto)
INDEX_DIR = "whoosh_index"
if not os.path.exists(INDEX_DIR):
    os.mkdir(INDEX_DIR)

if not exists_in(INDEX_DIR):
    ix = create_in(INDEX_DIR, schema)
else:
    ix = open_dir(INDEX_DIR)


def index_document(doc_type: str, doc_id: int, numero_dossier: str, nom_dossier: str, ocr_texte: str,
                   contenu_resume: str, entites: Dict, prediction: str):
    """Indexe un document (dossier ou echange) après OCR/NLP. Supporte nom_dossier."""
    writer = ix.writer()
    entites_text = " ".join([f"{k}:{v}" for k, vs in entites.items() for v in vs])  # e.g., "article_code:Article 123"
    writer.add_document(
        id=f"{doc_type}_{doc_id}",
        numero_dossier=numero_dossier,
        nom_dossier=nom_dossier,  # Nouveau champ
        ocr_texte=ocr_texte,
        contenu_resume=contenu_resume or "",
        entites_extraites=entites_text,
        prediction_issue=prediction
    )
    writer.commit()


def search_documents(query_str: str, field: str = "ocr_texte", limit: int = 10) -> List[Dict]:
    """Recherche full-text ou par champ spécifique (e.g., 'nom_dossier' pour recherche par nom).

    Args:
        query_str: La requête de recherche (e.g., "Dupont" pour nom_dossier).
        field: Champ cible ('ocr_texte', 'nom_dossier', 'numero_dossier', etc.).
        limit: Nombre max de résultats.

    Returns:
        Liste de dicts avec résultats anonymisés.
    """
    with ix.searcher() as searcher:
        if field not in ix.schema.names():
            raise ValueError(f"Champ '{field}' non indexé dans le schéma.")
        query = QueryParser(field, ix.schema).parse(query_str)
        results = searcher.search(query, limit=limit)
        hits = []
        for hit in results:
            hits.append({
                "id": hit["id"],
                "numero_dossier": hit.get("numero_dossier", ""),
                "nom_dossier": hit.get("nom_dossier", ""),  # Ajout du nom
                "score": hit.score,
                "contenu_resume": (hit.get("contenu_resume", "")[:200] + "...") if hit.get("contenu_resume") else "",
                "entites": hit.get("entites_extraites", "")[:200] if hit.get("entites_extraites") else ""
            })
        return hits


def search_by_nom_dossier(nom: str, limit: int = 10) -> List[Dict]:
    """Recherche spécifique par nom de dossier (flexible, e.g., "Dupont" trouve "Affaire Dupont")."""
    # Recherche partielle/full-text sur nom_dossier
    return search_documents(nom, field="nom_dossier", limit=limit)


def search_by_numero_dossier(numero: str, limit: int = 10) -> List[Dict]:
    """Recherche spécifique par numéro de dossier (exacte recommandée)."""
    # Pour match exact, utilisez des guillemets dans la query si besoin
    return search_documents(f'"{numero}"', field="numero_dossier", limit=limit)


def search_combined(query_str: str, nom_dossier: str = None, numero_dossier: str = None, limit: int = 10) -> List[Dict]:
    """Recherche combinée : full-text ET/OU par nom/numéro de dossier."""
    with ix.searcher() as searcher:
        queries = [QueryParser("ocr_texte", ix.schema).parse(query_str)]

        if nom_dossier:
            queries.append(QueryParser("nom_dossier", ix.schema).parse(nom_dossier))

        if numero_dossier:
            queries.append(QueryParser("numero_dossier", ix.schema).parse(f'"{numero_dossier}"'))

        query = Or(queries)
        results = searcher.search(query, limit=limit)
        hits = []
        for hit in results:
            hits.append({
                "id": hit["id"],
                "numero_dossier": hit.get("numero_dossier", ""),
                "nom_dossier": hit.get("nom_dossier", ""),
                "score": hit.score,
                "contenu_resume": (hit.get("contenu_resume", "")[:200] + "...") if hit.get("contenu_resume") else "",
                "entites": hit.get("entites_extraites", "")[:200] if hit.get("entites_extraites") else ""
            })
        return hits


def reindex_all_dossiers(db: Session):
    """Réindexe tous les dossiers existants avec le nouveau schéma (nom_dossier inclus).

    Attention : Cela met à jour l'index. Exécutez une seule fois après mise à jour du schéma.
    Si le schéma a changé, supprimez manuellement le dossier 'whoosh_index' avant d'appeler.
    """
    # Optionnel : Supprimez et recréez l'index pour repartir à zéro (décommentez si besoin)
    # if os.path.exists(INDEX_DIR):
    #     shutil.rmtree(INDEX_DIR)
    # os.mkdir(INDEX_DIR)
    # ix = create_in(INDEX_DIR, schema)

    dossiers = db.query(Dossier).all()
    writer = ix.writer()
    updated_count = 0
    for dossier in dossiers:
        if dossier.id:  # Assurez-vous que l'ID existe
            entites = dossier.entites_extraites or {}
            entites_text = " ".join([f"{k}:{v}" for k, vs in entites.items() for v in vs])
            # Utilisez update_document pour écraser si l'ID existe déjà
            writer.update_document(
                id=f"dossier_{dossier.id}",
                numero_dossier=dossier.numero_dossier or "",
                nom_dossier=dossier.nom_dossier or "",  # Nouveau champ
                ocr_texte=getattr(dossier, 'ocr_texte', '') or "",  # Si ocr_texte n'existe pas dans Dossier, adaptez
                contenu_resume=dossier.resume_nlp or "",  # Utilisez resume_nlp comme résumé (adaptez si différent)
                entites_extraites=entites_text,
                prediction_issue=dossier.prediction_issue or ""
            )
            updated_count += 1
    writer.commit()
    print(f"Réindexé {updated_count} dossiers.")


def get_all_dossier_texts(db: Session) -> List[str]:
    """Pour recommandations : Récupère tous contenus_resume anonymisés."""
    dossiers = db.query(Dossier).all()
    return [d.resume_nlp or getattr(d, 'ocr_texte', '') or "" for d in dossiers if
            d.resume_nlp or getattr(d, 'ocr_texte', '')]

# Exemples d'utilisation (appelez dans vos services ou scripts)
# Exemple 1: Indexer un nouveau dossier
# index_document("dossier", 1, "DOS-001", "Affaire Dupont vs Martin", ocr_text, resume_nlp, entites, "Favorable")

# Exemple 2: Recherche par nom de dossier
# resultats = search_by_nom_dossier("Dupont", limit=5)
# for res in resultats:
#     print(f"ID: {res['id']}, Nom: {res['nom_dossier']}, Numéro: {res['numero_dossier']}, Score: {res['score']}")

# Exemple 3: Recherche combinée
# resultats = search_combined("loi malgache", nom_dossier="Dupont", numero_dossier="DOS-001", limit=10)

# Exemple 4: Réindexer (une seule fois, avec une session DB)
# reindex_all_dossiers(db_session)
