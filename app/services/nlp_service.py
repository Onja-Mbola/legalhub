import pytesseract
from PIL import Image
import io
from fastapi import UploadFile
from pdf2image import convert_from_bytes
import spacy
from spacy.pipeline import EntityRuler
import re
from typing import Optional, List, Dict

try:
    nlp = spacy.load("fr_core_news_sm")
except OSError:
    raise ImportError("Modèle spaCy 'fr_core_news_sm' non installé. Exécutez: python -m spacy download fr_core_news_sm")

ruler = nlp.add_pipe("entity_ruler", before="ner")

patterns = [
    {
        "label": "ARTICLE_CODE",
        "pattern": [
            {"LOWER": {"IN": ["article", "art."]}},
            {"SHAPE": "d+"},
            {"LOWER": {"IN": ["du", "de", "d'"]}},
            {"LOWER": {"IN": ["code", "codes"]}},
            {"LOWER": {"IN": ["civil", "pénal", "procédure", "pénal", "obligations", "civiles", "commerciales"]}},
            {"LOWER": {"IN": ["malgache"], "OP": "?"}},
        ]
    },
    {
        "label": "LOI_MALGACHE",
        "pattern": [
            {"LOWER": {"IN": ["loi", "ordonnance"]}},
            {"LOWER": "n°"},
            {"SHAPE": "d+"},
            {"SHAPE": {"IN": ["d+", "-d{3}"]}, "OP": "?"},
            {"LOWER": {"IN": ["du", "du"], "OP": "?"}},
        ]
    },
    {
        "label": "TRIBUNAL_MALGACHE",
        "pattern": [
            {"LOWER": {"IN": ["tribunal", "tpi", "cour"]}},
            {"LOWER": {"IN": ["de", "d'"]}},
            {"LOWER": {"IN": ["première", "premiere"], "OP": "?"}},
            {"LOWER": {"IN": ["instance", "appel"]}, "OP": "?"},
            {"LOWER": {"IN": ["d'", "de"]}, "OP": "?"},
            {"LOWER": {"IN": ["antananarivo", "toamasina", "fianarantsoa", "mahajanga", "toliara", "antsiranana"]}},
        ]
    },
    {
        "label": "ENTITE_JURIDIQUE_MG",
        "pattern": [
            {"LOWER": {"IN": ["greffe", "huissier", "notaire", "avocat"]}},
            {"LOWER": {"IN": ["du", "de"]}, "OP": "?"},
            {"LOWER": {"IN": ["tribunal", "justice"]}, "OP": "?"},
        ]
    },
]

ruler.add_patterns(patterns)


def perform_ocr(file: UploadFile) -> str:
    content = file.file.read()
    if not content:
        return ""

    lang = 'fra'

    if "pdf" in file.content_type.lower():
        images = convert_from_bytes(content)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img, lang=lang) + "\n"
    else:
        img = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(img, lang=lang)

    return text.strip()


def anonymize_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(
        r'\b[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸ][a-zàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]+ [A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸ][a-zàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]+\b',
        '[PARTIE_ANONYME]', text)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_ANONYME]', text)
    text = re.sub(r'(\+261|00261)\s?\d{2}\s?\d{6,8}', '[TEL_MG_ANONYME]', text)
    text = re.sub(
        r'(lot|immeuble|résidence|bp|boîte\s+postale)\s*[\w\s.,-]+\s*(antananarivo|toamasina|fianarantsoa|mahajanga|toliara|antsiranana)\s*\d{3}?',
        '[ADRESSE_MG_ANONYME]', text, flags=re.IGNORECASE)
    text = re.sub(r'\d{1,2}/\d{1,2}/\d{4}', '[DATE_ANONYME]', text)

    return text


def extract_entities(text: str) -> Dict[str, List[str]]:
    if not text:
        return {}

    doc = nlp(text)
    entites = {
        "tribunal": [],
        "tribunal_malgache": [],
        "date": [],
        "loi_malgache": [],
        "article_code": [],
        "entite_juridique_mg": [],
        "autre": []
    }

    for ent in doc.ents:
        label = ent.label_
        if label == "LOC":
            entites["tribunal"].append(ent.text)
        elif label == "DATE":
            entites["date"].append(ent.text)
        elif label == "MONEY":
            entites["autre"].append(f"MONTANT: {ent.text}")
        elif label == "ARTICLE_CODE":
            entites["article_code"].append(ent.text)
        elif label == "LOI_MALGACHE":
            entites["loi_malgache"].append(ent.text)
        elif label == "TRIBUNAL_MALGACHE":
            entites["tribunal_malgache"].append(ent.text)
        elif label == "ENTITE_JURIDIQUE_MG":
            entites["entite_juridique_mg"].append(ent.text)
        else:
            entites["autre"].append(f"{label}: {ent.text}")

    for key in entites:
        entites[key] = list(set(entites[key]))
        entites[key] = [e.strip() for e in entites[key] if e.strip()]

    return entites


def extract_entities_with_regex(text: str) -> Dict[str, List[str]]:
    entities = {
        "article_code": [],
        "loi_malgache": [],
        "tribunal_malgache": [],
        "montant": [],
        "reference": [],
        "date": []
    }

    article_pattern = r'article\s+\d+\s+(du|de)\s+(code\s+(civil|pénal|procédure|obligations\s+civiles\s+et\s+commerciales)(?:\s+malgache)?)'
    entities["article_code"] = re.findall(article_pattern, text, re.IGNORECASE)

    loi_pattern = r'(loi|ordonnance)\s+n°\s+\d{4}-\d{3}'
    entities["loi_malgache"] = re.findall(loi_pattern, text, re.IGNORECASE)

    tribunal_pattern = r'(tribunal\s+de\s+premiè?re\s+instance|cour\s+d\'appel)\s+(d\')?(antananarivo|toamasina|fianarantsoa|mahajanga|toliara|antsiranana)'
    entities["tribunal_malgache"] = re.findall(tribunal_pattern, text, re.IGNORECASE)

    montant_pattern = r'\d+(?:\s?\d{3})*\s*(?:Ariary|Ar|MGA)'
    entities["montant"] = re.findall(montant_pattern, text, re.IGNORECASE)

    ref_pattern = r'(?:n°|N°|numéro)\s*:?\s*[\dA-Z/-]+'
    entities["reference"] = re.findall(ref_pattern, text, re.IGNORECASE)

    date_pattern = r'\d{1,2}/\d{1,2}/\d{4}'
    entities["date"] = re.findall(date_pattern, text)

    for key in entities:
        if isinstance(entities[key], list) and entities[key] and isinstance(entities[key][0], tuple):
            entities[key] = [' '.join(item) if isinstance(item, tuple) else item for item in entities[key]]
        entities[key] = list(set(entities[key]))

    return entities