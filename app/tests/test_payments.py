from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


client = TestClient(app)


def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def register_admin():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Payment Admin",
            "email": "payment_admin@example.com",
            "password": "Admin@12345",
            "role": "Super Admin",
        },
    )

    assert response.status_code in (201, 409)

    login = client.post(
        "/auth/login",
        json={
            "email": "payment_admin@example.com",
            "password": "Admin@12345",
        },
    )

    assert login.status_code == 200

    return {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }


def create_bill(headers):
    # ---------------------------------------------------------
    # CREATE CUSTOMER
    # ---------------------------------------------------------
    customer = client.post(
        "/customers",
        headers=headers,
        json={
            "customer_number": "PAY-CUST-001",
            "full_name": "Payment Customer",
            "email": "payment.customer@example.com",
            "phone": "9876543210",
            "address": "Payment Street",
            "city": "Hyderabad",
            "status": "Active",
        },
    )

    assert customer.status_code == 201, (
        f"Customer creation failed: "
        f"{customer.status_code} - {customer.text}"
    )

    customer_id = customer.json()["id"]

    # ---------------------------------------------------------
    # CREATE CONNECTION
    # ---------------------------------------------------------
    connection = client.post(
        "/connections",
        headers=headers,
        json={
            "customer_id": customer_id,
            "connection_number": "PAY-CONN-001",
            "connection_type": "Residential",
            "sanctioned_load": 5,
            "tariff_type": "Residential",
            "connection_date": str(date.today()),
            "status": "Active",
        },
    )

    assert connection.status_code == 201, (
        f"Connection creation failed: "
        f"{connection.status_code} - {connection.text}"
    )

    connection_id = connection.json()["id"]

    # ---------------------------------------------------------
    # GENERATE BILL
    # ---------------------------------------------------------
    bill = client.post(
        "/bills/generate",
        headers=headers,
        json={
            "connection_id": connection_id,
            "billing_month": "2026-09",
            "units_consumed": 100,
            "tariff_rate": 5,
            "fixed_charge": 100,
            "tax": 50,
            "late_fee": 0,
            "discount": 0,
            "due_date": "2026-10-10",
        },
    )

    assert bill.status_code == 201, (
        f"Bill creation failed: "
        f"{bill.status_code} - {bill.text}"
    )

    return bill.json()


# =============================================================
# TEST 1
# CREATE SUCCESSFUL PAYMENT
# =============================================================

def test_create_successful_payment():
    setup_database()

    headers = register_admin()

    bill = create_bill(headers)

    response = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 650,
            "payment_method": "UPI",
            "transaction_id": "TXN-PAY-001",
            "payment_date": "2026-09-24T10:00:00",
            "payment_status": "Success",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["bill_id"] == bill["id"]
    assert Decimal(str(data["amount"])) == Decimal("650")
    assert data["payment_method"] == "UPI"
    assert data["transaction_id"] == "TXN-PAY-001"
    assert data["payment_status"] == "Success"


# =============================================================
# TEST 2
# SUCCESSFUL PAYMENT MARKS BILL AS PAID
# =============================================================

def test_successful_payment_marks_bill_paid():
    setup_database()

    headers = register_admin()

    bill = create_bill(headers)

    payment = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 650,
            "payment_method": "Card",
            "transaction_id": "TXN-PAY-002",
            "payment_status": "Success",
        },
    )

    assert payment.status_code == 201

    bill_response = client.get(
        f"/bills/{bill['id']}",
        headers=headers,
    )

    assert bill_response.status_code == 200

    assert (
        bill_response.json()["bill_status"]
        == "Paid"
    )


# =============================================================
# TEST 3
# FAILED PAYMENT DOES NOT MARK BILL AS PAID
# =============================================================

def test_failed_payment_does_not_mark_bill_paid():
    setup_database()

    headers = register_admin()

    bill = create_bill(headers)

    payment = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 650,
            "payment_method": "Wallet",
            "transaction_id": "TXN-PAY-003",
            "payment_status": "Failed",
        },
    )

    assert payment.status_code == 201

    bill_response = client.get(
        f"/bills/{bill['id']}",
        headers=headers,
    )

    assert bill_response.status_code == 200

    assert (
        bill_response.json()["bill_status"]
        != "Paid"
    )


# =============================================================
# TEST 4
# PAYMENT CANNOT EXCEED BILL AMOUNT
# =============================================================

def test_payment_cannot_exceed_bill_amount():
    setup_database()

    headers = register_admin()

    bill = create_bill(headers)

    response = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 651,
            "payment_method": "UPI",
            "transaction_id": "TXN-PAY-004",
            "payment_status": "Success",
        },
    )

    assert response.status_code == 422


# =============================================================
# TEST 5
# DUPLICATE TRANSACTION
# =============================================================

def test_duplicate_transaction_is_prevented():
    setup_database()

    headers = register_admin()

    bill = create_bill(headers)

    first = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 300,
            "payment_method": "UPI",
            "transaction_id": "TXN-PAY-005",
            "payment_status": "Success",
        },
    )

    assert first.status_code == 201

    second = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 300,
            "payment_method": "Card",
            "transaction_id": "TXN-PAY-005",
            "payment_status": "Success",
        },
    )

    assert second.status_code == 409


# =============================================================
# TEST 6
# GET PAYMENTS
# =============================================================

def test_get_payments():
    setup_database()

    headers = register_admin()

    bill = create_bill(headers)

    payment = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 650,
            "payment_method": "UPI",
            "transaction_id": "TXN-PAY-006",
            "payment_status": "Success",
        },
    )

    assert payment.status_code == 201

    response = client.get(
        "/payments",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert any(
        item["transaction_id"] == "TXN-PAY-006"
        for item in data
    )


# =============================================================
# TEST 7
# GET PAYMENT BY ID
# =============================================================

def test_get_payment_by_id():
    setup_database()

    headers = register_admin()

    bill = create_bill(headers)

    payment = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 650,
            "payment_method": "Net Banking",
            "transaction_id": "TXN-PAY-007",
            "payment_status": "Success",
        },
    )

    assert payment.status_code == 201

    payment_id = payment.json()["id"]

    response = client.get(
        f"/payments/{payment_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment_id
    assert data["bill_id"] == bill["id"]
    assert data["transaction_id"] == "TXN-PAY-007"


# =============================================================
# TEST 8
# GET BILL PAYMENTS
# =============================================================

def test_get_bill_payments():
    setup_database()

    headers = register_admin()

    bill = create_bill(headers)

    payment = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 650,
            "payment_method": "UPI",
            "transaction_id": "TXN-PAY-008",
            "payment_status": "Success",
        },
    )

    assert payment.status_code == 201

    response = client.get(
        f"/bills/{bill['id']}/payments",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert any(
        item["transaction_id"] == "TXN-PAY-008"
        for item in data
    )


# =============================================================
# TEST 9
# INVALID BILL
# =============================================================

def test_invalid_bill():
    setup_database()

    headers = register_admin()

    response = client.post(
        "/payments/99999",
        headers=headers,
        json={
            "amount": 100,
            "payment_method": "UPI",
            "transaction_id": "TXN-PAY-009",
            "payment_status": "Success",
        },
    )

    assert response.status_code == 404


# =============================================================
# TEST 10
# PAYMENT AMOUNT MUST BE POSITIVE
# =============================================================

def test_payment_amount_must_be_positive():
    setup_database()

    headers = register_admin()

    bill = create_bill(headers)

    response = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 0,
            "payment_method": "UPI",
            "transaction_id": "TXN-PAY-010",
            "payment_status": "Success",
        },
    )

    assert response.status_code == 422


# =============================================================
# TEST 11
# PENDING PAYMENT DOES NOT MARK BILL AS PAID
# =============================================================

def test_payment_status_pending_does_not_mark_bill_paid():
    setup_database()

    headers = register_admin()

    bill = create_bill(headers)

    payment = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 650,
            "payment_method": "UPI",
            "transaction_id": "TXN-PAY-011",
            "payment_status": "Pending",
        },
    )

    assert payment.status_code == 201

    bill_response = client.get(
        f"/bills/{bill['id']}",
        headers=headers,
    )

    assert bill_response.status_code == 200

    assert (
        bill_response.json()["bill_status"]
        != "Paid"
    )


# =============================================================
# TEST 12
# REFUNDED PAYMENT DOES NOT MARK BILL AS PAID
# =============================================================

def test_refunded_payment_does_not_mark_bill_paid():
    setup_database()

    headers = register_admin()

    bill = create_bill(headers)

    payment = client.post(
        f"/payments/{bill['id']}",
        headers=headers,
        json={
            "amount": 650,
            "payment_method": "Wallet",
            "transaction_id": "TXN-PAY-012",
            "payment_status": "Refunded",
        },
    )

    assert payment.status_code == 201

    bill_response = client.get(
        f"/bills/{bill['id']}",
        headers=headers,
    )

    assert bill_response.status_code == 200

    assert (
        bill_response.json()["bill_status"]
        != "Paid"
    )