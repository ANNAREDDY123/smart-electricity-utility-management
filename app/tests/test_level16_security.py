from sqlalchemy.exc import IntegrityError

from app.models.audit_log import AuditLog
from app.models.customer import Customer


def test_customer_soft_delete(client):
    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Level 16 Admin",
            "email": "level16.admin@example.com",
            "password": "Admin@123",
            "role": "Super Admin",
        },
    )

    assert register_response.status_code in (200, 201)

    login_response = client.post(
        "/auth/login",
        json={
            "email": "level16.admin@example.com",
            "password": "Admin@123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
    }

    customer_response = client.post(
        "/customers",
        json={
            "customer_number": "LEVEL16-CUST-001",
            "full_name": "Level 16 Customer",
            "email": "level16.customer@example.com",
            "phone": "9876543210",
            "address": "Hyderabad",
            "city": "Hyderabad",
        },
        headers=headers,
    )

    assert customer_response.status_code == 201

    customer_id = customer_response.json()["id"]

    delete_response = client.delete(
        f"/customers/{customer_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/customers/{customer_id}",
        headers=headers,
    )

    assert get_response.status_code == 404


def test_validation_error_is_handled(client):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "",
            "email": "invalid-email",
            "password": "",
            "role": "Invalid Role",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["detail"] == "Request validation failed"
    assert "errors" in body


def test_rate_limiter_rejects_excess_requests():
    from app.utils.rate_limit import RateLimiter

    limiter = RateLimiter(
        max_requests=2,
        window_seconds=60,
    )

    class Client:
        host = "127.0.0.1"

    class Request:
        client = Client()

    request = Request()

    limiter.check(request)
    limiter.check(request)

    try:
        limiter.check(request)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 429
    else:
        raise AssertionError(
            "Rate limiter did not reject the third request"
        )