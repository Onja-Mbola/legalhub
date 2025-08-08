import os
from typing import List

from fastapi import UploadFile


def save_uploaded_files(files: List[UploadFile], dossier_path: str) -> List[str]:
    saved_files = []
    os.makedirs(dossier_path, exist_ok=True)
    for file in files:
        file_location = os.path.join(dossier_path, file.filename)
        with open(file_location, "wb") as f:
            f.write(file.file.read())
        saved_files.append(file.filename)
    return saved_files