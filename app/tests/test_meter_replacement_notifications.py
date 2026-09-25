from app.models.meter import MeterStatus
from app.models.notification import Notification, NotificationType
from app.tests.conftest import TestingSessionLocal


def test_meter_replacement_completed_creates_notification(client):
    # ---------------------------------------------------------
    # 1. Register Super Admin
    # ---------------------------------------------------------
    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Meter Replacement Admin",
            "email": "meter.replacement.admin@example.com",
            "password": "Admin@123",
            "role": "Super Admin",
        },
    )

    assert register_response.status_code in (200, 201), (
        register_response.status_code,
        register_response.text,
    )

    # ---------------------------------------------------------
    # 2. Login as Super Admin
    # ---------------------------------------------------------
    login_response = client.post(
        "/auth/login",
        json={
            "email": "meter.replacement.admin@example.com",
            "password": "Admin@123",
        },
    )

    assert login_response.status_code == 200, (
        login_response.status_code,
        login_response.text,
    )

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 3. Get current user
    # ---------------------------------------------------------
    me_response = client.get(
        "/auth/me",
        headers=headers,
    )

    assert me_response.status_code == 200, (
        me_response.status_code,
        me_response.text,
    )

    user_id = me_response.json()["id"]

    # ---------------------------------------------------------
    # 4. Create Customer
    # ---------------------------------------------------------
    customer_response = client.post(
        "/customers",
        json={
            "customer_number": "CUST-METER-REPLACE-001",
            "full_name": "Meter Replacement Customer",
            "email": "meter.replacement.customer@example.com",
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

    # ---------------------------------------------------------
    # 5. Create Connection
    # ---------------------------------------------------------
    connection_response = client.post(
        "/connections",
        json={
            "customer_id": customer_id,
            "connection_number": "CONN-METER-REPLACE-001",
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

    # ---------------------------------------------------------
    # 6. Create Original Meter
    # ---------------------------------------------------------
    meter_response = client.post(
        "/meters",
        json={
            "connection_id": connection_id,
            "meter_number": "METER-OLD-001",
            "meter_type": "Smart Meter",
            "installation_date": "2026-09-25",
            "initial_reading": 0,
            "current_reading": 100,
            "meter_status": MeterStatus.ACTIVE.value,
        },
        headers=headers,
    )

    assert meter_response.status_code == 201, (
        meter_response.status_code,
        meter_response.text,
    )

    old_meter_id = meter_response.json()["id"]

    assert meter_response.json()["meter_number"] == "METER-OLD-001"
    assert meter_response.json()["meter_status"] == "Active"

    # ---------------------------------------------------------
    # 7. Replace Meter
    # ---------------------------------------------------------
    replace_response = client.post(
        f"/meters/{old_meter_id}/replace",
        json={
            "meter_number": "METER-NEW-001",
            "meter_type": "Smart Meter",
            "installation_date": "2026-09-25",
            "initial_reading": 0,
            "current_reading": 0,
        },
        headers=headers,
    )

    assert replace_response.status_code == 200, (
        replace_response.status_code,
        replace_response.text,
    )

    new_meter = replace_response.json()

    assert new_meter["meter_number"] == "METER-NEW-001"
    assert new_meter["meter_status"] == "Active"
    assert new_meter["connection_id"] == connection_id

    # ---------------------------------------------------------
    # 8. Verify Old Meter Was Removed
    # ---------------------------------------------------------
    old_meter_response = client.get(
        f"/meters/{old_meter_id}",
        headers=headers,
    )

    assert old_meter_response.status_code == 200

    old_meter = old_meter_response.json()

    assert old_meter["meter_status"] == "Removed"

    # ---------------------------------------------------------
    # 9. Verify Meter Replacement Notification
    # ---------------------------------------------------------
    db = TestingSessionLocal()

    try:
        notification = (
            db.query(Notification)
            .filter(
                Notification.notification_type
                == NotificationType.METER_REPLACEMENT_COMPLETED,
                Notification.user_id == user_id,
            )
            .order_by(Notification.id.desc())
            .first()
        )

        assert notification is not None

        assert (
            notification.notification_type
            == NotificationType.METER_REPLACEMENT_COMPLETED
        )

        assert notification.user_id == user_id

        assert notification.title == "Meter Replacement Completed"

        assert str(old_meter_id) in notification.message

        assert str(new_meter["id"]) in notification.message

        assert "METER-NEW-001" in notification.message

    finally:
        db.close()