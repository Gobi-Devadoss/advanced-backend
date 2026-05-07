import os
import uuid
from typing import Tuple, List
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models import FileMetadata, User
from app.config import settings
from app.utils.file_handler import validate_file, ALLOWED_TYPES


class FileService:

    @staticmethod
    async def upload(db: Session, file: UploadFile, uploader: User) -> FileMetadata:
        content = await validate_file(file)

        ext = ALLOWED_TYPES.get(file.content_type, "")
        unique_name = f"{uuid.uuid4().hex}{ext}"
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

        with open(file_path, "wb") as f:
            f.write(content)

        meta = FileMetadata(
            uploader_id=uploader.id,
            filename=unique_name,
            original_filename=file.filename,
            file_type=file.content_type,
            file_size=len(content),
            file_path=file_path,
        )
        db.add(meta)
        db.commit()
        db.refresh(meta)
        return meta

    @staticmethod
    def list_files(
        db: Session, uploader_id: int, page: int = 1, page_size: int = 10
    ) -> Tuple[List[FileMetadata], int]:
        query = db.query(FileMetadata).filter(FileMetadata.uploader_id == uploader_id)
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total
