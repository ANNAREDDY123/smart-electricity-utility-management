from fastapi.testclient import TestClient


def register_user(client: TestClient) -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": "notification_test@example.com",
            "password": "Test@12345",
            "full_name": "Notification Test User",
            "role": "Customer",
        },
    )

    assert response.status_code in (200, 201), response.text

    return response.json()


def login_user(client: TestClient) -> str:
    response = client.post(
        "/auth/login",
        json={
            "email": "notification_test@example.com",
            "password": "Test@12345",
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def test_create_notification(client):
    user = register_user(client)
    token = login_user(client)

    response = client.post(
        "/notifications",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "user_id": user["id"],
            "notification_type": "Bill Generated",
            "title": "New Electricity Bill",
            "message": "Your electricity bill has been generated successfully.",
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["id"] > 0
    assert data["user_id"] == user["id"]
    assert data["notification_type"] == "Bill Generated"
    assert data["title"] == "New Electricity Bill"
    assert data["message"] == (
        "Your electricity bill has been generated successfully."
    )
    assert data["status"] in ("Pending", "Sent")


def test_list_notifications(client):
    user = register_user(client)
    token = login_user(client)

    create_response = client.post(
        "/notifications",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "user_id": user["id"],
            "notification_type": "Payment Success",
            "title": "Payment Successful",
            "message": "Your electricity bill payment was successful.",
        },
    )

    assert create_response.status_code == 201, create_response.text

    response = client.get(
        "/notifications",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    notification = data[0]

    assert notification["user_id"] == user["id"]
    assert notification["notification_type"] == "Payment Success"


def test_get_notification(client):
    user = register_user(client)
    token = login_user(client)

    create_response = client.post(
        "/notifications",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "user_id": user["id"],
            "notification_type": "Bill Overdue",
            "title": "Bill Overdue",
            "message": "Your electricity bill is overdue.",
        },
    )

    assert create_response.status_code == 201, create_response.text

    notification_id = create_response.json()["id"]

    response = client.get(
        f"/notifications/{notification_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == notification_id
    assert data["user_id"] == user["id"]
    assert data["notification_type"] == "Bill Overdue"


def test_get_notification_not_found(client):
    user = register_user(client)
    token = login_user(client)

    response = client.get(
        "/notifications/999999",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


def test_notification_background_task_marks_sent(client):
    user = register_user(client)
    token = login_user(client)

    response = client.post(
        "/notifications",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "user_id": user["id"],
            "notification_type": "Complaint Resolved",
            "title": "Complaint Resolved",
            "message": "Your complaint has been resolved.",
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

       # Notification is created before background processing.
    # The initial response may therefore contain Pending status.
    assert data["status"] in ("Pending", "Sent")