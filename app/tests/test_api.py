import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# ── Test DB ───────────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test_hospital.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def register_and_login(client, email, password="password123", role="patient") -> str:
    client.post("/api/auth/register", json={
        "full_name": "Test User",
        "email": email,
        "password": password,
        "role": role,
    })
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["data"]["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ────────────────────────────────────────────────────────────────

class TestAuth:

    def test_register_success(self, client):
        res = client.post("/api/auth/register", json={
            "full_name": "Alice", "email": "alice@test.com",
            "password": "password123", "role": "patient",
        })
        assert res.status_code == 200
        assert res.json()["success"] is True

    def test_register_duplicate(self, client):
        data = {"full_name": "Bob", "email": "bob@test.com", "password": "password123", "role": "patient"}
        client.post("/api/auth/register", json=data)
        res = client.post("/api/auth/register", json=data)
        assert res.status_code == 400

    def test_register_weak_password(self, client):
        res = client.post("/api/auth/register", json={
            "full_name": "Dan", "email": "dan@test.com", "password": "123", "role": "patient",
        })
        assert res.status_code == 422

    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "full_name": "Carol", "email": "carol@test.com",
            "password": "password123", "role": "patient",
        })
        res = client.post("/api/auth/login", json={"email": "carol@test.com", "password": "password123"})
        assert res.status_code == 200
        assert "access_token" in res.json()["data"]

    def test_login_wrong_password(self, client):
        res = client.post("/api/auth/login", json={"email": "carol@test.com", "password": "wrong"})
        assert res.status_code == 401

    def test_forgot_password(self, client):
        res = client.post("/api/auth/forgot-password", json={"email": "carol@test.com"})
        assert res.status_code == 200
        assert "reset_token" in res.json()["data"]

    def test_reset_password(self, client):
        r = client.post("/api/auth/forgot-password", json={"email": "carol@test.com"})
        token = r.json()["data"]["reset_token"]
        res = client.post("/api/auth/reset-password", json={
            "token": token, "new_password": "newpassword123",
        })
        assert res.status_code == 200
        assert res.json()["success"] is True


# ── Doctor Tests ──────────────────────────────────────────────────────────────

class TestDoctors:

    def test_create_profile_as_doctor(self, client):
        token = register_and_login(client, "dr.smith@test.com", role="doctor")
        res = client.post("/api/doctors/profile", json={
            "specialization": "Cardiology",
            "experience_years": 5,
            "consultation_fee": 500.0,
            "available_from": "09:00",
            "available_to": "17:00",
        }, headers=auth(token))
        assert res.status_code == 200

    def test_create_profile_as_patient_fails(self, client):
        token = register_and_login(client, "patient2@test.com")
        res = client.post("/api/doctors/profile", json={
            "specialization": "Cardiology",
        }, headers=auth(token))
        assert res.status_code == 403

    def test_list_doctors(self, client):
        res = client.get("/api/doctors/")
        assert res.status_code == 200
        assert "data" in res.json()

    def test_search_doctors(self, client):
        res = client.get("/api/doctors/?search=smith")
        assert res.status_code == 200

    def test_filter_by_specialization(self, client):
        res = client.get("/api/doctors/?specialization=Cardiology")
        assert res.status_code == 200
        for doc in res.json()["data"]:
            assert "cardiology" in doc["specialization"].lower()


# ── Appointment Tests ─────────────────────────────────────────────────────────

class TestAppointments:

    def _setup_doctor(self, client) -> int:
        """Register a doctor, create profile, return doctor profile id."""
        token = register_and_login(client, "dr.jones@test.com", role="doctor")
        client.post("/api/doctors/profile", json={
            "specialization": "Neurology",
            "experience_years": 3,
            "consultation_fee": 400.0,
            "available_from": "08:00",
            "available_to": "18:00",
        }, headers=auth(token))
        docs = client.get("/api/doctors/").json()["data"]
        return docs[-1]["id"]

    def test_book_appointment(self, client):
        doctor_id = self._setup_doctor(client)
        token = register_and_login(client, "patient3@test.com")
        res = client.post("/api/appointments/", json={
            "doctor_id": doctor_id,
            "appointment_date": "2027-06-15",
            "appointment_time": "10:00",
            "reason": "Headache",
        }, headers=auth(token))
        assert res.status_code == 200

    def test_double_booking_prevented(self, client):
        docs = client.get("/api/doctors/").json()["data"]
        doctor_id = docs[-1]["id"]
        p1 = register_and_login(client, "patient4@test.com")
        p2 = register_and_login(client, "patient4b@test.com")
        payload = {"doctor_id": doctor_id, "appointment_date": "2027-07-01", "appointment_time": "11:00"}
        assert client.post("/api/appointments/", json=payload, headers=auth(p1)).status_code == 200
        assert client.post("/api/appointments/", json=payload, headers=auth(p2)).status_code == 409

    def test_past_date_rejected(self, client):
        docs = client.get("/api/doctors/").json()["data"]
        doctor_id = docs[-1]["id"]
        token = register_and_login(client, "patient5@test.com")
        res = client.post("/api/appointments/", json={
            "doctor_id": doctor_id,
            "appointment_date": "2020-01-01",
            "appointment_time": "10:00",
        }, headers=auth(token))
        assert res.status_code == 400

    def test_list_appointments_with_filter(self, client):
        token = register_and_login(client, "patient6@test.com")
        res = client.get("/api/appointments/?status=pending", headers=auth(token))
        assert res.status_code == 200


# ── Admin Tests ───────────────────────────────────────────────────────────────

class TestAdmin:

    def test_list_users_as_admin(self, client):
        token = register_and_login(client, "admin@test.com", role="admin")
        res = client.get("/api/admin/users", headers=auth(token))
        assert res.status_code == 200

    def test_list_users_as_patient_fails(self, client):
        token = register_and_login(client, "patienta@test.com")
        res = client.get("/api/admin/users", headers=auth(token))
        assert res.status_code == 403

    def test_deactivate_and_activate_user(self, client):
        admin_token = register_and_login(client, "admin2@test.com", role="admin")
        # Register a target user
        client.post("/api/auth/register", json={
            "full_name": "Target", "email": "target@test.com",
            "password": "password123", "role": "patient",
        })
        users = client.get("/api/admin/users", headers=auth(admin_token)).json()["data"]
        target = next(u for u in users if u["email"] == "target@test.com")

        res = client.patch(f"/api/admin/users/{target['id']}/deactivate", headers=auth(admin_token))
        assert res.status_code == 200

        res = client.patch(f"/api/admin/users/{target['id']}/activate", headers=auth(admin_token))
        assert res.status_code == 200


# ── Health Tests ──────────────────────────────────────────────────────────────

class TestHealth:

    def test_root(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert res.json()["success"] is True

    def test_health(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["success"] is True
