from math import ceil


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


def login_user(client, email, password):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_admin_and_get_token(client):
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


def create_customer(
    client,
    token,
    customer_number="CUS-1001",
    email="customer@example.com",
    full_name="Test Customer",
    city="Hyderabad",
):
    response = client.post(
        "/customers",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_number": customer_number,
            "full_name": full_name,
            "email": email,
            "phone": "9876543210",
            "address": "Madhapur, Hyderabad",
            "city": city,
        },
    )

    return response


def test_create_customer(client):
    token = create_admin_and_get_token(client)

    response = create_customer(
        client,
        token,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["customer_number"] == "CUS-1001"
    assert data["full_name"] == "Test Customer"
    assert data["email"] == "customer@example.com"
    assert data["phone"] == "9876543210"
    assert data["address"] == "Madhapur, Hyderabad"
    assert data["city"] == "Hyderabad"
    assert data["status"] == "Active"


def test_duplicate_customer_number(client):
    token = create_admin_and_get_token(client)

    first_response = create_customer(
        client,
        token,
        customer_number="CUS-1001",
        email="first@example.com",
    )

    assert first_response.status_code == 201

    second_response = create_customer(
        client,
        token,
        customer_number="CUS-1001",
        email="second@example.com",
    )

    assert second_response.status_code == 409

    assert (
        second_response.json()["detail"]
        == "Customer number is already registered"
    )


def test_duplicate_customer_email(client):
    token = create_admin_and_get_token(client)

    first_response = create_customer(
        client,
        token,
        customer_number="CUS-1001",
        email="same@example.com",
    )

    assert first_response.status_code == 201

    second_response = create_customer(
        client,
        token,
        customer_number="CUS-1002",
        email="same@example.com",
    )

    assert second_response.status_code == 409

    assert (
        second_response.json()["detail"]
        == "Customer email is already registered"
    )


def test_get_customer(client):
    token = create_admin_and_get_token(client)

    create_response = create_customer(
        client,
        token,
    )

    customer_id = create_response.json()["id"]

    response = client.get(
        f"/customers/{customer_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer_id
    assert data["customer_number"] == "CUS-1001"


def test_get_nonexistent_customer(client):
    token = create_admin_and_get_token(client)

    response = client.get(
        "/customers/9999",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_list_customers(client):
    token = create_admin_and_get_token(client)

    create_customer(
        client,
        token,
        customer_number="CUS-1001",
        email="customer1@example.com",
        full_name="Customer One",
    )

    create_customer(
        client,
        token,
        customer_number="CUS-1002",
        email="customer2@example.com",
        full_name="Customer Two",
    )

    response = client.get(
        "/customers",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["pages"] == 1
    assert len(data["items"]) == 2


def test_filter_customers_by_city(client):
    token = create_admin_and_get_token(client)

    create_customer(
        client,
        token,
        customer_number="CUS-1001",
        email="hyd@example.com",
        city="Hyderabad",
    )

    create_customer(
        client,
        token,
        customer_number="CUS-1002",
        email="bangalore@example.com",
        city="Bangalore",
    )

    response = client.get(
        "/customers?city=Hyderabad",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["city"] == "Hyderabad"


def test_filter_customers_by_status(client):
    token = create_admin_and_get_token(client)

    create_customer(
        client,
        token,
        customer_number="CUS-1001",
        email="active@example.com",
    )

    create_customer(
        client,
        token,
        customer_number="CUS-1002",
        email="suspended@example.com",
    )

    customer_id = 2

    update_response = client.put(
        f"/customers/{customer_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "status": "Suspended",
        },
    )

    assert update_response.status_code == 200

    response = client.get(
        "/customers?status=Suspended",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "Suspended"


def test_customer_pagination(client):
    token = create_admin_and_get_token(client)

    for number in range(1, 6):
        create_customer(
            client,
            token,
            customer_number=f"CUS-{1000 + number}",
            email=f"customer{number}@example.com",
            full_name=f"Customer {number}",
        )

    response = client.get(
        "/customers?page=2&limit=2",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 2
    assert data["limit"] == 2
    assert data["pages"] == ceil(5 / 2)
    assert len(data["items"]) == 2


def test_customer_sorting_descending(client):
    token = create_admin_and_get_token(client)

    create_customer(
        client,
        token,
        customer_number="CUS-1001",
        email="a@example.com",
        full_name="Alpha Customer",
    )

    create_customer(
        client,
        token,
        customer_number="CUS-1002",
        email="b@example.com",
        full_name="Beta Customer",
    )

    response = client.get(
        "/customers?sort_by=full_name&sort_order=desc",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["full_name"] == "Beta Customer"
    assert data["items"][1]["full_name"] == "Alpha Customer"


def test_update_customer(client):
    token = create_admin_and_get_token(client)

    create_response = create_customer(
        client,
        token,
    )

    customer_id = create_response.json()["id"]

    response = client.put(
        f"/customers/{customer_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "full_name": "Updated Customer",
            "phone": "9123456789",
            "city": "Bangalore",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["full_name"] == "Updated Customer"
    assert data["phone"] == "9123456789"
    assert data["city"] == "Bangalore"


def test_update_customer_duplicate_email(client):
    token = create_admin_and_get_token(client)

    create_customer(
        client,
        token,
        customer_number="CUS-1001",
        email="first@example.com",
    )

    create_customer(
        client,
        token,
        customer_number="CUS-1002",
        email="second@example.com",
    )

    response = client.put(
        "/customers/2",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "email": "first@example.com",
        },
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]
        == "Customer email is already registered"
    )


def test_delete_customer(client):
    token = create_admin_and_get_token(client)

    create_response = create_customer(
        client,
        token,
    )

    customer_id = create_response.json()["id"]

    response = client.delete(
        f"/customers/{customer_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/customers/{customer_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert get_response.status_code == 404


def test_customer_create_requires_authorization(client):
    response = client.post(
        "/customers",
        json={
            "customer_number": "CUS-1001",
            "full_name": "Test Customer",
            "email": "customer@example.com",
            "phone": "9876543210",
            "address": "Hyderabad",
            "city": "Hyderabad",
        },
    )

    assert response.status_code == 401


def test_customer_rbac_billing_officer_can_list(client):
    register_user(
        client,
        "Billing Officer",
        "billing@example.com",
        "Billing@12345",
        "Billing Officer",
    )

    token = login_user(
        client,
        "billing@example.com",
        "Billing@12345",
    )

    response = client.get(
        "/customers",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200


def test_customer_rbac_field_technician_cannot_create(client):
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
        "/customers",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_number": "CUS-1001",
            "full_name": "Test Customer",
            "email": "customer@example.com",
            "phone": "9876543210",
            "address": "Hyderabad",
            "city": "Hyderabad",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_customer_rbac_customer_cannot_create(client):
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
        "/customers",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_number": "CUS-1001",
            "full_name": "Another Customer",
            "email": "another@example.com",
            "phone": "9876543210",
            "address": "Hyderabad",
            "city": "Hyderabad",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"