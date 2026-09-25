from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.bill import Bill, BillStatus
from app.models.complaint import (
    ComplaintPriority,
    ComplaintStatus,
    ComplaintType,
)
from app.models.connection import (
    Connection,
    ConnectionStatus,
    ConnectionType,
)
from app.models.customer import CustomerStatus
from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.models.user import User, UserRole


client = TestClient(app)


def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_admin():
    setup_database()

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Level 13 Admin",
            "email": "level13.admin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "level13.admin@example.com",
            "password": "Admin@12345",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def create_customer(
    headers,
    customer_number,
    email,
    city="Hyderabad",
):
    response = client.post(
        "/customers",
        headers=headers,
        json={
            "customer_number": customer_number,
            "full_name": f"Customer {customer_number}",
            "email": email,
            "phone": "9876543210",
            "address": city,
            "city": city,
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_connection(
    headers,
    customer_id,
    connection_number,
    connection_type="Residential",
    tariff_type="Domestic",
    status="Active",
):
    response = client.post(
        "/connections",
        headers=headers,
        json={
            "customer_id": customer_id,
            "connection_number": connection_number,
            "connection_type": connection_type,
            "sanctioned_load": 5,
            "tariff_type": tariff_type,
            "connection_date": "2026-01-01",
            "status": status,
        },
    )

    assert response.status_code == 201

    return response.json()


def create_bill(
    db,
    connection_id,
    billing_month,
    total_amount,
    due_date,
    bill_status=BillStatus.GENERATED,
):
    bill = Bill(
        connection_id=connection_id,
        billing_month=billing_month,
        units_consumed=Decimal("100.00"),
        energy_charge=Decimal(str(total_amount)),
        fixed_charge=Decimal("0.00"),
        tax=Decimal("0.00"),
        late_fee=Decimal("0.00"),
        discount=Decimal("0.00"),
        total_amount=Decimal(str(total_amount)),
        due_date=due_date,
        bill_status=bill_status,
    )

    db.add(bill)
    db.commit()
    db.refresh(bill)

    return bill


def create_payment(
    db,
    bill_id,
    status=PaymentStatus.SUCCESS,
    transaction_id="TXN-LEVEL13-001",
):
    payment = Payment(
        bill_id=bill_id,
        amount=Decimal("100.00"),
        payment_method=PaymentMethod.UPI,
        transaction_id=transaction_id,
        payment_date=date.today(),
        payment_status=status,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def create_field_technician(
    db,
    email="technician.level13@example.com",
):
    from app.utils.security import hash_password

    technician = User(
        full_name="Level 13 Technician",
        email=email,
        password_hash=hash_password(
            "Tech@12345"
        ),
        role=UserRole.FIELD_TECHNICIAN,
        is_active=True,
    )

    db.add(technician)
    db.commit()
    db.refresh(technician)

    return technician


def test_customer_filter_by_city():
    headers = create_admin()

    create_customer(
        headers,
        "L13-CUST-001",
        "l13cust1@example.com",
        "Hyderabad",
    )

    create_customer(
        headers,
        "L13-CUST-002",
        "l13cust2@example.com",
        "Bangalore",
    )

    response = client.get(
        "/customers?city=Hyderabad",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["city"] == "Hyderabad"


def test_customer_filter_by_status():
    headers = create_admin()

    create_customer(
        headers,
        "L13-CUST-001",
        "l13status1@example.com",
    )

    response = client.put(
        "/customers/1",
        headers=headers,
        json={
            "status": "Suspended"
        },
    )

    assert response.status_code == 200

    response = client.get(
        "/customers?status=Suspended",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "Suspended"


def test_customer_filter_by_connection_type():
    headers = create_admin()

    customer_1 = create_customer(
        headers,
        "L13-CUST-001",
        "l13type1@example.com",
    )

    customer_2 = create_customer(
        headers,
        "L13-CUST-002",
        "l13type2@example.com",
    )

    create_connection(
        headers,
        customer_1["id"],
        "L13-CONN-001",
        connection_type="Residential",
    )

    create_connection(
        headers,
        customer_2["id"],
        "L13-CONN-002",
        connection_type="Commercial",
    )

    response = client.get(
        "/customers?connection_type=Commercial",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["id"] == customer_2["id"]


def test_connection_filters():
    headers = create_admin()

    customer = create_customer(
        headers,
        "L13-CUST-001",
        "l13connection@example.com",
    )

    create_connection(
        headers,
        customer["id"],
        "L13-CONN-001",
        connection_type="Residential",
        tariff_type="Domestic",
    )

    create_connection(
        headers,
        customer["id"],
        "L13-CONN-002",
        connection_type="Commercial",
        tariff_type="Business",
    )

    response = client.get(
        "/connections?connection_type=Commercial&tariff_type=Business",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["connection_number"] == (
        "L13-CONN-002"
    )


def test_connection_filter_by_status():
    headers = create_admin()

    customer = create_customer(
        headers,
        "L13-CUST-001",
        "l13connstatus@example.com",
    )

    create_connection(
        headers,
        customer["id"],
        "L13-CONN-001",
        status="Active",
    )

    create_connection(
        headers,
        customer["id"],
        "L13-CONN-002",
        status="Suspended",
    )

    response = client.get(
        "/connections?status=Suspended",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "Suspended"


def test_bill_filter_by_billing_month_and_amount():
    headers = create_admin()

    customer = create_customer(
        headers,
        "L13-CUST-001",
        "l13bill1@example.com",
    )

    connection = create_connection(
        headers,
        customer["id"],
        "L13-CONN-001",
    )

    db = SessionLocal()

    try:
        create_bill(
            db,
            connection["id"],
            "2026-01",
            500,
            date(2026, 2, 15),
        )

        create_bill(
            db,
            connection["id"],
            "2026-02",
            1500,
            date(2026, 3, 15),
        )
    finally:
        db.close()

    response = client.get(
        "/bills?billing_month=2026-02&min_amount=1000&max_amount=2000",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert float(
        data["items"][0]["total_amount"]
    ) == 1500


def test_bill_filter_by_payment_status():
    headers = create_admin()

    customer = create_customer(
        headers,
        "L13-CUST-001",
        "l13payment@example.com",
    )

    connection = create_connection(
        headers,
        customer["id"],
        "L13-CONN-001",
    )

    db = SessionLocal()

    try:
        bill = create_bill(
            db,
            connection["id"],
            "2026-01",
            100,
            date(2026, 2, 15),
        )

        bill_id = bill.id

        create_payment(
            db,
            bill.id,
            PaymentStatus.SUCCESS,
        )

    finally:
        db.close()

    response = client.get(
        "/bills?payment_status=Success",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["id"] == bill_id


def test_bill_filter_by_overdue_status():
    headers = create_admin()

    customer = create_customer(
        headers,
        "L13-CUST-001",
        "l13overdue@example.com",
    )

    connection = create_connection(
        headers,
        customer["id"],
        "L13-CONN-001",
    )

    db = SessionLocal()

    try:
        create_bill(
            db,
            connection["id"],
            "2025-01",
            700,
            date.today() - timedelta(days=10),
        )
    finally:
        db.close()

    response = client.get(
        "/bills?overdue_status=true",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1


def test_bill_pagination_and_sorting():
    headers = create_admin()

    customer = create_customer(
        headers,
        "L13-CUST-001",
        "l13pages@example.com",
    )

    connection = create_connection(
        headers,
        customer["id"],
        "L13-CONN-001",
    )

    db = SessionLocal()

    try:
        for index, amount in enumerate(
            [100, 200, 300],
            start=1,
        ):
            create_bill(
                db,
                connection["id"],
                f"2026-0{index}",
                amount,
                date(2026, 12, 31),
            )
    finally:
        db.close()

    response = client.get(
        "/bills?page=1&limit=2&sort_by=total_amount&sort_order=desc",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2

    assert float(
        data["items"][0]["total_amount"]
    ) == 300


def test_complaint_filters_and_pagination():
    headers = create_admin()

    customer = create_customer(
        headers,
        "L13-CUST-001",
        "l13complaint@example.com",
    )

    connection = create_connection(
        headers,
        customer["id"],
        "L13-CONN-001",
    )

    db = SessionLocal()

    try:
        technician = create_field_technician(
            db
        )
        technician_id = technician.id
    finally:
        db.close()

    response = client.post(
        "/complaints",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Power Failure",
            "description": "Power failure issue",
            "priority": "Emergency",
        },
    )

    assert response.status_code == 201

    complaint_id = response.json()["id"]

    response = client.post(
        "/complaints",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Billing Issue",
            "description": "Billing issue",
            "priority": "Low",
        },
    )

    assert response.status_code == 201

    response = client.put(
        f"/complaints/{complaint_id}/assign",
        headers=headers,
        json={
            "assigned_to": technician_id
        },
    )

    assert response.status_code == 200

    response = client.get(
        "/complaints"
        "?priority=Emergency"
        "&complaint_type=Power%20Failure"
        f"&assigned_to={technician_id}"
        "&page=1"
        "&limit=1"
        "&sort_by=priority"
        "&sort_order=asc",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == complaint_id


def test_complaint_filter_by_status():
    headers = create_admin()

    customer = create_customer(
        headers,
        "L13-CUST-001",
        "l13complaintstatus@example.com",
    )

    connection = create_connection(
        headers,
        customer["id"],
        "L13-CONN-001",
    )

    response = client.post(
        "/complaints",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "connection_id": connection["id"],
            "complaint_type": "Meter Issue",
            "description": "Meter issue",
            "priority": "Medium",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/complaints?complaint_status=Open",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "Open"