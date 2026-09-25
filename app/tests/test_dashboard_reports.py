from datetime import date, datetime, timedelta

import pytest

from app.database import Base
from app.models.bill import Bill, BillStatus
from app.models.complaint import (
    Complaint,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintType,
)
from app.models.connection import (
    Connection,
    ConnectionStatus,
    ConnectionType,
)
from app.models.customer import Customer, CustomerStatus
from app.models.meter import Meter, MeterStatus
from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.models.user import User, UserRole


@pytest.fixture(autouse=True)
def reset_database():
    yield


@pytest.fixture
def admin_user(client):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Dashboard Admin",
            "email": "dashboard_admin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert response.status_code == 201

    return response.json()


def login(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "dashboard_admin@example.com",
            "password": "Admin@12345",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def seed_dashboard_data(db):
    customer = Customer(
        customer_number="CUST-DASH-001",
        full_name="Dashboard Customer",
        email="dashboard_customer@example.com",
        phone="9876543210",
        address="Dashboard Address",
        city="Hyderabad",
        status=CustomerStatus.ACTIVE,
    )

    db.add(customer)
    db.flush()

    active_connection = Connection(
        customer_id=customer.id,
        connection_number="CONN-DASH-001",
        connection_type=ConnectionType.RESIDENTIAL,
        sanctioned_load=5,
        tariff_type="Residential",
        connection_date=date.today(),
        status=ConnectionStatus.ACTIVE,
    )

    disconnected_connection = Connection(
        customer_id=customer.id,
        connection_number="CONN-DASH-002",
        connection_type=ConnectionType.COMMERCIAL,
        sanctioned_load=10,
        tariff_type="Commercial",
        connection_date=date.today(),
        status=ConnectionStatus.DISCONNECTED,
    )

    db.add_all(
        [
            active_connection,
            disconnected_connection,
        ]
    )
    db.flush()

    active_meter = Meter(
        connection_id=active_connection.id,
        meter_number="MTR-DASH-001",
        meter_type="Smart",
        installation_date=date.today(),
        initial_reading=100,
        current_reading=250,
        meter_status=MeterStatus.ACTIVE,
    )

    faulty_meter = Meter(
        connection_id=disconnected_connection.id,
        meter_number="MTR-DASH-002",
        meter_type="Smart",
        installation_date=date.today(),
        initial_reading=50,
        current_reading=50,
        meter_status=MeterStatus.FAULTY,
    )

    db.add_all(
        [
            active_meter,
            faulty_meter,
        ]
    )
    db.flush()

    current_month = datetime.now().strftime("%Y-%m")

    bill = Bill(
        connection_id=active_connection.id,
        billing_month=current_month,
        units_consumed=150,
        energy_charge=1500,
        fixed_charge=100,
        tax=160,
        late_fee=0,
        discount=0,
        total_amount=1760,
        due_date=date.today() + timedelta(days=10),
        bill_status=BillStatus.PENDING,
    )

    overdue_bill = Bill(
        connection_id=disconnected_connection.id,
        billing_month="2026-01",
        units_consumed=100,
        energy_charge=1000,
        fixed_charge=100,
        tax=110,
        late_fee=0,
        discount=0,
        total_amount=1210,
        due_date=date.today() - timedelta(days=30),
        bill_status=BillStatus.GENERATED,
    )

    db.add_all(
        [
            bill,
            overdue_bill,
        ]
    )
    db.flush()

    technician = User(
        full_name="Dashboard Technician",
        email="dashboard_technician@example.com",
        password_hash="not-used-in-this-test",
        role=UserRole.FIELD_TECHNICIAN,
        is_active=True,
    )

    db.add(technician)
    db.flush()

    open_complaint = Complaint(
        customer_id=customer.id,
        connection_id=active_connection.id,
        complaint_type=ComplaintType.POWER_FAILURE,
        description="Power failure complaint",
        priority=ComplaintPriority.HIGH,
        assigned_to=technician.id,
        status=ComplaintStatus.IN_PROGRESS,
    )

    resolved_complaint = Complaint(
        customer_id=customer.id,
        connection_id=active_connection.id,
        complaint_type=ComplaintType.METER_ISSUE,
        description="Meter issue complaint",
        priority=ComplaintPriority.MEDIUM,
        assigned_to=technician.id,
        status=ComplaintStatus.RESOLVED,
    )

    db.add_all(
        [
            open_complaint,
            resolved_complaint,
        ]
    )
    db.flush()

    successful_payment = Payment(
        bill_id=bill.id,
        amount=500,
        payment_method=PaymentMethod.UPI,
        transaction_id="TXN-DASH-001",
        payment_date=datetime.now(),
        payment_status=PaymentStatus.SUCCESS,
    )

    db.add(successful_payment)

    db.commit()

    return {
        "customer_id": customer.id,
        "active_connection_id": active_connection.id,
        "disconnected_connection_id": disconnected_connection.id,
        "bill_id": bill.id,
        "overdue_bill_id": overdue_bill.id,
        "technician_id": technician.id,
    }


def test_dashboard_metrics(client, admin_user, db_session):
    token = login(client)

    seed_dashboard_data(db_session)

    response = client.get(
        "/dashboard",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_customers"] == 1
    assert data["active_connections"] == 1
    assert data["disconnected_connections"] == 1
    assert data["total_meters"] == 2
    assert data["faulty_meters"] == 1
    assert data["monthly_units_consumed"] == 150
    assert data["monthly_revenue"] == 1760
    assert data["pending_bills"] == 1
    assert data["overdue_bills"] == 1
    assert data["open_complaints"] == 1
    assert data["resolved_complaints"] == 1


def test_daily_collection_report(client, admin_user, db_session):
    token = login(client)

    seed_dashboard_data(db_session)

    today = str(date.today())

    response = client.get(
        "/reports/daily-collection",
        params={
            "report_date": today,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["collection_date"] == today
    assert data["total_collection"] == 500
    assert data["successful_payments"] == 1


def test_monthly_revenue_report(client, admin_user, db_session):
    token = login(client)

    seed_dashboard_data(db_session)

    current_month = datetime.now().strftime("%Y-%m")

    response = client.get(
        "/reports/monthly-revenue",
        params={
            "billing_month": current_month,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["billing_month"] == current_month
    assert data["total_revenue"] == 1760
    assert data["total_bills"] == 1
    assert data["total_units_consumed"] == 150


def test_customer_billing_report(client, admin_user, db_session):
    token = login(client)

    seed_dashboard_data(db_session)

    response = client.get(
        "/reports/customers/billing",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    customer = data[0]

    assert customer["customer_number"] == "CUST-DASH-001"
    assert customer["customer_name"] == "Dashboard Customer"
    assert customer["total_bills"] == 2
    assert customer["total_units_consumed"] == 250
    assert customer["total_billed_amount"] == 2970
    assert customer["total_paid_amount"] == 500
    assert customer["outstanding_amount"] == 2470


def test_connection_consumption_report(client, admin_user, db_session):
    token = login(client)

    seed_dashboard_data(db_session)

    response = client.get(
        "/reports/connections/consumption",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2

    active_connection = next(
        item
        for item in data
        if item["connection_number"] == "CONN-DASH-001"
    )

    assert active_connection["units_consumed"] == 150
    assert active_connection["total_billed_amount"] == 1760


def test_technician_performance_report(client, admin_user, db_session):
    token = login(client)

    seed_dashboard_data(db_session)

    response = client.get(
        "/reports/technicians/performance",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    technician = data[0]

    assert technician["technician_name"] == "Dashboard Technician"
    assert technician["assigned_complaints"] == 2
    assert technician["resolved_complaints"] == 1
    assert technician["open_complaints"] == 1


def test_complaint_resolution_report(client, admin_user, db_session):
    token = login(client)

    seed_dashboard_data(db_session)

    response = client.get(
        "/reports/complaints/resolution",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_complaints"] == 2
    assert data["resolved_complaints"] == 1
    assert data["closed_complaints"] == 0
    assert data["open_complaints"] == 1
    assert data["average_resolution_days"] >= 0


def test_outstanding_payment_report(client, admin_user, db_session):
    token = login(client)

    seed_dashboard_data(db_session)

    response = client.get(
        "/reports/outstanding-payments",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2

    bill = next(
        item
        for item in data
        if item["bill_id"] is not None
    )

    assert bill["total_amount"] > 0
    assert bill["paid_amount"] >= 0
    assert bill["outstanding_amount"] >= 0


def test_dashboard_requires_authentication(client):
    response = client.get("/dashboard")

    assert response.status_code == 401


def test_reports_require_authentication(client):
    endpoints = [
        "/reports/daily-collection",
        "/reports/monthly-revenue",
        "/reports/customers/billing",
        "/reports/connections/consumption",
        "/reports/technicians/performance",
        "/reports/complaints/resolution",
        "/reports/outstanding-payments",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)

        assert response.status_code == 401