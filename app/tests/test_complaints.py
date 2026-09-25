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
            "full_name": "Complaint Admin",
            "email": "complaint_admin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert response.status_code in (201, 409)

    login = client.post(
        "/auth/login",
        json={
            "email": "complaint_admin@example.com",
            "password": "Admin@12345",
        },
    )

    assert login.status_code == 200

    return {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }


def create_customer(headers):
    response = client.post(
        "/customers",
        headers=headers,
        json={
            "customer_number": "COMP-CUST-001",
            "full_name": "Complaint Customer",
            "email": "complaint.customer@example.com",
            "phone": "9876543210",
            "address": "Complaint Street",
            "city": "Hyderabad",
            "status": "Active",
        },
    )

    assert response.status_code == 201, (
        f"Customer creation failed: "
        f"{response.status_code} - {response.text}"
    )

    return response.json()


def create_connection(headers, customer_id):
    response = client.post(
        "/connections",
        headers=headers,
        json={
            "customer_id": customer_id,
            "connection_number": "COMP-CONN-001",
            "connection_type": "Residential",
            "sanctioned_load": 5,
            "tariff_type": "Residential",
            "connection_date": "2026-09-24",
            "status": "Active",
        },
    )

    assert response.status_code == 201, (
        f"Connection creation failed: "
        f"{response.status_code} - {response.text}"
    )

    return response.json()


def create_field_technician():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Complaint Technician",
            "email": "complaint.tech@example.com",
            "password": "Tech@12345",
            "role": "Field Technician",
        },
    )

    assert response.status_code == 201, (
        f"Technician creation failed: "
        f"{response.status_code} - {response.text}"
    )

    return response.json()


# =============================================================
# TEST 1
# CREATE COMPLAINT
# =============================================================

def test_create_complaint():
    setup_database()

    headers = register_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    response = client.post(
        "/complaints",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Power Failure",
            "description": "Power supply is not available.",
            "priority": "High",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer["id"]
    assert data["connection_id"] == connection["id"]
    assert data["complaint_type"] == "Power Failure"
    assert data["priority"] == "High"
    assert data["status"] == "Open"
    assert data["assigned_to"] is None


# =============================================================
# TEST 2
# GET COMPLAINTS
# =============================================================

def test_get_complaints():
    setup_database()

    headers = register_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    client.post(
        "/complaints",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Meter Issue",
            "description": "Meter is not working properly.",
            "priority": "Medium",
        },
    )

    response = client.get(
        "/complaints",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["complaint_type"] == "Meter Issue"


# =============================================================
# TEST 3
# GET COMPLAINT BY ID + HISTORY
# =============================================================

def test_get_complaint_by_id_and_history():
    setup_database()

    headers = register_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    complaint = client.post(
        "/complaints",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Voltage Issue",
            "description": "Voltage fluctuation is occurring.",
            "priority": "High",
        },
    )

    assert complaint.status_code == 201

    complaint_id = complaint.json()["id"]

    response = client.get(
        f"/complaints/{complaint_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == complaint_id
    assert data["status"] == "Open"
    assert "history" in data
    assert len(data["history"]) >= 1

    assert data["history"][0]["new_status"] == "Open"


# =============================================================
# TEST 4
# ASSIGN TECHNICIAN
# =============================================================

def test_assign_technician():
    setup_database()

    headers = register_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    complaint = client.post(
        "/complaints",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Meter Issue",
            "description": "Meter requires inspection.",
            "priority": "High",
        },
    )

    assert complaint.status_code == 201

    technician = create_field_technician()

    response = client.put(
        f"/complaints/{complaint.json()['id']}/assign",
        headers=headers,
        json={
            "assigned_to": technician["id"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["assigned_to"] == technician["id"]
    assert data["status"] == "Assigned"


# =============================================================
# TEST 5
# ONLY FIELD TECHNICIAN CAN BE ASSIGNED
# =============================================================

def test_only_field_technician_can_be_assigned():
    setup_database()

    headers = register_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    complaint = client.post(
        "/complaints",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Connection Issue",
            "description": "Connection inspection required.",
            "priority": "Medium",
        },
    )

    assert complaint.status_code == 201

    response = client.put(
        f"/complaints/{complaint.json()['id']}/assign",
        headers=headers,
        json={
            "assigned_to": 1,
        },
    )

    assert response.status_code == 422


# =============================================================
# TEST 6
# UPDATE STATUS
# =============================================================

def test_update_complaint_status():
    setup_database()

    headers = register_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    complaint = client.post(
        "/complaints",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Power Failure",
            "description": "Power failure at premises.",
            "priority": "Emergency",
        },
    )

    assert complaint.status_code == 201

    technician = create_field_technician()

    assign = client.put(
        f"/complaints/{complaint.json()['id']}/assign",
        headers=headers,
        json={
            "assigned_to": technician["id"],
        },
    )

    assert assign.status_code == 200

    response = client.put(
        f"/complaints/{complaint.json()['id']}/status",
        headers=headers,
        json={
            "status": "In Progress",
            "remarks": "Technician started investigation.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "In Progress"


# =============================================================
# TEST 7
# COMPLAINT HISTORY IS MAINTAINED
# =============================================================

def test_complaint_history_is_maintained():
    setup_database()

    headers = register_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    complaint = client.post(
        "/complaints",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Billing Issue",
            "description": "Bill amount appears incorrect.",
            "priority": "Medium",
        },
    )

    assert complaint.status_code == 201

    complaint_id = complaint.json()["id"]

    technician = create_field_technician()

    assign = client.put(
        f"/complaints/{complaint_id}/assign",
        headers=headers,
        json={
            "assigned_to": technician["id"],
        },
    )

    assert assign.status_code == 200

    status_response = client.put(
        f"/complaints/{complaint_id}/status",
        headers=headers,
        json={
            "status": "In Progress",
            "remarks": "Investigation started.",
        },
    )

    assert status_response.status_code == 200

    response = client.get(
        f"/complaints/{complaint_id}",
        headers=headers,
    )

    assert response.status_code == 200

    history = response.json()["history"]

    assert len(history) >= 3

    statuses = [
        item["new_status"]
        for item in history
    ]

    assert "Open" in statuses
    assert "Assigned" in statuses
    assert "In Progress" in statuses


# =============================================================
# TEST 8
# INVALID CUSTOMER
# =============================================================

def test_invalid_customer():
    setup_database()

    headers = register_admin()

    response = client.post(
        "/complaints",
        headers=headers,
        json={
            "customer_id": 99999,
            "connection_id": 99999,
            "complaint_type": "Other",
            "description": "Invalid customer complaint.",
            "priority": "Low",
        },
    )

    assert response.status_code == 404


# =============================================================
# TEST 9
# INVALID CONNECTION FOR CUSTOMER
# =============================================================

def test_connection_must_belong_to_customer():
    setup_database()

    headers = register_admin()

    customer1 = create_customer(headers)

    customer2 = client.post(
        "/customers",
        headers=headers,
        json={
            "customer_number": "COMP-CUST-002",
            "full_name": "Second Customer",
            "email": "second.customer@example.com",
            "phone": "9876543211",
            "address": "Second Street",
            "city": "Hyderabad",
            "status": "Active",
        },
    )

    assert customer2.status_code == 201

    connection = create_connection(
        headers,
        customer1["id"],
    )

    response = client.post(
        "/complaints",
        headers=headers,
        json={
            "customer_id": customer2.json()["id"],
            "connection_id": connection["id"],
            "complaint_type": "Connection Issue",
            "description": "Connection does not belong to customer.",
            "priority": "Low",
        },
    )

    assert response.status_code == 422


# =============================================================
# TEST 10
# INVALID COMPLAINT ID
# =============================================================

def test_invalid_complaint_id():
    setup_database()

    headers = register_admin()

    response = client.get(
        "/complaints/99999",
        headers=headers,
    )

    assert response.status_code == 404