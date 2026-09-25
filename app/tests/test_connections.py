from decimal import Decimal

from app.database import SessionLocal
from app.services.connection_service import ConnectionService


def register_user(
    client,
    full_name,
    email,
    password,
    role,
):
    response = client.post(
        "/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": role,
        },
    )

    assert response.status_code == 201

    return response.json()


def login_user(
    client,
    email,
    password,
):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_admin(client):
    register_user(
        client,
        "System Administrator",
        "admin@example.com",
        "Admin@12345",
        "Super Admin",
    )

    return login_user(
        client,
        "admin@example.com",
        "Admin@12345",
    )


def create_customer(client, token):
    response = client.post(
        "/customers",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_number": "CUS-1001",
            "full_name": "Test Customer",
            "email": "customer@example.com",
            "phone": "9876543210",
            "address": "Madhapur, Hyderabad",
            "city": "Hyderabad",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_connection(
    client,
    token,
    customer_id,
    connection_number="CON-1001",
    connection_type="Residential",
    sanctioned_load=5.0,
    tariff_type="Domestic",
    connection_date="2026-09-22",
):
    return client.post(
        "/connections",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_id": customer_id,
            "connection_number": connection_number,
            "connection_type": connection_type,
            "sanctioned_load": sanctioned_load,
            "tariff_type": tariff_type,
            "connection_date": connection_date,
        },
    )


def test_create_connection(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    response = create_connection(
        client,
        token,
        customer["id"],
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["customer_id"] == customer["id"]
    assert data["connection_number"] == "CON-1001"
    assert data["connection_type"] == "Residential"
    assert Decimal(str(data["sanctioned_load"])) == Decimal("5.00")
    assert data["tariff_type"] == "Domestic"
    assert data["connection_date"] == "2026-09-22"
    assert data["status"] == "Active"


def test_customer_can_have_multiple_connections(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    first = create_connection(
        client,
        token,
        customer["id"],
        connection_number="CON-1001",
    )

    second = create_connection(
        client,
        token,
        customer["id"],
        connection_number="CON-1002",
        connection_type="Commercial",
        tariff_type="Commercial",
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert (
        first.json()["customer_id"]
        == second.json()["customer_id"]
    )


def test_duplicate_connection_number(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    first = create_connection(
        client,
        token,
        customer["id"],
        connection_number="CON-1001",
    )

    assert first.status_code == 201

    second = create_connection(
        client,
        token,
        customer["id"],
        connection_number="CON-1001",
    )

    assert second.status_code == 409
    assert (
        second.json()["detail"]
        == "Connection number is already registered"
    )


def test_connection_requires_existing_customer(client):
    token = create_admin(client)

    response = create_connection(
        client,
        token,
        customer_id=9999,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_closed_customer_cannot_create_connection(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    update_response = client.put(
        f"/customers/{customer['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "status": "Closed",
        },
    )

    assert update_response.status_code == 200

    response = create_connection(
        client,
        token,
        customer["id"],
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Closed customers cannot create connections"
    )


def test_get_connection(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    create_response = create_connection(
        client,
        token,
        customer["id"],
    )

    connection_id = create_response.json()["id"]

    response = client.get(
        f"/connections/{connection_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == connection_id


def test_get_nonexistent_connection(client):
    token = create_admin(client)

    response = client.get(
        "/connections/9999",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Connection not found"


def test_list_connections(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    first = create_connection(
        client,
        token,
        customer["id"],
        connection_number="CON-1001",
    )

    second = create_connection(
        client,
        token,
        customer["id"],
        connection_number="CON-1002",
        connection_type="Commercial",
        tariff_type="Commercial",
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        "/connections",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_filter_connections_by_type(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    create_connection(
        client,
        token,
        customer["id"],
        connection_number="CON-1001",
        connection_type="Residential",
    )

    create_connection(
        client,
        token,
        customer["id"],
        connection_number="CON-1002",
        connection_type="Industrial",
    )

    response = client.get(
        "/connections?connection_type=Industrial",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["connection_type"] == "Industrial"


def test_filter_connections_by_status(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    create_connection(
        client,
        token,
        customer["id"],
        connection_number="CON-1001",
    )

    create_connection(
        client,
        token,
        customer["id"],
        connection_number="CON-1002",
    )

    disconnect_response = client.patch(
        "/connections/2/disconnect",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert disconnect_response.status_code == 200

    response = client.get(
        "/connections?status=Disconnected",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "Disconnected"


def test_filter_connections_by_tariff(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    create_connection(
        client,
        token,
        customer["id"],
        connection_number="CON-1001",
        tariff_type="Domestic",
    )

    create_connection(
        client,
        token,
        customer["id"],
        connection_number="CON-1002",
        tariff_type="Industrial High Voltage",
        connection_type="Industrial",
    )

    response = client.get(
        "/connections?tariff_type=Industrial",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert "Industrial" in data["items"][0]["tariff_type"]


def test_filter_connections_by_customer(client):
    token = create_admin(client)

    customer_one = create_customer(
        client,
        token,
    )

    create_connection(
        client,
        token,
        customer_one["id"],
        connection_number="CON-1001",
    )

    response = client.get(
        f"/connections?customer_id={customer_one['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert (
        data["items"][0]["customer_id"]
        == customer_one["id"]
    )


def test_connection_pagination(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    for number in range(1, 6):
        response = create_connection(
            client,
            token,
            customer["id"],
            connection_number=f"CON-{1000 + number}",
        )

        assert response.status_code == 201

    response = client.get(
        "/connections?page=2&limit=2",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 2
    assert data["limit"] == 2
    assert data["pages"] == 3
    assert len(data["items"]) == 2


def test_update_connection(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    create_response = create_connection(
        client,
        token,
        customer["id"],
    )

    connection_id = create_response.json()["id"]

    response = client.put(
        f"/connections/{connection_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "sanctioned_load": 10.0,
            "tariff_type": "Domestic Premium",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert Decimal(str(data["sanctioned_load"])) == Decimal("10.00")
    assert data["tariff_type"] == "Domestic Premium"


def test_disconnect_connection(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    create_response = create_connection(
        client,
        token,
        customer["id"],
    )

    connection_id = create_response.json()["id"]

    response = client.patch(
        f"/connections/{connection_id}/disconnect",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Disconnected"


def test_disconnect_already_disconnected_connection(client):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    create_connection(
        client,
        token,
        customer["id"],
    )

    first = client.patch(
        "/connections/1/disconnect",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert first.status_code == 200

    second = client.patch(
        "/connections/1/disconnect",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert second.status_code == 400
    assert (
        second.json()["detail"]
        == "Connection is already disconnected"
    )


def test_disconnected_connection_cannot_generate_bill(
    client,
    db_session,
):
    token = create_admin(client)

    customer = create_customer(
        client,
        token,
    )

    create_response = create_connection(
        client,
        token,
        customer["id"],
    )

    assert create_response.status_code == 201

    connection_id = create_response.json()["id"]

    disconnect_response = client.patch(
        f"/connections/{connection_id}/disconnect",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert disconnect_response.status_code == 200
    assert disconnect_response.json()["status"] == "Disconnected"

    service = ConnectionService(db_session)

    try:
        service.ensure_bill_generation_allowed(
            connection_id
        )
    except Exception as exc:
        assert exc.status_code == 400
        assert (
            exc.detail
            == "Disconnected connections cannot "
            "generate new bills"
        )
    else:
        raise AssertionError(
            "Disconnected connection should not "
            "be allowed to generate bills"
        )
def test_connection_rbac_field_technician_cannot_create(
    client,
):
    register_user(
        client,
        "Field Technician",
        "technician@example.com",
        "Technician@12345",
        "Field Technician",
    )

    token = login_user(
        client,
        "technician@example.com",
        "Technician@12345",
    )

    response = client.post(
        "/connections",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_id": 1,
            "connection_number": "CON-1001",
            "connection_type": "Residential",
            "sanctioned_load": 5,
            "tariff_type": "Domestic",
            "connection_date": "2026-09-22",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_connection_rbac_customer_cannot_create(
    client,
):
    register_user(
        client,
        "Test Customer",
        "customer@example.com",
        "Customer@12345",
        "Customer",
    )

    token = login_user(
        client,
        "customer@example.com",
        "Customer@12345",
    )

    response = client.post(
        "/connections",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_id": 1,
            "connection_number": "CON-1001",
            "connection_type": "Residential",
            "sanctioned_load": 5,
            "tariff_type": "Domestic",
            "connection_date": "2026-09-22",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"