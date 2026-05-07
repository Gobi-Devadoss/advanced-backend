from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import FileOut
from app.services.file_service import FileService
from app.utils.auth import get_current_user
from app.utils.response import success_response, paginate

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post("/upload", summary="Upload a file")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meta = await FileService.upload(db, file, current_user)
    return success_response(FileOut.model_validate(meta), "File uploaded successfully")


@router.get("/", summary="List my uploaded files")
def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = FileService.list_files(db, current_user.id, page, page_size)
    return paginate([FileOut.model_validate(f) for f in items], total, page, page_size)
