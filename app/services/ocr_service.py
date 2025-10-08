import pytesseract
from PIL import Image
import io

from fastapi import UploadFile
from pdf2image import convert_from_bytes


def perform_ocr(file: UploadFile) -> str:
    content = file.file.read()
    if file.content_type == "application/pdf":
        images = convert_from_bytes(content)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img, lang='fra')
    else:
        img = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(img, lang='fra')
    return text


def anonymize_text(text: str) -> str:
    import re
    text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NOM_ANONYME]', text)
    text = re.sub(r'\d{10,}', '[TEL_ANONYME]', text)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_ANONYME]', text)
    return text
