from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.services.nlp_service import perform_ocr, anonymize_text, extract_entities
from app.services.ml_service import predict_issue, generate_resume, recommend_similars
from app.services.search_service import index_document
from app.services.FileStorageService import storage
from app.models.dossier import Dossier
import json


def process_upload(
        obj,  # L'objet DB (e.g., EchangeConclusion)
        files: List[UploadFile],  # Fichiers
        db: Session,
        dossier: Dossier,
        file_field: Optional[str] = None,  # Champ DB pour paths (JSON)
        contenu_field: Optional[str] = "contenu_resume",  # Champ texte existant
        ocr_all_files: bool = False,
        run_ml: bool = True,
        subfolder: str = ""  # Pour variantes (e.g., "par_defaut", "premiere_appel")
):
    """
    Hook générique : MinIO + OCR/NLP + ML + Whoosh.
    - subfolder : Ajoute /subfolder au path MinIO (e.g., "dossiers/DOS-001/echangeconclusions/par_defaut").
    """
    if not hasattr(dossier, 'consentement_rgpd') or not dossier.consentement_rgpd:
        print(f"Traitement NLP skip pour {dossier.numero_dossier}: Pas de consentement RGPD")
        return

    try:
        # 1. Stockage MinIO (anonymisé, sans avocat_nom)
        paths = []
        if files:
            doc_type_lower = obj.__class__.__name__.lower()  # "echangeconclusion"
            dossier_path = f"dossiers/{dossier.numero_dossier}/{doc_type_lower}s/{subfolder}".strip("/")
            paths = storage.save_uploaded_files(files, dossier_path)  # Retourne ["uuid_file.pdf", ...]
            # Stockez comme JSON (ou list si DB permet)
            setattr(obj, file_field, json.dumps(paths))  # obj.conclusions_file = '["path1", "path2"]'

        # 2. OCR et Anonymisation
        texts = []
        if files and files[0].filename:
            if ocr_all_files:
                for file in files:
                    ocr_text = perform_ocr(file)
                    anonymized = anonymize_text(ocr_text)
                    texts.append(anonymized)
            else:
                ocr_text = perform_ocr(files[0])
                anonymized = anonymize_text(ocr_text)
                texts.append(anonymized)

            full_ocr = " ".join(texts)
            obj.ocr_texte = full_ocr
            entites = extract_entities(full_ocr)
            obj.entites_extraites = entites
        else:
            entites = {}

        # 3. ML (sur Dossier)
        full_text = " ".join(texts) if texts else (getattr(obj, contenu_field, "") or "")
        if run_ml and full_text:
            dossier.prediction_issue = predict_issue(full_text)
            dossier.resume_nlp = generate_resume(full_text)
            sims = recommend_similars(full_text, db)
            print(f"Recommandations pour {dossier.numero_dossier} ({type(obj).__name__}): {sims}")

        # 4. Index Whoosh
        doc_type = obj.__class__.__name__.lower()
        contenu = getattr(obj, contenu_field, obj.ocr_texte or "")
        index_document(
            doc_type,
            obj.id,
            dossier.numero_dossier,
            dossier.nom_dossier,
            obj.ocr_texte or "",
            contenu,
            entites,
            dossier.prediction_issue or ""
        )

        # Commit
        db.commit()
        db.refresh(obj)
        if hasattr(obj, 'dossier_id'):
            db.refresh(db.query(Dossier).get(obj.dossier_id))

    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erreur DB process_upload {type(obj).__name__} {obj.id}: {str(e)}")
    except Exception as e:
        print(f"Erreur process_upload {type(obj).__name__} {obj.id}: {str(e)}")
