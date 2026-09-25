from app.models.complaint import ComplaintType, ComplaintPriority
from app.models.notification import Notification, NotificationType
from app.tests.conftest import TestingSessionLocal


def test_complaint_assigned_creates_notification(client):
    # Register Super Admin
    admin_register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Complaint Assignment Admin",
            "email": "complaint.assign.admin@example.com",
            "password": "Admin@123",
            "role": "Super Admin",
        },
    )

    assert admin_register_response.status_code in (200, 201), (
        admin_register_response.status_code,
        admin_register_response.text,
    )

    # Login as Super Admin
    admin_login_response = client.post(
        "/auth/login",
        json={
            "email": "complaint.assign.admin@example.com",
            "password": "Admin@123",
        },
    )

    assert admin_login_response.status_code == 200, (
        admin_login_response.status_code,
        admin_login_response.text,
    )

    admin_token = admin_login_response.json()["access_token"]

    admin_headers = {
        "Authorization": f"Bearer {admin_token}",
    }

    # Register Field Technician
    technician_register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Complaint Field Technician",
            "email": "complaint.assign.technician@example.com",
            "password": "Technician@123",
            "role": "Field Technician",
        },
    )

    assert technician_register_response.status_code in (200, 201), (
        technician_register_response.status_code,
        technician_register_response.text,
    )

    technician_user_id = technician_register_response.json()["id"]

    # Create Customer
    customer_response = client.post(
        "/customers",
        json={
            "customer_number": "CUST-COMPLAINT-ASSIGN-001",
            "full_name": "Complaint Assignment Customer",
            "email": "complaint.assign.customer@example.com",
            "phone": "9876543210",
            "address": "Hyderabad",
            "city": "Hyderabad",
        },
        headers=admin_headers,
    )

    assert customer_response.status_code in (200, 201), (
        customer_response.status_code,
        customer_response.text,
    )

    customer_id = customer_response.json()["id"]

    # Create Connection
    connection_response = client.post(
        "/connections",
        json={
            "customer_id": customer_id,
            "connection_number": "CONN-COMPLAINT-ASSIGN-001",
            "connection_type": "Residential",
            "sanctioned_load": 5.0,
            "tariff_type": "Domestic",
            "connection_date": "2026-09-25",
        },
        headers=admin_headers,
    )

    assert connection_response.status_code in (200, 201), (
        connection_response.status_code,
        connection_response.text,
    )

    connection_id = connection_response.json()["id"]

    # Create Complaint
    complaint_response = client.post(
        "/complaints",
        json={
            "customer_id": customer_id,
            "connection_id": connection_id,
            "complaint_type": ComplaintType.POWER_FAILURE.value,
            "description": "Power supply interruption",
            "priority": ComplaintPriority.HIGH.value,
        },
        headers=admin_headers,
    )

    assert complaint_response.status_code == 201, (
        complaint_response.status_code,
        complaint_response.text,
    )

    complaint_id = complaint_response.json()["id"]

    # Assign Complaint to Field Technician
    assign_response = client.put(
        f"/complaints/{complaint_id}/assign",
        json={
            "assigned_to": technician_user_id,
        },
        headers=admin_headers,
    )

    assert assign_response.status_code == 200, (
        assign_response.status_code,
        assign_response.text,
    )

    assigned_complaint = assign_response.json()

    assert assigned_complaint["assigned_to"] == technician_user_id

    # Verify Complaint Assigned Notification
    db = TestingSessionLocal()

    try:
        notification = (
            db.query(Notification)
            .filter(
                Notification.notification_type
                == NotificationType.COMPLAINT_ASSIGNED,
                Notification.user_id == technician_user_id,
            )
            .order_by(Notification.id.desc())
            .first()
        )

        assert notification is not None

        assert (
            notification.notification_type
            == NotificationType.COMPLAINT_ASSIGNED
        )

        assert notification.user_id == technician_user_id

        assert notification.title == "Complaint Assigned"

        assert str(complaint_id) in notification.message

        assert "ComplaintPriority.HIGH" in notification.message

        assert "ComplaintType.POWER_FAILURE" in notification.message

    finally:
        db.close()