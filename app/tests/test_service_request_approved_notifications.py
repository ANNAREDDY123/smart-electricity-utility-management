from app.models.notification import Notification, NotificationType
from app.models.service_request import ServiceRequestType
from app.tests.conftest import TestingSessionLocal


def test_service_request_approved_creates_notification(client):
    # ---------------------------------------------------------
    # 1. Register Super Admin
    # ---------------------------------------------------------
    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Service Request Approval Admin",
            "email": "service.request.approval.admin@example.com",
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
            "email": "service.request.approval.admin@example.com",
            "password": "Admin@123",
        },
    )

    assert login_response.status_code == 200, (
        login_response.status_code,
        login_response.text,
    )

    login_data = login_response.json()

    token = login_data["access_token"]

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
            "customer_number": "CUST-SERVICE-APPROVAL-001",
            "full_name": "Service Request Customer",
            "email": "service.request.customer@example.com",
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
    # 5. Create Service Request
    # ---------------------------------------------------------
    service_request_response = client.post(
        "/service-requests",
        json={
            "customer_id": customer_id,
            "connection_id": None,
            "request_type": ServiceRequestType.NEW_CONNECTION.value,
            "description": "Request for a new electricity connection",
            "requested_date": "2026-10-01",
        },
        headers=headers,
    )

    assert service_request_response.status_code == 201, (
        service_request_response.status_code,
        service_request_response.text,
    )

    service_request_id = service_request_response.json()["id"]

    # Verify initial status
    assert service_request_response.json()["status"] == "Submitted"

    # ---------------------------------------------------------
    # 6. Approve Service Request
    # ---------------------------------------------------------
    approve_response = client.put(
        f"/service-requests/{service_request_id}/approve",
        headers=headers,
    )

    assert approve_response.status_code == 200, (
        approve_response.status_code,
        approve_response.text,
    )

    approved_request = approve_response.json()

    assert approved_request["id"] == service_request_id
    assert approved_request["status"] == "Approved"

    # ---------------------------------------------------------
    # 7. Verify Notification
    # ---------------------------------------------------------
    db = TestingSessionLocal()

    try:
        notification = (
            db.query(Notification)
            .filter(
                Notification.notification_type
                == NotificationType.SERVICE_REQUEST_APPROVED,
                Notification.user_id == user_id,
            )
            .order_by(Notification.id.desc())
            .first()
        )

        assert notification is not None

        assert (
            notification.notification_type
            == NotificationType.SERVICE_REQUEST_APPROVED
        )

        assert notification.user_id == user_id

        assert notification.title == "Service Request Approved"

        assert str(service_request_id) in notification.message

        assert "ServiceRequestType.NEW_CONNECTION" in notification.message

        assert "2026-10-01" in notification.message

    finally:
        db.close()