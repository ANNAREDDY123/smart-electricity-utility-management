from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


client = TestClient(app)


def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def register_admin():
    setup_database()

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Billing Admin",
            "email": "billing-admin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "billing-admin@example.com",
            "password": "Admin@12345",
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def create_customer(token):
    response = client.post(
        "/customers",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "customer_number": "CUST-BILL-001",
            "full_name": "Bill Customer",
            "email": "bill-customer@example.com",
            "phone": "9876543211",
            "address": "Madhapur",
            "city": "Hyderabad",
            "state": "Telangana",
            "pincode": "500081",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_connection(token, customer_id):
    response = client.post(
        "/connections",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "customer_id": customer_id,
            "connection_number": "CONN-BILL-001",
            "connection_type": "Residential",
            "sanctioned_load": 5,
            "tariff_type": "Residential",
            "connection_date": str(date.today()),
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


def generate_bill(
    token,
    connection_id,
    billing_month="2026-09",
):
    return client.post(
        "/bills/generate",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "connection_id": connection_id,
            "billing_month": billing_month,
            "units_consumed": 150,
            "tariff_rate": 5,
            "fixed_charge": 100,
            "tax": 50,
            "late_fee": 0,
            "discount": 25,
            "due_date": "2026-10-10",
        },
    )


# ============================================================
# 1. GENERATE BILL
# ============================================================

def test_generate_bill():
    token = register_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    response = generate_bill(
        token,
        connection["id"],
    )

    assert response.status_code == 201

    data = response.json()

    assert data["connection_id"] == connection["id"]
    assert data["billing_month"] == "2026-09"
    assert data["units_consumed"] == "150.00"
    assert data["energy_charge"] == "750.00"
    assert data["fixed_charge"] == "100.00"
    assert data["tax"] == "50.00"
    assert data["late_fee"] == "0.00"
    assert data["discount"] == "25.00"
    assert data["total_amount"] == "875.00"
    assert data["bill_status"] == "Generated"


# ============================================================
# 2. DUPLICATE BILL
# ============================================================

def test_duplicate_bill_same_month_rejected():
    token = register_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    first_response = generate_bill(
        token,
        connection["id"],
        "2026-09",
    )

    assert first_response.status_code == 201

    second_response = generate_bill(
        token,
        connection["id"],
        "2026-09",
    )

    assert second_response.status_code == 409


# ============================================================
# 3. DIFFERENT MONTH
# ============================================================

def test_different_month_bill_allowed():
    token = register_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    first_response = generate_bill(
        token,
        connection["id"],
        "2026-09",
    )

    assert first_response.status_code == 201

    second_response = generate_bill(
        token,
        connection["id"],
        "2026-10",
    )

    assert second_response.status_code == 201


# ============================================================
# 4. ENERGY CHARGE CALCULATION
# ============================================================

def test_energy_charge_calculation():
    token = register_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    response = client.post(
        "/bills/generate",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "connection_id": connection["id"],
            "billing_month": "2026-11",
            "units_consumed": 200,
            "tariff_rate": 6,
            "fixed_charge": 100,
            "tax": 60,
            "late_fee": 10,
            "discount": 20,
            "due_date": "2026-12-10",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["energy_charge"] == "1200.00"
    assert data["total_amount"] == "1350.00"


# ============================================================
# 5. GET BILL
# ============================================================

def test_get_bill():
    token = register_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    create_response = generate_bill(
        token,
        connection["id"],
        "2026-12",
    )

    assert create_response.status_code == 201

    bill_id = create_response.json()["id"]

    response = client.get(
        f"/bills/{bill_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == bill_id


# ============================================================
# 6. LIST BILLS
# ============================================================

def test_list_bills():
    token = register_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    response = generate_bill(
        token,
        connection["id"],
        "2027-01",
    )

    assert response.status_code == 201

    list_response = client.get(
        "/bills",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert list_response.status_code == 200

    data = list_response.json()

    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


# ============================================================
# 7. CONNECTION BILLS
# ============================================================

def test_connection_bills():
    token = register_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    response = generate_bill(
        token,
        connection["id"],
        "2027-02",
    )

    assert response.status_code == 201

    bills_response = client.get(
        f"/connections/{connection['id']}/bills",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert bills_response.status_code == 200

    data = bills_response.json()

    assert data["total"] >= 1


# ============================================================
# 8. CUSTOMER BILLS
# ============================================================

def test_customer_bills():
    token = register_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    response = generate_bill(
        token,
        connection["id"],
        "2027-03",
    )

    assert response.status_code == 201

    bills_response = client.get(
        f"/customers/{customer['id']}/bills",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert bills_response.status_code == 200

    data = bills_response.json()

    assert data["total"] >= 1


# ============================================================
# 9. DISCONNECTED CONNECTION
# ============================================================

def test_disconnected_connection_cannot_generate_bill():
    token = register_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    disconnect_response = client.patch(
        f"/connections/{connection['id']}/disconnect",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert disconnect_response.status_code == 200

    response = generate_bill(
        token,
        connection["id"],
        "2027-04",
    )

    assert response.status_code == 400


# ============================================================
# 10. BILL AMOUNT MUST BE POSITIVE
# ============================================================

def test_bill_amount_must_be_positive():
    token = register_admin()

    customer = create_customer(token)

    connection = create_connection(
        token,
        customer["id"],
    )

    response = client.post(
        "/bills/generate",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "connection_id": connection["id"],
            "billing_month": "2027-05",
            "units_consumed": 10,
            "tariff_rate": 1,
            "fixed_charge": 0,
            "tax": 0,
            "late_fee": 0,
            "discount": 20,
            "due_date": "2027-06-10",
        },
    )

    assert response.status_code == 422