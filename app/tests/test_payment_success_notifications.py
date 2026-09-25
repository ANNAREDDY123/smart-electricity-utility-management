from datetime import date

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.notification import (
    Notification,
    NotificationType,
)


client = TestClient(app)


# ============================================================
# DATABASE SETUP
# ============================================================

def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ============================================================
# REGISTER + LOGIN ADMIN
# ============================================================

def register_admin():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Payment Notification Admin",
            "email": "payment_notification_admin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert response.status_code in (201, 409), (
        f"Admin registration failed: "
        f"{response.status_code} - {response.text}"
    )

    login = client.post(
        "/auth/login",
        json={
            "email": "payment_notification_admin@example.com",
            "password": "Admin@12345",
        },
    )

    assert login.status_code == 200, (
        f"Admin login failed: "
        f"{login.status_code} - {login.text}"
    )

    return {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }


# ============================================================
# CREATE BILL
# ============================================================

def create_bill(headers):
    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    customer = client.post(
        "/customers",
        headers=headers,
        json={
            "customer_number": "PAY-NOTIFY-CUST-001",
            "full_name": "Payment Notification Customer",
            "email": "payment.notification.customer@example.com",
            "phone": "9876543210",
            "address": "Payment Notification Street",
            "city": "Hyderabad",
            "status": "Active",
        },
    )

    assert customer.status_code == 201, (
        f"Customer creation failed: "
        f"{customer.status_code} - {customer.text}"
    )

    customer_id = customer.json()["id"]

    # --------------------------------------------------------
    # CONNECTION
    # --------------------------------------------------------

    connection = client.post(
        "/connections",
        headers=headers,
        json={
            "customer_id": customer_id,
            "connection_number": "PAY-NOTIFY-CONN-001",
            "connection_type": "Residential",
            "sanctioned_load": 5,
            "tariff_type": "Residential",
            "connection_date": str(date.today()),
            "status": "Active",
        },
    )

    assert connection.status_code == 201, (
        f"Connection creation failed: "
        f"{connection.status_code} - {connection.text}"
    )

    connection_id = connection.json()["id"]

    # --------------------------------------------------------
    # BILL
    # --------------------------------------------------------

    bill = client.post(
        "/bills/generate",
        headers=headers,
        json={
            "connection_id": connection_id,
            "billing_month": "2026-09",
            "units_consumed": 100,
            "tariff_rate": 5,
            "fixed_charge": 100,
            "tax": 50,
            "late_fee": 0,
            "discount": 0,
            "due_date": "2026-10-10",
        },
    )

    assert bill.status_code == 201, (
        f"Bill creation failed: "
        f"{bill.status_code} - {bill.text}"
    )

    return bill.json()


# ============================================================
# PAYMENT SUCCESS NOTIFICATION
# ============================================================

def test_payment_success_notification():
    setup_database()

    headers = register_admin()

    bill = create_bill(headers)

    # --------------------------------------------------------
    # CREATE SUCCESSFUL PAYMENT
    # --------------------------------------------------------

    response = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 650,
            "payment_method": "UPI",
            "transaction_id": "TXN-NOTIFY-SUCCESS-001",
            "payment_status": "Success",
        },
    )

    assert response.status_code == 201, (
        f"Payment creation failed: "
        f"{response.status_code} - {response.text}"
    )

    payment = response.json()

    assert payment["payment_status"] == "Success"

    # --------------------------------------------------------
    # VERIFY NOTIFICATION
    # --------------------------------------------------------

    db = SessionLocal()

    try:
        notification = (
            db.query(Notification)
            .filter(
                Notification.notification_type
                == NotificationType.PAYMENT_SUCCESS
            )
            .order_by(Notification.id.desc())
            .first()
        )

        assert notification is not None

        assert notification.title == "Payment Success"

        assert str(payment["id"]) in notification.message

        assert str(bill["id"]) in notification.message

        assert str(payment["amount"]) in notification.message

    finally:
        db.close()