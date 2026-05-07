import logging
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AppointmentStatus, User
from app.schemas import AppointmentCreate, AppointmentStatusUpdate, AppointmentOut
from app.services.appointment_service import AppointmentService
from app.utils.auth import get_current_user
from app.utils.response import success_response, paginate

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])
logger = logging.getLogger(__name__)


def _notify(appointment_id: int, new_status: str) -> None:
    logger.info(f"[NOTIFY] Appointment #{appointment_id} → {new_status}")


@router.post("/", summary="Book an appointment")
def book_appointment(
    data: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = AppointmentService.create(db, current_user, data)
    background_tasks.add_task(_notify, appt.id, "pending")
    return success_response(AppointmentOut.model_validate(appt), "Appointment booked")


@router.get("/", summary="List appointments with filters and pagination")
def list_appointments(
    status: Optional[AppointmentStatus] = None,
    date: Optional[str] = Query(None, description="Filter by date YYYY-MM-DD"),
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: str = Query("appointment_date"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = AppointmentService.list_appointments(
        db, current_user, status, date, patient_id, doctor_id, page, page_size, sort_by, order
    )
    return paginate([AppointmentOut.model_validate(a) for a in items], total, page, page_size)


@router.get("/{appointment_id}", summary="Get appointment by ID")
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = AppointmentService.get_by_id(db, appointment_id, current_user)
    return success_response(AppointmentOut.model_validate(appt))


@router.patch("/{appointment_id}/status", summary="Update appointment status")
def update_status(
    appointment_id: int,
    data: AppointmentStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = AppointmentService.update_status(db, appointment_id, data, current_user)
    background_tasks.add_task(_notify, appt.id, appt.status.value)
    return success_response(AppointmentOut.model_validate(appt), f"Status updated to {appt.status.value}")
