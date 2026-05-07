from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import DoctorProfileCreate, DoctorProfileUpdate, DoctorProfileOut
from app.services.doctor_service import DoctorService
from app.utils.auth import require_doctor, get_current_user
from app.utils.response import success_response, paginate

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])


@router.post("/profile", summary="Create doctor profile (Doctor only)")
def create_profile(
    data: DoctorProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor),
):
    profile = DoctorService.create_profile(db, current_user, data)
    return success_response(DoctorProfileOut.model_validate(profile), "Profile created")


@router.put("/profile", summary="Update doctor profile (Doctor only)")
def update_profile(
    data: DoctorProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor),
):
    profile = DoctorService.update_profile(db, current_user, data)
    return success_response(DoctorProfileOut.model_validate(profile), "Profile updated")


@router.get("/", summary="List / search doctors (Public)")
def list_doctors(
    search: Optional[str] = Query(None, description="Search by doctor name"),
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: str = Query("id"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    items, total = DoctorService.get_doctors(db, search, specialization, page, page_size, sort_by, order)
    return paginate([DoctorProfileOut.model_validate(d) for d in items], total, page, page_size)


@router.get("/{doctor_id}", summary="Get doctor by ID (Public)")
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    profile = DoctorService.get_by_id(db, doctor_id)
    return success_response(DoctorProfileOut.model_validate(profile))
