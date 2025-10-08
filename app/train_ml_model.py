import glob
import os
import pickle
import re
import json

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.multiclass import OneVsRestClassifier

try:
    import pdfminer.high_level as pdfminer_high_level

    extract_text = pdfminer_high_level.extract_text
    print("✅ pdfminer.six disponible pour l'extraction PDF.")
except ImportError:
    extract_text = None
    print("⚠️ pdfminer.six non installé. Fallback sur PyPDF2 (installez-le avec pip install PyPDF2).")


def extract_text_from_pdf(path: str) -> str:
    """Extrait le texte d'un PDF avec pdfminer ou PyPDF2 comme fallback."""
    if extract_text:
        try:
            return extract_text(path)
        except Exception as e:
            print(f"❌ Erreur pdfminer sur {path}: {e}")
            pass
    # Fallback: PyPDF2
    try:
        import PyPDF2
        text = []
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or '')
        return "\n".join(text)
    except ImportError:
        print("❌ PyPDF2 non installé. Impossible d'extraire les PDFs.")
        return ""
    except Exception as e:
        print(f"❌ Erreur PyPDF2 sur {path}: {e}")
        return ""


def anonymize_text(text: str) -> str:
    """Anonymise le texte (emails, phones, adresses, noms, etc.)."""
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]", text)
    text = re.sub(r"\+?\d[\d \-()]{6,}\d", "[PHONE]", text)
    text = re.sub(r"(demeurant|domicilié|domiciliée|à)\s+[^,\n]{2,60}", "[ADRESSE]", text, flags=re.IGNORECASE)
    text = re.sub(r"\b([A-ZÀ-ÖØ-Ý]{2,}(?:\s+[A-ZÀ-ÖØ-Ý]{2,}){0,4})\b",
                  lambda m: "[NOM]" if len(m.group(1)) > 2 else m.group(1), text)
    text = re.sub(r"\b\d{2,}/\d{2,}-[A-Z]{0,3}\d{0,3}\b", "[REF_DOSSIER]", text)
    text = re.sub(r"\b\d{6,}\b", "[NUM]", text)
    return text


def infer_label_from_text(text: str) -> int:
    """Infère le label à partir du texte (0=Défavorable, 1=Favorable, 2=Renvoi).

    Logique hiérarchique :
    - Priorité 1 : Renvoi (report/complément).
    - Priorité 2 : Favorable (cassation, annulation, accueil du pourvoi).
    - Priorité 3 : Défavorable (rejet, condamnation, confirmation).
    - Par défaut : 0 (Défavorable).
    """
    t = text.lower()

    # Priorité 1 : Renvoi (2)
    renvoi_keywords = [
        "renvoi", "renvoie", "renvoyé", "renvoyee", "renvoyée", "renvoi pour",
        "report", "reporte", "complément d'instruction", "complément d'information",
        "renvoi devant", "suspensif"
    ]
    if any(k in t for k in renvoi_keywords):
        return 2

    # Priorité 2 : Favorable (1)
    favorable_keywords = [
        "casse", "cassé", "cassation", "pourvoi en cassation", "annule", "annulation",
        "casse et annule", "accueille le pourvoi", "accueille", "accepte le pourvoi",
        "accepte", "admet le pourvoi", "admet", "acquitte", "acquittement",
        "infirme", "infirmation", "reçoit", "reçoit le pourvoi", "reformation"
    ]
    if any(k in t for k in favorable_keywords) and not any(k in t for k in ["rejet", "condamne", "rejete"]):
        return 1

    # Priorité 3 : Défavorable (0)
    defavorable_keywords = [
        "rejette", "rejet", "rejet du pourvoi", "condamne", "condamnation",
        "irrecevable", "irrecevabilité", "deboute", "déboute", "confirme",
        "confirmation", "maintient", "maintien", "rejeté", "non-admis",
        "non lieu", "non-lieu"
    ]
    if any(k in t for k in defavorable_keywords):
        return 0

    return 0  # Par défaut : Défavorable


def ingest_pdfs_to_dataframe(pdf_folder: str = "app/data/pdfs") -> pd.DataFrame:
    """Charge et traite les PDFs du dossier, retourne un DataFrame."""
    print(f"\n📂 Recherche des fichiers PDF dans : {os.path.abspath(pdf_folder)}")

    # Vérifie si le dossier existe
    if not os.path.exists(pdf_folder):
        print(f"❌ Le dossier '{pdf_folder}' n'existe pas ! Créez-le ou vérifiez le chemin.")
        return pd.DataFrame()  # Vide

    pdf_files = glob.glob(os.path.join(pdf_folder, "*.pdf"))
    print(f"🔍 {len(pdf_files)} fichiers PDF trouvés.")

    if not pdf_files:
        print("⚠️ Aucun PDF trouvé ! Vérifiez :")
        print("  - Y a-t-il des fichiers .pdf dans le dossier ? (ex: dir app\\data\\pdfs\\)")
        print("  - Les fichiers ont-ils bien l'extension .pdf ?")
        return pd.DataFrame()  # Vide

    rows = []
    total_files = len(pdf_files)
    valid_count = 0

    for i, path in enumerate(pdf_files, 1):
        print(f"\n--- Traitement du fichier {i}/{total_files}: {os.path.basename(path)} ---")
        raw = extract_text_from_pdf(path)
        if not raw.strip():
            print(f"⚠️ Impossible d'extraire le texte de {path} (PDF vide ou corrompu ?)")
            continue

        anon = anonymize_text(raw)
        label = infer_label_from_text(anon)
        rows.append({"texte": anon, "label": label, "source_file": os.path.basename(path)})
        valid_count += 1
        print(
            f"✅ Extrait et traité : {len(anon)} caractères, Label inféré = {label} ({['Défavorable', 'Favorable', 'Renvoi'][label]})")

    print(f"\n📈 Résumé : {valid_count} décisions valides extraites sur {total_files} fichiers PDF trouvés.")
    if valid_count == 0:
        print("❌ Aucune donnée extraite ! Vérifiez les PDFs (corrompus ? protégés par mot de passe ?).")

    return pd.DataFrame(rows)


# Chargement des données seed depuis JSON (NOUVEAU)
seed_json_path = "app/data/seed_data.json"
os.makedirs("data", exist_ok=True)  # Crée le dossier data si absent

seed_data = []
if os.path.exists(seed_json_path):
    try:
        with open(seed_json_path, "r", encoding="utf-8") as f:
            seed_data = json.load(f)
        print(f"📚 Données seed chargées depuis {seed_json_path} : {len(seed_data)} échantillons.")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Erreur lors du chargement de {seed_json_path} : {e}. Fallback sur liste vide.")
        seed_data = []
else:
    print(
        f"⚠️ Fichier {seed_json_path} non trouvé. Créez-le avec des exemples JSON (voir instructions). Fallback sur liste vide.")
    seed_data = []

df_seed = pd.DataFrame(seed_data)
if len(df_seed) == 0:
    print("   → Ajoutez des exemples dans app/data/seed_data.json pour enrichir le corpus initial.")

# Chargement des PDFs (chemin corrigé vers app/data/pdfs)
df_pdfs = ingest_pdfs_to_dataframe("app/data/pdfs")

if not df_pdfs.empty:
    print(
        f"🔄 Fusion avec PDFs : {len(df_pdfs)} échantillons PDF + {len(df_seed)} seed = {len(df_pdfs) + len(df_seed)} total.")
    df_full = pd.concat([df_seed, df_pdfs], ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)
else:
    print(
        "⚠️ Pas de PDFs → Utilisation seulement des données seed. Ajoutez des PDFs pour un vrai entraînement !")
    df_full = df_seed.copy()

# Préparation des données
texts = df_full["texte"].values
labels = df_full["label"].values

print(f"\n📊 Données totales : {len(texts)} échantillons")
print(f"   Distribution des labels : {pd.Series(labels).value_counts().sort_index().to_dict()}")
print(f"   (0=Défavorable, 1=Favorable, 2=Renvoi)")

if len(texts) == 0:
    raise ValueError(
        "❌ Aucune donnée disponible ! Ajoutez des PDFs dans app/data/pdfs/ ou des seeds dans app/data/seed_data.json.")

# Vectorisation TF-IDF
custom_stopwords = [
    "vu", "attendu", "motifs", "cour", "tribunal", "demand", "defense", "ayant", "considérant", "article",
    "code", "loi", "fait", "jugement", "cassation", "appel", "président", "magistrat", "madagascar"
]

vectorizer = TfidfVectorizer(
    max_features=min(5000, len(texts) * 10),  # Ajuste si peu de données
    stop_words=custom_stopwords + ['french'],
    ngram_range=(1, 2),
)

X = vectorizer.fit_transform(texts)
print(f"🔤 Vecteurs TF-IDF créés : {X.shape[0]} échantillons, {X.shape[1]} features.")

# Entraînement et évaluation
base_model = LogisticRegression(max_iter=1000, class_weight='balanced')
model = OneVsRestClassifier(base_model)

if len(texts) > 5:
    # Check pour stratify : Si classe rare <2, désactivez-le
    class_counts = pd.Series(labels).value_counts()
    min_class_size = class_counts.min()
    use_stratify = min_class_size >= 2
    if not use_stratify:
        print(
            f"⚠️ Classe rare ({min_class_size} échantillons) → Split sans stratification (aléatoire). Ajoutez plus de données pour équilibrer.")

    # Split possible
    X_train, X_test, y_train, y_test = train_test_split(
        X, labels, test_size=0.2, random_state=42, stratify=labels if use_stratify else None
    )
    print(f"   Split : {X_train.shape[0]} train, {X_test.shape[0]} test.")

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print("\n=== Évaluation du modèle ===")
    print(f"Précision globale : {accuracy_score(y_test, preds):.2f}")
    print("\nRapport de classification :")
    print(classification_report(
        y_test, preds,
        labels=[0, 1, 2],
        target_names=['Défavorable (0)', 'Favorable (1)', 'Renvoi (2)'],
        zero_division=1
    ))
    print("\nMatrice de confusion :")
    print(confusion_matrix(
        y_test, preds,
        labels=[0, 1, 2]
    ))

    # Validation croisée : Ajustez n_splits basé sur la classe la plus petite
    n_splits = min(5, min_class_size)
    if n_splits >= 2:
        print(f"\nValidation croisée ({n_splits}-fold) en cours...")
        cv_scores = cross_val_score(model, X, labels, cv=n_splits, scoring='accuracy')
        print(f"   Moyenne = {cv_scores.mean():.2f} (±{cv_scores.std():.2f})")
        print(f"   Scores par fold : {cv_scores}")
    else:
        print(f"\n⚠️ Trop peu d'échantillons par classe pour CV ({n_splits}-fold). Skip CV.")

else:
    print(f"\n⚠️ Trop peu de données (<6 échantillons). Entraînement sur tout sans split ni CV.")
    print("   Ajoutez plus de PDFs ou seeds pour une évaluation fiable !")
    model.fit(X, labels)
    # Pas d'évaluation détaillée

# Sauvegarde
os.makedirs("app/model", exist_ok=True)
with open("app/model/model.pkl", "wb") as f:
    pickle.dump((model, vectorizer), f)

os.makedirs("data/processed", exist_ok=True)
df_full.to_csv("data/processed/juris_corpus.csv", index=False)

print(f"\n✅ Modèle juridique malgache entraîné et sauvegardé sous app/model/model.pkl")
print(f"✅ Corpus enrichi ({len(df_full)} échantillons) sauvegardé sous data/processed/juris_corpus.csv")
print(
    "💡 Prochaines étapes : Éditez app/data/seed_data.json pour plus d'exemples, ajoutez des PDFs dans app/data/pdfs/, et relancez.")
