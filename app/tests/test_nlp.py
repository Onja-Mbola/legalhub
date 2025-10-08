import pytest
from app.services.nlp_service import extract_entities


def test_extract_entities():
    text = "Article 123 du Code civil malgache. Tribunal d'Antananarivo."
    entites = extract_entities(text)
    assert "article_code" in entites
    assert len(entites["article_code"]) > 0
    assert "tribunal_malgache" in entites

