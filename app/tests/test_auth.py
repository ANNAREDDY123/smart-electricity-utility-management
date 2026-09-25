def test_register_customer(client, customer_data):
    response = client.post(
        "/auth/register",
        json=customer_data,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["full_name"] == "Test Customer"
    assert data["email"] == "testcustomer@example.com"
    assert data["role"] == "Customer"
    assert data["is_active"] is True

    assert "password" not in data
    assert "password_hash" not in data


def test_duplicate_email(client, customer_data):
    first_response = client.post(
        "/auth/register",
        json=customer_data,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json={
            **customer_data,
            "full_name": "Another Customer",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email is already registered"


def test_register_super_admin(client):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "System Administrator",
            "email": "admin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["role"] == "Super Admin"
    assert data["is_active"] is True


def test_login_success(client, customer_data):
    register_response = client.post(
        "/auth/register",
        json=customer_data,
    )

    assert register_response.status_code == 201

    response = client.post(
        "/auth/login",
        json={
            "email": customer_data["email"],
            "password": customer_data["password"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    assert len(data["access_token"]) > 20
    assert len(data["refresh_token"]) > 20


def test_login_wrong_password(client, customer_data):
    register_response = client.post(
        "/auth/register",
        json=customer_data,
    )

    assert register_response.status_code == 201

    response = client.post(
        "/auth/login",
        json={
            "email": customer_data["email"],
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "doesnotexist@example.com",
            "password": "Test@12345",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_get_current_user(client, customer_data):
    register_response = client.post(
        "/auth/register",
        json=customer_data,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": customer_data["email"],
            "password": customer_data["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["full_name"] == customer_data["full_name"]
    assert data["email"] == customer_data["email"]
    assert data["role"] == "Customer"
    assert data["is_active"] is True

def test_get_current_user_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_refresh_token(client, customer_data):
    register_response = client.post(
        "/auth/register",
        json=customer_data,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": customer_data["email"],
            "password": customer_data["password"],
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_access_token_cannot_be_used_as_refresh_token(
    client,
    customer_data,
):
    register_response = client.post(
        "/auth/register",
        json=customer_data,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": customer_data["email"],
            "password": customer_data["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": access_token,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token required"


def test_change_password(client, customer_data):
    register_response = client.post(
        "/auth/register",
        json=customer_data,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": customer_data["email"],
            "password": customer_data["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.put(
        "/auth/change-password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "Test@12345",
            "new_password": "NewTest@12345",
        },
    )

    assert response.status_code == 204


def test_login_with_new_password(client, customer_data):
    register_response = client.post(
        "/auth/register",
        json=customer_data,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": customer_data["email"],
            "password": customer_data["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    change_response = client.put(
        "/auth/change-password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "Test@12345",
            "new_password": "NewTest@12345",
        },
    )

    assert change_response.status_code == 204

    new_login_response = client.post(
        "/auth/login",
        json={
            "email": customer_data["email"],
            "password": "NewTest@12345",
        },
    )

    assert new_login_response.status_code == 200

    data = new_login_response.json()

    assert "access_token" in data
    assert "refresh_token" in data


def test_old_password_no_longer_works(client, customer_data):
    register_response = client.post(
        "/auth/register",
        json=customer_data,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": customer_data["email"],
            "password": customer_data["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    change_response = client.put(
        "/auth/change-password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "Test@12345",
            "new_password": "NewTest@12345",
        },
    )

    assert change_response.status_code == 204

    old_password_response = client.post(
        "/auth/login",
        json={
            "email": customer_data["email"],
            "password": "Test@12345",
        },
    )

    assert old_password_response.status_code == 401
    assert old_password_response.json()["detail"] == "Invalid email or password"


def test_change_password_wrong_current_password(
    client,
    customer_data,
):
    register_response = client.post(
        "/auth/register",
        json=customer_data,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": customer_data["email"],
            "password": customer_data["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.put(
        "/auth/change-password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "WrongPassword123",
            "new_password": "NewTest@12345",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect"


def test_change_password_same_password(
    client,
    customer_data,
):
    register_response = client.post(
        "/auth/register",
        json=customer_data,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": customer_data["email"],
            "password": customer_data["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.put(
        "/auth/change-password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "Test@12345",
            "new_password": "Test@12345",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "New password must be different from current password"
    )

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


def test_super_admin_can_deactivate_user(client):
    admin = register_user(
        client,
        "System Administrator",
        "admin@example.com",
        "Admin@12345",
        "Super Admin",
    )

    customer = register_user(
        client,
        "Test Customer",
        "customer@example.com",
        "Customer@12345",
        "Customer",
    )

    admin_token = login_user(
        client,
        "admin@example.com",
        "Admin@12345",
    )

    response = client.patch(
        f"/users/{customer['id']}/status",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer["id"]
    assert data["is_active"] is False


def test_super_admin_can_activate_user(client):
    register_user(
        client,
        "System Administrator",
        "admin@example.com",
        "Admin@12345",
        "Super Admin",
    )

    customer = register_user(
        client,
        "Test Customer",
        "customer@example.com",
        "Customer@12345",
        "Customer",
    )

    admin_token = login_user(
        client,
        "admin@example.com",
        "Admin@12345",
    )

    deactivate_response = client.patch(
        f"/users/{customer['id']}/status",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
        json={
            "is_active": False,
        },
    )

    assert deactivate_response.status_code == 200

    activate_response = client.patch(
        f"/users/{customer['id']}/status",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
        json={
            "is_active": True,
        },
    )

    assert activate_response.status_code == 200

    assert activate_response.json()["is_active"] is True


def test_deactivated_user_cannot_login(client):
    register_user(
        client,
        "System Administrator",
        "admin@example.com",
        "Admin@12345",
        "Super Admin",
    )

    customer = register_user(
        client,
        "Test Customer",
        "customer@example.com",
        "Customer@12345",
        "Customer",
    )

    admin_token = login_user(
        client,
        "admin@example.com",
        "Admin@12345",
    )

    response = client.patch(
        f"/users/{customer['id']}/status",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={
            "email": "customer@example.com",
            "password": "Customer@12345",
        },
    )

    assert login_response.status_code == 403
    assert login_response.json()["detail"] == "User account is inactive"


def test_rbac_billing_officer_cannot_manage_users(client):
    register_user(
        client,
        "Billing Officer",
        "billing@example.com",
        "Billing@12345",
        "Billing Officer",
    )

    customer = register_user(
        client,
        "Test Customer",
        "customer@example.com",
        "Customer@12345",
        "Customer",
    )

    billing_token = login_user(
        client,
        "billing@example.com",
        "Billing@12345",
    )

    response = client.patch(
        f"/users/{customer['id']}/status",
        headers={
            "Authorization": f"Bearer {billing_token}",
        },
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_rbac_field_technician_cannot_manage_users(client):
    register_user(
        client,
        "Field Technician",
        "technician@example.com",
        "Technician@12345",
        "Field Technician",
    )

    customer = register_user(
        client,
        "Test Customer",
        "customer@example.com",
        "Customer@12345",
        "Customer",
    )

    technician_token = login_user(
        client,
        "technician@example.com",
        "Technician@12345",
    )

    response = client.patch(
        f"/users/{customer['id']}/status",
        headers={
            "Authorization": f"Bearer {technician_token}",
        },
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_rbac_customer_service_agent_cannot_manage_users(client):
    register_user(
        client,
        "Customer Service Agent",
        "agent@example.com",
        "Agent@12345",
        "Customer Service Agent",
    )

    customer = register_user(
        client,
        "Test Customer",
        "customer@example.com",
        "Customer@12345",
        "Customer",
    )

    agent_token = login_user(
        client,
        "agent@example.com",
        "Agent@12345",
    )

    response = client.patch(
        f"/users/{customer['id']}/status",
        headers={
            "Authorization": f"Bearer {agent_token}",
        },
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_rbac_customer_cannot_manage_users(client):
    register_user(
        client,
        "Test Customer",
        "customer@example.com",
        "Customer@12345",
        "Customer",
    )

    another_customer = register_user(
        client,
        "Another Customer",
        "another@example.com",
        "Another@12345",
        "Customer",
    )

    customer_token = login_user(
        client,
        "customer@example.com",
        "Customer@12345",
    )

    response = client.patch(
        f"/users/{another_customer['id']}/status",
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_rbac_requires_authentication(client):
    customer = register_user(
        client,
        "Test Customer",
        "customer@example.com",
        "Customer@12345",
        "Customer",
    )

    response = client.patch(
        f"/users/{customer['id']}/status",
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 401