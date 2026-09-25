from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


client = TestClient(app)


def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def register_admin():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Technician Admin",
            "email": "technician_admin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert response.status_code in (201, 409)

    login = client.post(
        "/auth/login",
        json={
            "email": "technician_admin@example.com",
            "password": "Admin@12345",
        },
    )

    assert login.status_code == 200

    return {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }


def create_technician(
    headers,
    employee_id="TECH-001",
    name="Ravi Technician",
):
    return client.post(
        "/technicians",
        headers=headers,
        json={
            "name": name,
            "employee_id": employee_id,
            "phone": "9876543210",
            "specialization": "Meter Installation",
            "availability_status": "Available",
        },
    )


def test_create_technician():
    setup_database()

    headers = register_admin()

    response = create_technician(headers)

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["name"] == "Ravi Technician"
    assert data["employee_id"] == "TECH-001"
    assert data["phone"] == "9876543210"
    assert data["specialization"] == "Meter Installation"
    assert data["availability_status"] == "Available"


def test_get_technician():
    setup_database()

    headers = register_admin()

    create_response = create_technician(headers)

    assert create_response.status_code == 201

    technician_id = create_response.json()["id"]

    response = client.get(
        f"/technicians/{technician_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == technician_id
    assert data["employee_id"] == "TECH-001"


def test_get_technicians():
    setup_database()

    headers = register_admin()

    first = create_technician(
        headers,
        employee_id="TECH-001",
        name="Ravi Technician",
    )

    second = create_technician(
        headers,
        employee_id="TECH-002",
        name="Suresh Technician",
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        "/technicians",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2


def test_update_technician_availability():
    setup_database()

    headers = register_admin()

    create_response = create_technician(headers)

    assert create_response.status_code == 201

    technician_id = create_response.json()["id"]

    response = client.put(
        f"/technicians/{technician_id}/availability",
        headers=headers,
        json={
            "availability_status": "Busy",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == technician_id
    assert data["availability_status"] == "Busy"


def test_update_technician_to_unavailable():
    setup_database()

    headers = register_admin()

    create_response = create_technician(headers)

    assert create_response.status_code == 201

    technician_id = create_response.json()["id"]

    response = client.put(
        f"/technicians/{technician_id}/availability",
        headers=headers,
        json={
            "availability_status": "Unavailable",
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["availability_status"]
        == "Unavailable"
    )


def test_filter_technicians_by_availability():
    setup_database()

    headers = register_admin()

    first = create_technician(
        headers,
        employee_id="TECH-001",
        name="Available Technician",
    )

    assert first.status_code == 201

    second = create_technician(
        headers,
        employee_id="TECH-002",
        name="Busy Technician",
    )

    assert second.status_code == 201

    second_id = second.json()["id"]

    update = client.put(
        f"/technicians/{second_id}/availability",
        headers=headers,
        json={
            "availability_status": "Busy",
        },
    )

    assert update.status_code == 200

    response = client.get(
        "/technicians",
        headers=headers,
        params={
            "availability_status": "Available",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["employee_id"] == "TECH-001"
    assert data[0]["availability_status"] == "Available"


def test_filter_technicians_by_specialization():
    setup_database()

    headers = register_admin()

    first = client.post(
        "/technicians",
        headers=headers,
        json={
            "name": "Meter Technician",
            "employee_id": "TECH-001",
            "phone": "9876543210",
            "specialization": "Meter Installation",
            "availability_status": "Available",
        },
    )

    assert first.status_code == 201

    second = client.post(
        "/technicians",
        headers=headers,
        json={
            "name": "Connection Technician",
            "employee_id": "TECH-002",
            "phone": "9876543211",
            "specialization": "Connection Inspection",
            "availability_status": "Available",
        },
    )

    assert second.status_code == 201

    response = client.get(
        "/technicians",
        headers=headers,
        params={
            "specialization": "Meter Installation",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["specialization"] == "Meter Installation"


def test_duplicate_employee_id_rejected():
    setup_database()

    headers = register_admin()

    first = create_technician(
        headers,
        employee_id="TECH-001",
        name="First Technician",
    )

    assert first.status_code == 201

    second = create_technician(
        headers,
        employee_id="TECH-001",
        name="Second Technician",
    )

    assert second.status_code == 409

    assert second.json()["detail"] == (
        "Employee ID already exists"
    )


def test_nonexistent_technician():
    setup_database()

    headers = register_admin()

    response = client.get(
        "/technicians/999999",
        headers=headers,
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Technician not found"
    )


def test_nonexistent_technician_availability_update():
    setup_database()

    headers = register_admin()

    response = client.put(
        "/technicians/999999/availability",
        headers=headers,
        json={
            "availability_status": "Busy",
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Technician not found"
    )


def test_invalid_availability_status():
    setup_database()

    headers = register_admin()

    response = create_technician(headers)

    assert response.status_code == 201

    technician_id = response.json()["id"]

    update = client.put(
        f"/technicians/{technician_id}/availability",
        headers=headers,
        json={
            "availability_status": "On Leave",
        },
    )

    assert update.status_code == 422


def test_technician_creation_requires_authorized_role():
    setup_database()

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Customer User",
            "email": "technician_customer@example.com",
            "password": "Customer@12345",
            "role": "Customer",
        },
    )

    assert register_response.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": "technician_customer@example.com",
            "password": "Customer@12345",
        },
    )

    assert login.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }

    response = client.post(
        "/technicians",
        headers=headers,
        json={
            "name": "Unauthorized Technician",
            "employee_id": "TECH-999",
            "phone": "9876543210",
            "specialization": "Meter Installation",
            "availability_status": "Available",
        },
    )

    assert response.status_code == 403