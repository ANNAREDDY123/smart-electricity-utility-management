from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


client = TestClient(app)


# ============================================================
# DATABASE SETUP
# ============================================================

def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ============================================================
# AUTHENTICATION HELPERS
# ============================================================

def create_admin():
    setup_database()

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Meter Reading Admin",
            "email": "meterreadingadmin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "meterreadingadmin@example.com",
            "password": "Admin@12345",
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data

    return data["access_token"]


def create_customer_user():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Meter Reading Customer User",
            "email": "meterreadingcustomer@example.com",
            "password": "Customer@12345",
            "role": "Customer",
        },
    )

    assert response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "meterreadingcustomer@example.com",
            "password": "Customer@12345",
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data

    return data["access_token"]


# ============================================================
# CUSTOMER HELPER
# ============================================================

def create_customer(
    token: str,
    customer_number: str = "MTR-CUST-001",
    email: str = "meterreadingcustomerdata@example.com",
):
    response = client.post(
        "/customers",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_number": customer_number,
            "full_name": "Meter Reading Customer",
            "email": email,
            "phone": "9876543210",
            "address": "Hyderabad",
            "city": "Hyderabad",
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


# ============================================================
# CONNECTION HELPER
# ============================================================

def create_connection(
    token: str,
    customer_id: int,
    connection_number: str = "MTR-CON-001",
):
    response = client.post(
        "/connections",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_id": customer_id,
            "connection_number": connection_number,
            "connection_type": "Residential",
            "sanctioned_load": 5,
            "tariff_type": "Domestic",
            "connection_date": str(date.today()),
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


# ============================================================
# METER HELPER
# ============================================================

def create_meter(
    token: str,
    connection_id: int,
    meter_number: str = "MTR-001",
    meter_type: str = "Smart Meter",
    initial_reading: int = 100,
    current_reading: int = 100,
):
    response = client.post(
        "/meters",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "connection_id": connection_id,
            "meter_number": meter_number,
            "meter_type": meter_type,
            "installation_date": str(date.today()),
            "initial_reading": initial_reading,
            "current_reading": current_reading,
            "meter_status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


# ============================================================
# READING HELPER
# ============================================================

def create_reading(
    token: str,
    meter_id: int,
    reading_date: str = "2026-09-15",
    previous_reading: int = 100,
    current_reading: int = 150,
    source: str = "Manual",
):
    return client.post(
        "/meter-readings",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "meter_id": meter_id,
            "reading_date": reading_date,
            "previous_reading": previous_reading,
            "current_reading": current_reading,
            "reading_source": source,
            "remarks": "Test meter reading",
        },
    )


# ============================================================
# 1. CREATE READING
# ============================================================

def test_create_meter_reading():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    meter = create_meter(
        token,
        connection["id"],
    )

    response = create_reading(
        token,
        meter["id"],
    )

    assert response.status_code == 201


# ============================================================
# 2. GET READING
# ============================================================

def test_get_meter_reading():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    meter = create_meter(
        token,
        connection["id"],
    )

    create_response = create_reading(
        token,
        meter["id"],
    )

    assert create_response.status_code == 201

    reading_id = create_response.json()["id"]

    response = client.get(
        f"/meter-readings/{reading_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == reading_id
    assert data["meter_id"] == meter["id"]


# ============================================================
# 3. UNITS CONSUMED CALCULATION
# ============================================================

def test_units_consumed_calculation():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-UNITS-001",
        initial_reading=1000,
        current_reading=1000,
    )

    response = create_reading(
        token,
        meter["id"],
        previous_reading=1000,
        current_reading=1275,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["units_consumed"] == "275.00"


# ============================================================
# 4. CURRENT < PREVIOUS
# ============================================================

def test_current_reading_less_than_previous():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-VALIDATION-001",
        initial_reading=100,
        current_reading=100,
    )

    response = create_reading(
        token,
        meter["id"],
        previous_reading=200,
        current_reading=150,
    )

    assert response.status_code == 422


# ============================================================
# 5. READING CANNOT DECREASE
# ============================================================

def test_reading_cannot_decrease_from_latest_reading():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-DECREASE-001",
        initial_reading=100,
        current_reading=100,
    )

    first_response = create_reading(
        token,
        meter["id"],
        reading_date="2026-09-10",
        previous_reading=100,
        current_reading=200,
    )

    assert first_response.status_code == 201

    second_response = create_reading(
        token,
        meter["id"],
        reading_date="2026-10-10",
        previous_reading=200,
        current_reading=150,
    )

    assert second_response.status_code == 422


# ============================================================
# 6. DUPLICATE BILLING PERIOD
# ============================================================

def test_duplicate_billing_period_rejected():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-DUPLICATE-001",
        initial_reading=100,
        current_reading=100,
    )

    first_response = create_reading(
        token,
        meter["id"],
        reading_date="2026-09-10",
        previous_reading=100,
        current_reading=150,
    )

    assert first_response.status_code == 201

    second_response = create_reading(
        token,
        meter["id"],
        reading_date="2026-09-20",
        previous_reading=150,
        current_reading=180,
    )

    assert second_response.status_code == 409


# ============================================================
# 7. FAULTY METER
# ============================================================

def test_faulty_meter_cannot_receive_reading():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-FAULTY-001",
    )

    update_response = client.put(
        f"/meters/{meter['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "meter_status": "Faulty",
        },
    )

    assert update_response.status_code == 200

    response = create_reading(
        token,
        meter["id"],
    )

    assert response.status_code == 400


# ============================================================
# 8. REMOVED METER
# ============================================================

def test_removed_meter_cannot_receive_reading():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-REMOVED-001",
    )

    replacement_response = client.post(
        f"/meters/{meter['id']}/replace",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "meter_number": "MTR-REPLACEMENT-001",
            "meter_type": "Smart Meter",
            "installation_date": "2026-09-20",
            "initial_reading": 0,
            "current_reading": 0,
        },
    )

    assert replacement_response.status_code == 200

    response = create_reading(
        token,
        meter["id"],
    )

    assert response.status_code == 400


# ============================================================
# 9. METER CURRENT READING UPDATE
# ============================================================

def test_meter_current_reading_is_updated():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
        connection_number="MTR-CON-UPDATE-001",
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-UPDATE-001",
        initial_reading=500,
        current_reading=500,
    )

    response = create_reading(
        token,
        meter["id"],
        previous_reading=500,
        current_reading=650,
    )

    assert response.status_code == 201

    meter_response = client.get(
        f"/meters/{meter['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert meter_response.status_code == 200

    meter_data = meter_response.json()

    assert meter_data["current_reading"] == "650.00"


# ============================================================
# 10. LIST METER READINGS
# ============================================================

def test_list_meter_readings():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
        connection_number="MTR-CON-LIST-001",
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-LIST-001",
        initial_reading=100,
        current_reading=100,
    )

    first = create_reading(
        token,
        meter["id"],
        reading_date="2026-09-10",
        previous_reading=100,
        current_reading=150,
    )

    assert first.status_code == 201

    second = create_reading(
        token,
        meter["id"],
        reading_date="2026-10-10",
        previous_reading=150,
        current_reading=220,
    )

    assert second.status_code == 201

    response = client.get(
        f"/meter-readings/meter/{meter['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


# ============================================================
# 11. CONNECTION READING HISTORY
# ============================================================

def test_list_connection_readings():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
        connection_number="MTR-CON-HISTORY-001",
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-HISTORY-001",
    )

    response = create_reading(
        token,
        meter["id"],
    )

    assert response.status_code == 201

    history_response = client.get(
        f"/meter-readings/connection/{connection['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert history_response.status_code == 200

    data = history_response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["meter_id"] == meter["id"]


# ============================================================
# 12. PAGINATION
# ============================================================

def test_meter_reading_pagination():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
        connection_number="MTR-CON-PAGE-001",
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-PAGE-001",
        initial_reading=100,
        current_reading=100,
    )

    first = create_reading(
        token,
        meter["id"],
        reading_date="2026-09-01",
        previous_reading=100,
        current_reading=110,
    )

    assert first.status_code == 201

    second = create_reading(
        token,
        meter["id"],
        reading_date="2026-10-01",
        previous_reading=110,
        current_reading=125,
    )

    assert second.status_code == 201

    response = client.get(
        f"/meter-readings/meter/{meter['id']}?page=1&limit=1",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["page"] == 1
    assert data["limit"] == 1
    assert len(data["items"]) == 1


# ============================================================
# 13. SORTING
# ============================================================

def test_meter_reading_sorting_ascending():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
        connection_number="MTR-CON-SORT-001",
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-SORT-001",
        initial_reading=100,
        current_reading=100,
    )

    first = create_reading(
        token,
        meter["id"],
        reading_date="2026-10-01",
        previous_reading=100,
        current_reading=200,
    )

    assert first.status_code == 201

    second = create_reading(
        token,
        meter["id"],
        reading_date="2026-11-01",
        previous_reading=200,
        current_reading=300,
    )

    assert second.status_code == 201

    response = client.get(
        f"/meter-readings/meter/{meter['id']}?"
        "sort_by=reading_date&sort_order=asc",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["billing_period"] == "2026-10"
    assert data["items"][1]["billing_period"] == "2026-11"


# ============================================================
# 14. SMART METER SOURCE
# ============================================================

def test_smart_meter_reading_source():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
        connection_number="MTR-CON-SMART-001",
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-SMART-001",
    )

    response = create_reading(
        token,
        meter["id"],
        source="Smart Meter",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["reading_source"] == "Smart Meter"


# ============================================================
# 15. FIELD TECHNICIAN SOURCE
# ============================================================

def test_field_technician_reading_source():
    token = create_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
        connection_number="MTR-CON-TECH-001",
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-TECH-001",
    )

    response = create_reading(
        token,
        meter["id"],
        source="Field Technician",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["reading_source"] == "Field Technician"


# ============================================================
# 16. NON-EXISTENT METER
# ============================================================

def test_create_reading_for_nonexistent_meter():
    token = create_admin()

    response = create_reading(
        token,
        meter_id=999999,
    )

    assert response.status_code == 404


# ============================================================
# 17. NON-EXISTENT READING
# ============================================================

def test_get_nonexistent_reading():
    token = create_admin()

    response = client.get(
        "/meter-readings/999999",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


# ============================================================
# 18. CUSTOMER CANNOT CREATE READING
# ============================================================

def test_customer_cannot_create_meter_reading():
    admin_token = create_admin()

    customer = create_customer(
        admin_token,
        customer_number="MTR-CUST-RBAC-001",
        email="meterreadingrbac@example.com",
    )

    connection = create_connection(
        admin_token,
        customer["id"],
        connection_number="MTR-CON-RBAC-001",
    )

    meter = create_meter(
        admin_token,
        connection["id"],
        meter_number="MTR-RBAC-001",
    )

    customer_token = create_customer_user()

    response = create_reading(
        customer_token,
        meter["id"],
    )

    assert response.status_code == 403


# ============================================================
# 19. INVALID PAGINATION
# ============================================================

def test_invalid_pagination():
    token = create_admin()

    customer = create_customer(
        token,
        customer_number="MTR-CUST-PAGE-001",
        email="meterreadingpage@example.com",
    )

    connection = create_connection(
        token,
        customer["id"],
        connection_number="MTR-CON-PAGINATION-001",
    )

    meter = create_meter(
        token,
        connection["id"],
        meter_number="MTR-PAGINATION-001",
    )

    response = client.get(
        f"/meter-readings/meter/{meter['id']}?page=0",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422