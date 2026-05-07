from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserOut
from app.utils.auth import require_admin
from app.utils.response import success_response, paginate

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users", summary="List all users (Admin only)")
def list_users(
    role: Optional[UserRole] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return paginate([UserOut.model_validate(u) for u in items], total, page, page_size)


@router.patch("/users/{user_id}/deactivate", summary="Deactivate a user (Admin only)")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return success_response(message=f"User {user_id} deactivated")


@router.patch("/users/{user_id}/activate", summary="Activate a user (Admin only)")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    return success_response(message=f"User {user_id} activated")
