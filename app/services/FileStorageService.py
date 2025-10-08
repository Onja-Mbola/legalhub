import os
from typing import List
from fastapi import UploadFile, HTTPException
from minio import Minio
from minio.error import S3Error
from datetime import timedelta
import io
from app.core.config import settings


class MinIOStorage:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"Erreur MinIO: {str(e)}")

    def save_uploaded_files(self, files: List[UploadFile], dossier_path: str) -> List[str]:
        saved_files = []
        for file in files:
            if file.filename.strip():
                object_name = f"{dossier_path}/{os.urandom(16).hex()}_{file.filename}"
                self.client.put_object(
                    self.bucket_name,
                    object_name,
                    io.BytesIO(file.file.read()),
                    length=file.size,
                    content_type=file.content_type
                )
                saved_files.append(object_name)
        return saved_files

    def get_presigned_url(self, object_name: str, expires: timedelta = timedelta(hours=1)) -> str:
        try:
            return self.client.presigned_get_object(self.bucket_name, object_name, expires=expires)
        except S3Error:
            raise HTTPException(status_code=404, detail="Fichier non trouvé")

    def delete_object(self, object_name: str):
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error:
            pass


storage = MinIOStorage()
