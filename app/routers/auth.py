import logging
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UserRegister, UserLogin, ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import AuthService
from app.utils.response import success_response

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


def _send_reset_email(email: str, token: str) -> None:
    """Background task: simulate sending a password-reset email."""
    logger.info(f"[EMAIL] Password reset link for {email}: token={token}")


@router.post("/register", summary="Register a new user")
def register(data: UserRegister, db: Session = Depends(get_db)):
    user = AuthService.register(db, data)
    return success_response(
        {"id": user.id, "email": user.email, "role": user.role.value},
        "User registered successfully",
    )


@router.post("/login", summary="Login and receive JWT")
def login(data: UserLogin, db: Session = Depends(get_db)):
    token_data = AuthService.login(db, data)
    return success_response(token_data, "Login successful")


@router.post("/forgot-password", summary="Request a password reset token")
def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    token = AuthService.forgot_password(db, data.email)
    background_tasks.add_task(_send_reset_email, data.email, token)
    return success_response(
        {"reset_token": token},  # Exposed for demo; production should only email the link
        "If this email is registered, a reset link has been sent.",
    )


@router.post("/reset-password", summary="Reset password using token")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    AuthService.reset_password(db, data.token, data.new_password)
    return success_response(message="Password reset successfully")
