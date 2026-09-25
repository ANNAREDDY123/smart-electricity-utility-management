from datetime import date

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


client = TestClient(app)


def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_admin():
    setup_database()

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Tariff Admin",
            "email": "tariffadmin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "tariffadmin@example.com",
            "password": "Admin@12345",
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def create_tariff(
    token: str,
    tariff_name: str = "Residential 0-100",
    minimum_units: int = 0,
    maximum_units: int | None = 100,
    rate_per_unit: float = 5.0,
    fixed_charge: float = 50.0,
    effective_from: str = "2026-01-01",
    effective_to: str | None = None,
):
    return client.post(
        "/tariffs",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "tariff_name": tariff_name,
            "connection_type": "Residential",
            "minimum_units": minimum_units,
            "maximum_units": maximum_units,
            "rate_per_unit": rate_per_unit,
            "fixed_charge": fixed_charge,
            "effective_from": effective_from,
            "effective_to": effective_to,
            "status": "Active",
        },
    )


def test_create_tariff():
    token = create_admin()

    response = create_tariff(token)

    assert response.status_code == 201

    data = response.json()

    assert data["tariff_name"] == "Residential 0-100"
    assert data["connection_type"] == "Residential"
    assert float(data["minimum_units"]) == 0
    assert float(data["maximum_units"]) == 100
    assert float(data["rate_per_unit"]) == 5
    assert float(data["fixed_charge"]) == 50
    assert data["status"] == "Active"


def test_list_tariffs():
    token = create_admin()

    create_tariff(token)

    response = client.get(
        "/tariffs",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["tariff_name"] == "Residential 0-100"


def test_filter_tariffs_by_connection_type():
    token = create_admin()

    create_tariff(token)

    response = client.get(
        "/tariffs",
        params={
            "connection_type": "Residential"
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_update_tariff():
    token = create_admin()

    response = create_tariff(token)

    tariff_id = response.json()["id"]

    update_response = client.put(
        f"/tariffs/{tariff_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "rate_per_unit": 6.5,
            "fixed_charge": 75,
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert float(data["rate_per_unit"]) == 6.5
    assert float(data["fixed_charge"]) == 75


def test_delete_tariff():
    token = create_admin()

    response = create_tariff(token)

    tariff_id = response.json()["id"]

    delete_response = client.delete(
        f"/tariffs/{tariff_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        "/tariffs",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert get_response.status_code == 200
    assert get_response.json() == []


def test_apply_tariff_for_first_slab():
    token = create_admin()

    create_tariff(
        token,
        tariff_name="Residential 0-100",
        minimum_units=0,
        maximum_units=100,
        rate_per_unit=5,
    )

    response = client.get(
        "/tariffs/apply",
        params={
            "connection_type": "Residential",
            "units_consumed": 75,
            "effective_date": "2026-06-15",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tariff_name"] == "Residential 0-100"
    assert float(data["units_consumed"]) == 75
    assert float(data["rate_per_unit"]) == 5


def test_apply_tariff_for_second_slab():
    token = create_admin()

    create_tariff(
        token,
        tariff_name="Residential 0-100",
        minimum_units=0,
        maximum_units=100,
        rate_per_unit=5,
    )

    create_tariff(
        token,
        tariff_name="Residential 101-200",
        minimum_units=101,
        maximum_units=200,
        rate_per_unit=7,
    )

    response = client.get(
        "/tariffs/apply",
        params={
            "connection_type": "Residential",
            "units_consumed": 150,
            "effective_date": "2026-06-15",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tariff_name"] == "Residential 101-200"
    assert float(data["rate_per_unit"]) == 7


def test_apply_tariff_for_open_ended_slab():
    token = create_admin()

    create_tariff(
        token,
        tariff_name="Residential 0-100",
        minimum_units=0,
        maximum_units=100,
        rate_per_unit=5,
    )

    create_tariff(
        token,
        tariff_name="Residential 101-200",
        minimum_units=101,
        maximum_units=200,
        rate_per_unit=7,
    )

    create_tariff(
        token,
        tariff_name="Residential 201+",
        minimum_units=201,
        maximum_units=None,
        rate_per_unit=10,
    )

    response = client.get(
        "/tariffs/apply",
        params={
            "connection_type": "Residential",
            "units_consumed": 500,
            "effective_date": "2026-06-15",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tariff_name"] == "Residential 201+"
    assert float(data["rate_per_unit"]) == 10


def test_apply_tariff_wrong_connection_type_returns_404():
    token = create_admin()

    create_tariff(
        token,
        tariff_name="Residential 0-100",
        minimum_units=0,
        maximum_units=100,
    )

    response = client.get(
        "/tariffs/apply",
        params={
            "connection_type": "Commercial",
            "units_consumed": 50,
            "effective_date": "2026-06-15",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_apply_tariff_outside_slab_returns_404():
    token = create_admin()

    create_tariff(
        token,
        tariff_name="Residential 0-100",
        minimum_units=0,
        maximum_units=100,
    )

    response = client.get(
        "/tariffs/apply",
        params={
            "connection_type": "Residential",
            "units_consumed": 150,
            "effective_date": "2026-06-15",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_tariff_effective_date_is_respected():
    token = create_admin()

    create_tariff(
        token,
        tariff_name="Old Residential Tariff",
        minimum_units=0,
        maximum_units=100,
        rate_per_unit=4,
        effective_from="2025-01-01",
        effective_to="2025-12-31",
    )

    create_tariff(
        token,
        tariff_name="New Residential Tariff",
        minimum_units=0,
        maximum_units=100,
        rate_per_unit=6,
        effective_from="2026-01-01",
    )

    response = client.get(
        "/tariffs/apply",
        params={
            "connection_type": "Residential",
            "units_consumed": 50,
            "effective_date": "2026-06-15",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tariff_name"] == "New Residential Tariff"
    assert float(data["rate_per_unit"]) == 6


def test_overlapping_active_slab_is_rejected():
    token = create_admin()

    first = create_tariff(
        token,
        tariff_name="Residential 0-100",
        minimum_units=0,
        maximum_units=100,
    )

    assert first.status_code == 201

    second = create_tariff(
        token,
        tariff_name="Residential 50-150",
        minimum_units=50,
        maximum_units=150,
    )

    assert second.status_code == 409


def test_invalid_tariff_range_is_rejected():
    token = create_admin()

    response = create_tariff(
        token,
        tariff_name="Invalid Slab",
        minimum_units=200,
        maximum_units=100,
    )

    assert response.status_code == 422


def test_invalid_effective_dates_are_rejected():
    token = create_admin()

    response = create_tariff(
        token,
        tariff_name="Invalid Dates",
        minimum_units=0,
        maximum_units=100,
        effective_from="2026-12-31",
        effective_to="2026-01-01",
    )

    assert response.status_code == 422


def test_negative_units_cannot_apply_tariff():
    token = create_admin()

    create_tariff(token)

    response = client.get(
        "/tariffs/apply",
        params={
            "connection_type": "Residential",
            "units_consumed": -10,
            "effective_date": "2026-06-15",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422