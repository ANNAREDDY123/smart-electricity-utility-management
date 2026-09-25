from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.bill import Bill, BillStatus
from app.models.connection import (
    Connection,
    ConnectionStatus,
    ConnectionType,
)
from app.models.customer import Customer, CustomerStatus
from app.models.meter import Meter, MeterStatus
from app.models.meter_reading import (
    MeterReading,
    ReadingSource,
)
from app.models.tariff import Tariff, TariffStatus


client = TestClient(app)


def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_admin():
    setup_database()

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Analytics Admin",
            "email": "analytics.admin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "analytics.admin@example.com",
            "password": "Admin@12345",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def create_customer(
    headers,
    customer_number="AN-CUST-001",
    email="analytics.customer@example.com",
):
    response = client.post(
        "/customers",
        headers=headers,
        json={
            "customer_number": customer_number,
            "full_name": "Analytics Customer",
            "email": email,
            "phone": "9876543210",
            "address": "Hyderabad",
            "city": "Hyderabad",
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_connection(
    headers,
    customer_id,
    connection_number="AN-CONN-001",
):
    response = client.post(
        "/connections",
        headers=headers,
        json={
            "customer_id": customer_id,
            "connection_number": connection_number,
            "connection_type": "Residential",
            "sanctioned_load": 5,
            "tariff_type": "Residential",
            "connection_date": "2026-01-01",
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_bill(
    db,
    connection_id,
    billing_month,
    units_consumed,
    total_amount,
):
    bill = Bill(
        connection_id=connection_id,
        billing_month=billing_month,
        units_consumed=Decimal(str(units_consumed)),
        energy_charge=Decimal(str(total_amount)),
        fixed_charge=Decimal("0.00"),
        tax=Decimal("0.00"),
        late_fee=Decimal("0.00"),
        discount=Decimal("0.00"),
        total_amount=Decimal(str(total_amount)),
        due_date=date(2026, 12, 31),
        bill_status=BillStatus.GENERATED,
    )

    db.add(bill)
    db.commit()
    db.refresh(bill)

    return bill


def seed_analytics_data(headers):
    customer = create_customer(headers)

    connection = create_connection(
        headers,
        customer["id"],
    )

    db = SessionLocal()

    try:
        create_bill(
            db=db,
            connection_id=connection["id"],
            billing_month="2026-01",
            units_consumed=100,
            total_amount=600,
        )

        create_bill(
            db=db,
            connection_id=connection["id"],
            billing_month="2026-02",
            units_consumed=150,
            total_amount=850,
        )

        create_bill(
            db=db,
            connection_id=connection["id"],
            billing_month="2026-03",
            units_consumed=200,
            total_amount=1100,
        )
    finally:
        db.close()

    return customer, connection


def test_monthly_consumption_for_connection():
    headers = create_admin()

    customer, connection = seed_analytics_data(
        headers
    )

    response = client.get(
        f"/analytics/connections/{connection['id']}/monthly",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3

    assert data[0]["month"] == "2026-01"
    assert float(data[0]["units_consumed"]) == 100
    assert float(data[0]["bill_amount"]) == 600

    assert data[1]["month"] == "2026-02"
    assert float(data[1]["units_consumed"]) == 150
    assert float(data[1]["bill_amount"]) == 850

    assert data[2]["month"] == "2026-03"
    assert float(data[2]["units_consumed"]) == 200
    assert float(data[2]["bill_amount"]) == 1100


def test_yearly_consumption_for_connection():
    headers = create_admin()

    customer, connection = seed_analytics_data(
        headers
    )

    response = client.get(
        f"/analytics/connections/{connection['id']}/yearly",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0]["year"] == 2026
    assert float(data[0]["units_consumed"]) == 450
    assert float(data[0]["bill_amount"]) == 2550


def test_connection_wise_usage():
    headers = create_admin()

    customer, connection = seed_analytics_data(
        headers
    )

    response = client.get(
        "/analytics/connections/usage",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0]["connection_id"] == connection["id"]
    assert data[0]["connection_number"] == "AN-CONN-001"
    assert float(data[0]["units_consumed"]) == 450
    assert float(data[0]["bill_amount"]) == 2550


def test_customer_wise_usage():
    headers = create_admin()

    customer, connection = seed_analytics_data(
        headers
    )

    response = client.get(
        "/analytics/customers/usage",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0]["customer_id"] == customer["id"]
    assert data[0]["customer_number"] == "AN-CUST-001"
    assert data[0]["customer_name"] == "Analytics Customer"
    assert float(data[0]["units_consumed"]) == 450
    assert float(data[0]["bill_amount"]) == 2550


def test_highest_consuming_connections():
    headers = create_admin()

    customer_1 = create_customer(
        headers,
        customer_number="AN-CUST-001",
        email="analytics.customer1@example.com",
    )

    connection_1 = create_connection(
        headers,
        customer_1["id"],
        connection_number="AN-CONN-001",
    )

    customer_2 = create_customer(
        headers,
        customer_number="AN-CUST-002",
        email="analytics.customer2@example.com",
    )

    connection_2 = create_connection(
        headers,
        customer_2["id"],
        connection_number="AN-CONN-002",
    )

    db = SessionLocal()

    try:
        create_bill(
            db=db,
            connection_id=connection_1["id"],
            billing_month="2026-01",
            units_consumed=100,
            total_amount=600,
        )

        create_bill(
            db=db,
            connection_id=connection_2["id"],
            billing_month="2026-01",
            units_consumed=500,
            total_amount=2500,
        )
    finally:
        db.close()

    response = client.get(
        "/analytics/connections/highest-consumption?limit=2",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["connection_id"] == connection_2["id"]
    assert float(data[0]["units_consumed"]) == 500

    assert data[1]["connection_id"] == connection_1["id"]
    assert float(data[1]["units_consumed"]) == 100


def test_average_monthly_consumption():
    headers = create_admin()

    customer, connection = seed_analytics_data(
        headers
    )

    response = client.get(
        "/analytics/consumption/average-monthly",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert float(
        data["average_monthly_consumption"]
    ) == 150


def test_invalid_connection_returns_404():
    headers = create_admin()

    response = client.get(
        "/analytics/connections/999999/monthly",
        headers=headers,
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Connection not found"
    )


def test_analytics_requires_authentication():
    response = client.get(
        "/analytics/connections/1/monthly"
    )

    assert response.status_code == 401