from datetime import date

from fastapi.testclient import TestClient

from app.models.notification import (
    Notification,
    NotificationType,
)


def register_admin(client: TestClient) -> str:
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Bill Notification Admin",
            "email": "bill_notification_admin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert response.status_code in (200, 201), response.text

    login_response = client.post(
        "/auth/login",
        json={
            "email": "bill_notification_admin@example.com",
            "password": "Admin@12345",
        },
    )

    assert login_response.status_code == 200, login_response.text

    return login_response.json()["access_token"]


def create_customer(
    client: TestClient,
    token: str,
) -> int:

    response = client.post(
        "/customers",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_number": "BILL-NOTIFY-CUST-001",
            "full_name": "Bill Notification Customer",
            "email": "bill_notification_customer@example.com",
            "phone": "9876543210",
            "address": "Notification Street",
            "city": "Hyderabad",
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()["id"]


def create_connection(
    client: TestClient,
    token: str,
    customer_id: int,
) -> int:

    response = client.post(
        "/connections",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_id": customer_id,
            "connection_number": "BILL-NOTIFY-CONN-001",
            "connection_type": "Residential",
            "sanctioned_load": 5,
            "tariff_type": "Residential",
            "connection_date": str(date.today()),
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()["id"]


def test_bill_generated_creates_notification(
    client,
    db_session,
):

    token = register_admin(client)

    customer_id = create_customer(
        client,
        token,
    )

    connection_id = create_connection(
        client,
        token,
        customer_id,
    )

    response = client.post(
        "/bills/generate",
        headers={
            "Authorization": f"Bearer {token}",
        },
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

    assert response.status_code == 201, response.text

    bill = response.json()

    assert bill["id"] > 0
    assert bill["billing_month"] == "2026-09"

    notification = (
        db_session.query(Notification)
        .filter(
            Notification.notification_type
            == NotificationType.BILL_GENERATED
        )
        .order_by(Notification.id.desc())
        .first()
    )

    assert notification is not None
    assert notification.notification_type == (
        NotificationType.BILL_GENERATED
    )
    assert notification.title == "Bill Generated"
    assert str(bill["id"]) in notification.message
    assert "2026-09" in notification.message