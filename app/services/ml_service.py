from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle
import os
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.dossier import Dossier  # Adaptez l'import selon votre structure
from app.services.search_service import get_all_dossier_texts  # On l'ajoutera plus bas (pour recommandations)

MODEL_PATH = "app/model/model.pkl"
SUMMARY_MODEL = "t5-small"  # Léger ; pour français : "VikOS/t5-french-summarization" si besoin
SIM_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # Multilingue, inclut français

model = None
vectorizer = None
summarizer = None
similarity_model = None


def load_models():
    global model, vectorizer, summarizer, similarity_model
    if model is None:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                model, vectorizer = pickle.load(f)
            print("Modèles sklearn chargés.")
        else:
            raise FileNotFoundError(f"Modèle ML manquant : {MODEL_PATH}. Entraînez-le avec train_ml_model.py")

    if summarizer is None:
        summarizer = pipeline("summarization", model=SUMMARY_MODEL)
        print("Modèle résumé HuggingFace chargé.")

    if similarity_model is None:
        similarity_model = SentenceTransformer(SIM_MODEL)
        print("Modèle similarités chargé.")


def predict_issue(text: str) -> str:
    """Prédit l'issue (Favorable/Défavorable) basée sur texte anonymisé."""
    load_models()
    if not text:
        return "Inconnu"
    vec = vectorizer.transform([text])
    pred = model.predict(vec)[0]
    return "Favorable" if pred == 1 else "Défavorable"  # 1 = Favorable (adaptez labels)


def generate_resume(text: str, max_length: int = 100) -> str:
    """Génère un résumé anonymisé (max 100 mots)."""
    load_models()
    if len(text) < 50:
        return text[:max_length]  # Pas de résumé si court
    summary = summarizer(text, max_length=max_length, min_length=30, do_sample=False)[0]['summary_text']
    return summary


def recommend_similars(dossier_text: str, db: Session, top_k: int = 5) -> List[Tuple[int, float]]:
    """Recommande dossiers similaires (IDs + score similarité). Utilise embeddings sémantiques."""
    load_models()
    if not dossier_text:
        return []

    # Récupérez textes de tous dossiers (anonymisés)
    all_texts = get_all_dossier_texts(db)  # Fonction à ajouter dans search_service.py
    if len(all_texts) < 2:
        return []

    # Embeddings
    emb_query = similarity_model.encode(dossier_text)
    all_embs = similarity_model.encode(all_texts)

    # Similarité cosinus
    from sklearn.metrics.pairwise import cosine_similarity
    sims = cosine_similarity([emb_query], all_embs)[0]

    # Top K (excluez le dossier lui-même si ID connu)
    top_indices = sims.argsort()[-top_k - 1:-1][::-1]
    results = [(i, float(sims[i])) for i in top_indices]
    return results  # e.g., [(dossier_id_2, 0.85), ...]
