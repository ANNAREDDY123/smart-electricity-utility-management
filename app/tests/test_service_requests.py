from datetime import date

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


client = TestClient(app)


# ============================================================
# DATABASE SETUP
# ============================================================

def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ============================================================
# AUTHENTICATION
# ============================================================

def create_admin():
    setup_database()

    register = client.post(
        "/auth/register",
        json={
            "full_name": "Service Request Admin",
            "email": "servicerequestadmin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert register.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": "servicerequestadmin@example.com",
            "password": "Admin@12345",
        },
    )

    assert login.status_code == 200

    return {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }


# ============================================================
# CUSTOMER
# ============================================================

def create_customer(headers):
    response = client.post(
        "/customers",
        headers=headers,
        json={
            "customer_number": "SR-CUST-001",
            "full_name": "Service Request Customer",
            "email": "servicerequestcustomer@example.com",
            "phone": "9876543210",
            "address": "Hyderabad",
            "city": "Hyderabad",
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


# ============================================================
# CONNECTION
# ============================================================

def create_connection(headers, customer_id):
    response = client.post(
        "/connections",
        headers=headers,
        json={
            "customer_id": customer_id,
            "connection_number": "SR-CONN-001",
            "connection_type": "Residential",
            "sanctioned_load": 5,
            "tariff_type": "Residential",
            "connection_date": str(date.today()),
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


# ============================================================
# TEST 1 — CREATE REQUEST
# ============================================================

def test_create_service_request():
    headers = create_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "request_type": "Meter Replacement",
            "description": "Meter is faulty and needs replacement.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer["id"]
    assert data["connection_id"] == connection["id"]
    assert data["request_type"] == "Meter Replacement"
    assert data["status"] == "Submitted"


# ============================================================
# TEST 2 — GET ALL REQUESTS
# ============================================================

def test_get_service_requests():
    headers = create_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    create_response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "request_type": "Load Change",
            "description": "Increase sanctioned load.",
            "requested_date": "2026-09-25",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/service-requests",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["request_type"] == "Load Change"


# ============================================================
# TEST 3 — GET REQUEST BY ID
# ============================================================

def test_get_service_request_by_id():
    headers = create_admin()

    customer = create_customer(headers)

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": None,
            "request_type": "New Connection",
            "description": "Request for a new electricity connection.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 201

    request_id = response.json()["id"]

    response = client.get(
        f"/service-requests/{request_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == request_id
    assert data["request_type"] == "New Connection"


# ============================================================
# TEST 4 — APPROVE REQUEST
# ============================================================

def test_approve_service_request():
    headers = create_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "request_type": "Meter Replacement",
            "description": "Replace faulty meter.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 201

    request_id = response.json()["id"]

    response = client.put(
        f"/service-requests/{request_id}/approve",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Approved"


# ============================================================
# TEST 5 — REJECT REQUEST
# ============================================================

def test_reject_service_request():
    headers = create_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "request_type": "Load Change",
            "description": "Request to increase load.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 201

    request_id = response.json()["id"]

    response = client.put(
        f"/service-requests/{request_id}/reject",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Rejected"


# ============================================================
# TEST 6 — COMPLETE REQUEST
# ============================================================

def test_complete_service_request():
    headers = create_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "request_type": "Meter Replacement",
            "description": "Replace damaged electricity meter.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 201

    request_id = response.json()["id"]

    approve = client.put(
        f"/service-requests/{request_id}/approve",
        headers=headers,
    )

    assert approve.status_code == 200
    assert approve.json()["status"] == "Approved"

    complete = client.put(
        f"/service-requests/{request_id}/complete",
        headers=headers,
    )

    assert complete.status_code == 200
    assert complete.json()["status"] == "Completed"


# ============================================================
# TEST 7 — CUSTOMER FILTER
# ============================================================

def test_filter_service_requests_by_customer():
    headers = create_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "request_type": "Address Change",
            "description": "Update service address.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 201

    response = client.get(
        f"/service-requests?customer_id={customer['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["customer_id"] == customer["id"]


# ============================================================
# TEST 8 — STATUS FILTER
# ============================================================

def test_filter_service_requests_by_status():
    headers = create_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "request_type": "Reconnection",
            "description": "Request reconnection of service.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/service-requests?request_status=Submitted",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["status"] == "Submitted"


# ============================================================
# TEST 9 — INVALID CUSTOMER
# ============================================================

def test_create_request_invalid_customer():
    headers = create_admin()

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": 99999,
            "connection_id": None,
            "request_type": "New Connection",
            "description": "Request for new connection.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


# ============================================================
# TEST 10 — INVALID CONNECTION
# ============================================================

def test_create_request_invalid_connection():
    headers = create_admin()

    customer = create_customer(headers)

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": 99999,
            "request_type": "Meter Replacement",
            "description": "Replace electricity meter.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Connection not found"


# ============================================================
# TEST 11 — NEW CONNECTION CANNOT HAVE CONNECTION ID
# ============================================================

def test_new_connection_request_cannot_have_connection_id():
    headers = create_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "request_type": "New Connection",
            "description": "Request for a new connection.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 422


# ============================================================
# TEST 12 — CONNECTION MUST BELONG TO CUSTOMER
# ============================================================

def test_connection_must_belong_to_customer():
    headers = create_admin()

    customer_one = create_customer(headers)

    connection = create_connection(
        headers,
        customer_one["id"],
    )

    customer_two_response = client.post(
        "/customers",
        headers=headers,
        json={
            "customer_number": "SR-CUST-002",
            "full_name": "Second Customer",
            "email": "servicerequestcustomer2@example.com",
            "phone": "9876543211",
            "address": "Hyderabad",
            "city": "Hyderabad",
            "status": "Active",
        },
    )

    assert customer_two_response.status_code == 201

    customer_two = customer_two_response.json()

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer_two["id"],
            "connection_id": connection["id"],
            "request_type": "Meter Replacement",
            "description": "Replace meter.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 409


# ============================================================
# TEST 13 — SUSPENDED CUSTOMER CANNOT CREATE REQUEST
# ============================================================

def test_suspended_customer_cannot_create_request():
    headers = create_admin()

    customer_response = client.post(
        "/customers",
        headers=headers,
        json={
            "customer_number": "SR-CUST-003",
            "full_name": "Suspended Customer",
            "email": "suspendedcustomer@example.com",
            "phone": "9876543212",
            "address": "Hyderabad",
            "city": "Hyderabad",
        },
    )

    assert customer_response.status_code == 201

    customer = customer_response.json()

    # Put the customer into Suspended status.
    # This avoids changing the already-tested Level 2 customer API.
    from app.database import SessionLocal
    from app.models.customer import Customer, CustomerStatus

    db = SessionLocal()

    try:
        db_customer = db.get(Customer, customer["id"])

        assert db_customer is not None

        db_customer.status = CustomerStatus.SUSPENDED

        db.commit()
    finally:
        db.close()

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": None,
            "request_type": "New Connection",
            "description": "Request for new connection.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "Suspended customers cannot create service requests"
    )

# ============================================================
# TEST 14 — CANNOT COMPLETE UNAPPROVED REQUEST
# ============================================================

def test_cannot_complete_unapproved_request():
    headers = create_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "request_type": "Meter Replacement",
            "description": "Replace electricity meter.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 201

    request_id = response.json()["id"]

    response = client.put(
        f"/service-requests/{request_id}/complete",
        headers=headers,
    )

    assert response.status_code == 409


# ============================================================
# TEST 15 — CANNOT APPROVE REJECTED REQUEST
# ============================================================

def test_cannot_approve_rejected_request():
    headers = create_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "request_type": "Load Change",
            "description": "Change sanctioned load.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 201

    request_id = response.json()["id"]

    reject = client.put(
        f"/service-requests/{request_id}/reject",
        headers=headers,
    )

    assert reject.status_code == 200

    approve = client.put(
        f"/service-requests/{request_id}/approve",
        headers=headers,
    )

    assert approve.status_code == 409


# ============================================================
# TEST 16 — CANNOT REJECT COMPLETED REQUEST
# ============================================================

def test_cannot_reject_completed_request():
    headers = create_admin()

    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    response = client.post(
        "/service-requests",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "request_type": "Meter Replacement",
            "description": "Replace meter.",
            "requested_date": "2026-09-25",
        },
    )

    assert response.status_code == 201

    request_id = response.json()["id"]

    approve = client.put(
        f"/service-requests/{request_id}/approve",
        headers=headers,
    )

    assert approve.status_code == 200

    complete = client.put(
        f"/service-requests/{request_id}/complete",
        headers=headers,
    )

    assert complete.status_code == 200

    reject = client.put(
        f"/service-requests/{request_id}/reject",
        headers=headers,
    )

    assert reject.status_code == 409