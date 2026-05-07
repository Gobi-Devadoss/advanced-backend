from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import User
from app.schemas import UserRegister, UserLogin
from app.utils.auth import (
    hash_password, verify_password,
    create_access_token, create_reset_token, verify_reset_token,
)
from app.config import settings


class AuthService:

    @staticmethod
    def register(db: Session, data: UserRegister) -> User:
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(
            full_name=data.full_name,
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def login(db: Session, data: UserLogin) -> dict:
        user = db.query(User).filter(User.email == data.email, User.is_active == True).first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token({"sub": str(user.id), "role": user.role.value})
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user.role.value,
            "user_id": user.id,
        }

    @staticmethod
    def forgot_password(db: Session, email: str) -> str:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal whether email exists — return a dummy message
            return "reset-token-not-applicable"
        token = create_reset_token(email)
        user.reset_token = token
        user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(
            minutes=settings.RESET_TOKEN_EXPIRE_MINUTES
        )
        db.commit()
        return token

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> None:
        email = verify_reset_token(token)
        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        user = db.query(User).filter(User.email == email, User.reset_token == token).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        user.hashed_password = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.commit()
