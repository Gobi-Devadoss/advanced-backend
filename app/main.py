from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine, Base
from app.models import User, DoctorProfile, Appointment, FileMetadata  # register models
from app.routers import auth, doctors, appointments, files, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hospital Management API",
    version="2.0.0",
    description="Production-grade hospital appointment booking backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(files.router)
app.include_router(admin.router)


@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "message": "Database error", "data": None},
    )


@app.get("/", tags=["Health"])
def root():
    return {"success": True, "message": "Hospital Management API v2.0 is running 🏥"}


@app.get("/health", tags=["Health"])
def health():
    return {"success": True, "message": "OK"}
