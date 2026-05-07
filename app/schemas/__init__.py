from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, EmailStr, field_validator
from app.models import AppointmentStatus, UserRole


# ── Generic responses ─────────────────────────────────────────────────────────

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.patient

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


# ── User ──────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Doctor Profile ────────────────────────────────────────────────────────────

class DoctorProfileCreate(BaseModel):
    specialization: str
    qualification: Optional[str] = None
    experience_years: int = 0
    consultation_fee: float = 0.0
    bio: Optional[str] = None
    available_from: str = "09:00"
    available_to: str = "17:00"


class DoctorProfileUpdate(BaseModel):
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    bio: Optional[str] = None
    available_from: Optional[str] = None
    available_to: Optional[str] = None


class DoctorProfileOut(BaseModel):
    id: int
    user_id: int
    specialization: str
    qualification: Optional[str] = None
    experience_years: int
    consultation_fee: float
    bio: Optional[str] = None
    available_from: str
    available_to: str

    model_config = {"from_attributes": True}


# ── Appointment ───────────────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: str   # YYYY-MM-DD
    appointment_time: str   # HH:MM
    reason: Optional[str] = None

    @field_validator("appointment_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be YYYY-MM-DD")
        return v

    @field_validator("appointment_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("Time must be HH:MM")
        return v


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
    notes: Optional[str] = None


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_date: str
    appointment_time: str
    status: AppointmentStatus
    reason: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


# ── File ──────────────────────────────────────────────────────────────────────

class FileOut(BaseModel):
    id: int
    original_filename: str
    filename: str
    file_type: str
    file_size: int

    model_config = {"from_attributes": True}
