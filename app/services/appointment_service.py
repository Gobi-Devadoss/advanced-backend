from datetime import datetime
from typing import Optional, Tuple, List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Appointment, AppointmentStatus, DoctorProfile, User, UserRole
from app.schemas import AppointmentCreate, AppointmentStatusUpdate


class AppointmentService:

    @staticmethod
    def _check_slot(db: Session, doctor_id: int, date: str, time: str, exclude_id: Optional[int] = None) -> None:
        """Raise 409 if the slot is already taken."""
        query = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == date,
            Appointment.appointment_time == time,
            Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.approved]),
        )
        if exclude_id:
            query = query.filter(Appointment.id != exclude_id)
        if query.first():
            raise HTTPException(status_code=409, detail="This time slot is already booked")

    @staticmethod
    def _check_working_hours(doctor: DoctorProfile, time: str) -> None:
        def to_min(t: str) -> int:
            h, m = map(int, t.split(":"))
            return h * 60 + m
        appt = to_min(time)
        if not (to_min(doctor.available_from) <= appt < to_min(doctor.available_to)):
            raise HTTPException(
                status_code=400,
                detail=f"Doctor is only available {doctor.available_from}–{doctor.available_to}",
            )

    @staticmethod
    def _check_future_date(date: str) -> None:
        if datetime.strptime(date, "%Y-%m-%d").date() < datetime.utcnow().date():
            raise HTTPException(status_code=400, detail="Appointment date must be in the future")

    @staticmethod
    def create(db: Session, patient: User, data: AppointmentCreate) -> Appointment:
        doctor = db.query(DoctorProfile).filter(DoctorProfile.id == data.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

        AppointmentService._check_future_date(data.appointment_date)
        AppointmentService._check_working_hours(doctor, data.appointment_time)
        AppointmentService._check_slot(db, data.doctor_id, data.appointment_date, data.appointment_time)

        appt = Appointment(
            patient_id=patient.id,
            doctor_id=data.doctor_id,
            appointment_date=data.appointment_date,
            appointment_time=data.appointment_time,
            reason=data.reason,
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)
        return appt

    @staticmethod
    def update_status(
        db: Session,
        appointment_id: int,
        data: AppointmentStatusUpdate,
        current_user: User,
    ) -> Appointment:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if current_user.role == UserRole.patient:
            if appt.patient_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not your appointment")
            if data.status != AppointmentStatus.rejected:
                raise HTTPException(status_code=403, detail="Patients can only cancel appointments")
        elif current_user.role == UserRole.doctor:
            doctor = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user.id).first()
            if not doctor or appt.doctor_id != doctor.id:
                raise HTTPException(status_code=403, detail="Not your appointment")

        appt.status = data.status
        if data.notes:
            appt.notes = data.notes
        db.commit()
        db.refresh(appt)
        return appt

    @staticmethod
    def list_appointments(
        db: Session,
        current_user: User,
        status: Optional[AppointmentStatus] = None,
        date: Optional[str] = None,
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "appointment_date",
        order: str = "asc",
    ) -> Tuple[List[Appointment], int]:
        query = db.query(Appointment)

        # Scope results by role
        if current_user.role == UserRole.patient:
            query = query.filter(Appointment.patient_id == current_user.id)
        elif current_user.role == UserRole.doctor:
            doctor = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user.id).first()
            if doctor:
                query = query.filter(Appointment.doctor_id == doctor.id)

        if status:
            query = query.filter(Appointment.status == status)
        if date:
            query = query.filter(Appointment.appointment_date == date)
        if patient_id and current_user.role == UserRole.admin:
            query = query.filter(Appointment.patient_id == patient_id)
        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)

        total = query.count()
        sort_col = getattr(Appointment, sort_by, Appointment.appointment_date)
        if order == "desc":
            sort_col = sort_col.desc()
        items = query.order_by(sort_col).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, appointment_id: int, current_user: User) -> Appointment:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")
        if current_user.role == UserRole.patient and appt.patient_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        return appt
