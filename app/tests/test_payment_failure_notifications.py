from app.models.notification import Notification, NotificationType
from app.tests.conftest import TestingSessionLocal


def test_failed_payment_creates_failure_notification(client):
    # Register admin
    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Payment Failure Admin",
            "email": "payment.failure.admin@example.com",
            "password": "Admin@123",
            "role": "Super Admin",
        },
    )

    assert register_response.status_code in (200, 201)

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": "payment.failure.admin@example.com",
            "password": "Admin@123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # Create customer
    customer_response = client.post(
        "/customers",
        json={
            "customer_number": "CUST-NOTIFY-FAIL-001",
            "full_name": "Failure Notification Customer",
            "email": "failure.customer@example.com",
            "phone": "9876543210",
            "address": "Hyderabad",
            "city": "Hyderabad",
        },
        headers=headers,
    )

    assert customer_response.status_code in (200, 201), (
        customer_response.status_code,
        customer_response.text,
    )

    customer_id = customer_response.json()["id"]

    # Create connection
    connection_response = client.post(
        "/connections",
        json={
            "customer_id": customer_id,
            "connection_number": "CONN-NOTIFY-FAIL-001",
            "connection_type": "Residential",
            "sanctioned_load": 5.0,
            "tariff_type": "Domestic",
            "connection_date": "2026-09-25",
        },
        headers=headers,
    )

    assert connection_response.status_code in (200, 201), (
        connection_response.status_code,
        connection_response.text,
    )

    connection_id = connection_response.json()["id"]

    # Create bill
    bill_response = client.post(
        "/bills/generate",
        json={
            "connection_id": connection_id,
            "billing_month": "2026-09",
            "units_consumed": 100,
            "tariff_rate": 5.0,
            "fixed_charge": 50.0,
            "tax": 50.0,
            "due_date": "2026-10-10",
        },
        headers=headers,
    )

    assert bill_response.status_code in (200, 201), (
        bill_response.status_code,
        bill_response.text,
    )

    bill_id = bill_response.json()["id"]

    # Create failed payment
    payment_response = client.post(
        f"/payments/{bill_id}",
        json={
            "amount": 500,
            "payment_method": "UPI",
            "transaction_id": "TXN-NOTIFY-FAIL-001",
            "payment_status": "Failed",
        },
        headers=headers,
    )

    assert payment_response.status_code == 201, (
        payment_response.status_code,
        payment_response.text,
    )

    payment_data = payment_response.json()

    assert payment_data["payment_status"] == "Failed"

    payment_id = payment_data["id"]

    # Check notification
    db = TestingSessionLocal()

    try:
        notification = (
            db.query(Notification)
            .filter(
                Notification.notification_type
                == NotificationType.PAYMENT_FAILURE
            )
            .order_by(Notification.id.desc())
            .first()
        )

        assert notification is not None
        assert notification.title == "Payment Failure"
        assert str(payment_id) in notification.message
        assert str(bill_id) in notification.message
        assert "500" in notification.message

    finally:
        db.close()