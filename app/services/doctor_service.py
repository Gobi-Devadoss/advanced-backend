from typing import Optional, Tuple, List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import DoctorProfile, User, UserRole
from app.schemas import DoctorProfileCreate, DoctorProfileUpdate
from app.utils.cache import cache_get, cache_set, cache_clear_prefix

CACHE_TTL = 120  # 2 minutes


class DoctorService:

    @staticmethod
    def create_profile(db: Session, user: User, data: DoctorProfileCreate) -> DoctorProfile:
        if user.role != UserRole.doctor:
            raise HTTPException(status_code=403, detail="Only doctors can create a profile")
        if db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first():
            raise HTTPException(status_code=400, detail="Doctor profile already exists")
        profile = DoctorProfile(user_id=user.id, **data.model_dump())
        db.add(profile)
        db.commit()
        db.refresh(profile)
        cache_clear_prefix("doctors:")
        return profile

    @staticmethod
    def update_profile(db: Session, user: User, data: DoctorProfileUpdate) -> DoctorProfile:
        profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Doctor profile not found")
        for key, val in data.model_dump(exclude_none=True).items():
            setattr(profile, key, val)
        db.commit()
        db.refresh(profile)
        cache_clear_prefix("doctors:")
        return profile

    @staticmethod
    def get_doctors(
        db: Session,
        search: Optional[str] = None,
        specialization: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "id",
        order: str = "asc",
    ) -> Tuple[List[DoctorProfile], int]:
        cache_key = f"doctors:{search}:{specialization}:{page}:{page_size}:{sort_by}:{order}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        query = db.query(DoctorProfile).join(User)
        if search:
            query = query.filter(User.full_name.ilike(f"%{search}%"))
        if specialization:
            query = query.filter(DoctorProfile.specialization.ilike(f"%{specialization}%"))

        total = query.count()
        sort_col = getattr(DoctorProfile, sort_by, DoctorProfile.id)
        if order == "desc":
            sort_col = sort_col.desc()
        items = query.order_by(sort_col).offset((page - 1) * page_size).limit(page_size).all()

        result = (items, total)
        cache_set(cache_key, result, CACHE_TTL)
        return result

    @staticmethod
    def get_by_id(db: Session, doctor_id: int) -> DoctorProfile:
        profile = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return profile
