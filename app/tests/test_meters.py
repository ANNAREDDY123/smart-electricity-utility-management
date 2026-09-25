from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


client = TestClient(app)


def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_admin(client: TestClient):
    setup_database()

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Meter Admin",
            "email": "meteradmin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "meteradmin@example.com",
            "password": "Admin@12345",
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data

    return data["access_token"]


def create_customer(
    client: TestClient,
    token: str,
    email: str = "metercustomer@example.com",
    customer_number: str = "CUST-MTR-001",
):
    response = client.post(
        "/customers",
        json={
            "customer_number": customer_number,
            "full_name": "Meter Customer",
            "email": email,
            "phone": "9876543210",
            "address": "Meter Street",
            "city": "Hyderabad",
            "status": "Active",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    return response.json()


def create_connection(
    client: TestClient,
    token: str,
    customer_id: int,
    connection_number: str = "CONN-MTR-001",
):
    response = client.post(
        "/connections",
        json={
            "customer_id": customer_id,
            "connection_number": connection_number,
            "connection_type": "Residential",
            "sanctioned_load": 5,
            "tariff_type": "Residential",
            "connection_date": str(date.today()),
            "status": "Active",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    return response.json()


def create_meter(
    client: TestClient,
    token: str,
    connection_id: int,
    meter_number: str = "MTR-001",
    meter_type: str = "Smart Meter",
    initial_reading: int = 100,
    current_reading: int = 100,
):
    return client.post(
        "/meters",
        json={
            "connection_id": connection_id,
            "meter_number": meter_number,
            "meter_type": meter_type,
            "installation_date": str(date.today()),
            "initial_reading": initial_reading,
            "current_reading": current_reading,
            "meter_status": "Active",
        },
        headers={"Authorization": f"Bearer {token}"},
    )


def test_create_meter(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    response = create_meter(
        client,
        token,
        connection["id"],
    )

    assert response.status_code == 201

    data = response.json()

    assert data["connection_id"] == connection["id"]
    assert data["meter_number"] == "MTR-001"
    assert data["meter_type"] == "Smart Meter"
    assert data["initial_reading"] == "100.00"
    assert data["current_reading"] == "100.00"
    assert data["meter_status"] == "Active"


def test_get_meter(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    create_response = create_meter(
        client,
        token,
        connection["id"],
    )

    meter_id = create_response.json()["id"]

    response = client.get(
        f"/meters/{meter_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == meter_id
    assert data["meter_number"] == "MTR-001"


def test_list_meters(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    create_meter(
        client,
        token,
        connection["id"],
    )

    response = client.get(
        "/meters",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["meter_number"] == "MTR-001"


def test_filter_meters_by_connection(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    create_meter(
        client,
        token,
        connection["id"],
    )

    response = client.get(
        f"/meters?connection_id={connection['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["connection_id"] == connection["id"]


def test_filter_meters_by_type(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    create_meter(
        client,
        token,
        connection["id"],
        meter_type="Digital Meter",
    )

    response = client.get(
        "/meters?meter_type=Digital%20Meter",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["meter_type"] == "Digital Meter"


def test_filter_meters_by_status(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    create_meter(
        client,
        token,
        connection["id"],
    )

    response = client.get(
        "/meters?meter_status=Active",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["meter_status"] == "Active"


def test_meter_pagination(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection1 = create_connection(
        client,
        token,
        customer["id"],
        "CONN-PAGE-001",
    )

    connection2 = create_connection(
        client,
        token,
        customer["id"],
        "CONN-PAGE-002",
    )

    response1 = create_meter(
        client,
        token,
        connection1["id"],
        "MTR-001",
    )

    response2 = create_meter(
        client,
        token,
        connection2["id"],
        "MTR-002",
    )

    assert response1.status_code == 201
    assert response2.status_code == 201

    response = client.get(
        "/meters?page=1&limit=1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 1
    assert data["total"] == 2
    assert len(data["items"]) == 1


def test_meter_sorting(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection1 = create_connection(
        client,
        token,
        customer["id"],
        "CONN-SORT-001",
    )

    connection2 = create_connection(
        client,
        token,
        customer["id"],
        "CONN-SORT-002",
    )

    response1 = create_meter(
        client,
        token,
        connection1["id"],
        "MTR-002",
    )

    response2 = create_meter(
        client,
        token,
        connection2["id"],
        "MTR-001",
    )

    assert response1.status_code == 201
    assert response2.status_code == 201

    response = client.get(
        "/meters?sort_by=meter_number&sort_order=asc",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["items"][0]["meter_number"] == "MTR-001"
    assert data["items"][1]["meter_number"] == "MTR-002"


def test_update_meter(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    create_response = create_meter(
        client,
        token,
        connection["id"],
    )

    meter_id = create_response.json()["id"]

    response = client.put(
        f"/meters/{meter_id}",
        json={
            "meter_type": "Advanced Smart Meter",
            "current_reading": 150,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["meter_type"] == "Advanced Smart Meter"
    assert data["current_reading"] == "150.00"


def test_meter_reading_cannot_decrease(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    create_response = create_meter(
        client,
        token,
        connection["id"],
        current_reading=200,
    )

    meter_id = create_response.json()["id"]

    response = client.put(
        f"/meters/{meter_id}",
        json={
            "current_reading": 150,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


def test_duplicate_meter_number(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    first_response = create_meter(
        client,
        token,
        connection["id"],
        meter_number="MTR-DUP-001",
    )

    assert first_response.status_code == 201

    second_response = create_meter(
        client,
        token,
        connection["id"],
        meter_number="MTR-DUP-001",
    )

    assert second_response.status_code == 409


def test_multiple_active_meters_not_allowed(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    first_response = create_meter(
        client,
        token,
        connection["id"],
        meter_number="MTR-ACTIVE-001",
    )

    assert first_response.status_code == 201

    second_response = create_meter(
        client,
        token,
        connection["id"],
        meter_number="MTR-ACTIVE-002",
    )

    assert second_response.status_code == 409


def test_faulty_meter_allowed(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    response = client.post(
        "/meters",
        json={
            "connection_id": connection["id"],
            "meter_number": "MTR-FAULTY-001",
            "meter_type": "Smart Meter",
            "installation_date": str(date.today()),
            "initial_reading": 100,
            "current_reading": 100,
            "meter_status": "Faulty",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["meter_status"] == "Faulty"


def test_meter_on_disconnected_connection_not_allowed(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    connection_id = connection["id"]

    disconnect_response = client.patch(
        f"/connections/{connection_id}/disconnect",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert disconnect_response.status_code == 200

    response = create_meter(
        client,
        token,
        connection_id,
        meter_number="MTR-DISCONNECTED-001",
    )

    assert response.status_code == 400


def test_initial_reading_cannot_exceed_current_reading(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    response = create_meter(
        client,
        token,
        connection["id"],
        meter_number="MTR-INVALID-001",
        initial_reading=200,
        current_reading=100,
    )

    assert response.status_code == 400


def test_replace_meter(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    create_response = create_meter(
        client,
        token,
        connection["id"],
        meter_number="MTR-OLD-001",
    )

    assert create_response.status_code == 201

    old_meter_id = create_response.json()["id"]

    response = client.post(
        f"/meters/{old_meter_id}/replace",
        json={
            "new_meter_number": "MTR-NEW-001",
            "meter_type": "Advanced Smart Meter",
            "installation_date": str(date.today()),
            "initial_reading": 0,
            "current_reading": 0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["meter_number"] == "MTR-NEW-001"
    assert data["meter_status"] == "Active"

    old_response = client.get(
        f"/meters/{old_meter_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert old_response.status_code == 200
    assert old_response.json()["meter_status"] == "Removed"


def test_replace_meter_duplicate_number(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection1 = create_connection(
        client,
        token,
        customer["id"],
        "CONN-REPLACE-001",
    )

    connection2 = create_connection(
        client,
        token,
        customer["id"],
        "CONN-REPLACE-002",
    )

    old_response = create_meter(
        client,
        token,
        connection1["id"],
        "MTR-OLD-002",
    )

    assert old_response.status_code == 201

    old_meter_id = old_response.json()["id"]

    existing_response = create_meter(
        client,
        token,
        connection2["id"],
        "MTR-TEMP-002",
    )

    assert existing_response.status_code == 201

    response = client.post(
        f"/meters/{old_meter_id}/replace",
        json={
            "new_meter_number": "MTR-TEMP-002",
            "meter_type": "Smart Meter",
            "installation_date": str(date.today()),
            "initial_reading": 0,
            "current_reading": 0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409


def test_get_nonexistent_meter(client: TestClient):
    token = create_admin(client)

    response = client.get(
        "/meters/99999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_customer_cannot_create_meter(client: TestClient):
    token = create_admin(client)

    customer_email = "metercustomer-role@example.com"
    customer_password = "Test@12345"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Meter Role Customer",
            "email": customer_email,
            "password": customer_password,
            "role": "Customer",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": customer_email,
            "password": customer_password,
        },
    )

    assert login_response.status_code == 200

    customer_token = login_response.json()["access_token"]

    customer = create_customer(
        client,
        token,
        customer_email,
        "CUST-MTR-RBAC-001",
    )

    connection = create_connection(
        client,
        token,
        customer["id"],
        "CONN-MTR-RBAC",
    )

    response = create_meter(
        client,
        customer_token,
        connection["id"],
        "MTR-RBAC-001",
    )

    assert response.status_code == 403


def test_field_technician_can_create_meter(client: TestClient):
    token = create_admin(client)

    technician_email = "metertechnician@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Meter Technician",
            "email": technician_email,
            "password": "Tech@12345",
            "role": "Field Technician",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": technician_email,
            "password": "Tech@12345",
        },
    )

    assert login_response.status_code == 200

    technician_token = login_response.json()["access_token"]

    customer = create_customer(
        client,
        token,
        "technician-customer@example.com",
        "CUST-MTR-TECH-001",
    )

    connection = create_connection(
        client,
        token,
        customer["id"],
        "CONN-MTR-TECH-001",
    )

    response = create_meter(
        client,
        technician_token,
        connection["id"],
        "MTR-TECH-001",
    )

    assert response.status_code == 201


def test_meter_update_status(client: TestClient):
    token = create_admin(client)

    customer = create_customer(client, token)

    connection = create_connection(
        client,
        token,
        customer["id"],
    )

    create_response = create_meter(
        client,
        token,
        connection["id"],
        meter_number="MTR-STATUS-001",
    )

    meter_id = create_response.json()["id"]

    response = client.put(
        f"/meters/{meter_id}",
        json={
            "meter_status": "Faulty",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["meter_status"] == "Faulty"