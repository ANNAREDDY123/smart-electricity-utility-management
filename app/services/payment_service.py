from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.bill import Bill, BillStatus
from app.models.payment import Payment, PaymentStatus
from app.repositories.bill_repository import BillRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import PaymentCreate


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.payment_repository = PaymentRepository(db)
        self.bill_repository = BillRepository(db)

    def get_payment(
        self,
        payment_id: int,
    ) -> Payment:
        payment = self.payment_repository.get_by_id(
            payment_id
        )

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        return payment

    def get_bill(
        self,
        bill_id: int,
    ) -> Bill:
        bill = self.bill_repository.get_by_id(
            bill_id
        )

        if not bill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill not found",
            )

        return bill

    def create_payment(
        self,
        bill_id: int,
        data: PaymentCreate,
    ) -> Payment:
        bill = self.get_bill(bill_id)

        existing_transaction = (
            self.payment_repository.get_by_transaction_id(
                data.transaction_id
            )
        )

        if existing_transaction:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Transaction ID already exists",
            )

        if data.amount > bill.total_amount:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Payment amount cannot exceed bill amount",
            )

        successful_payments = (
            self.payment_repository
            .get_successful_payments_by_bill_id(
                bill_id
            )
        )

        successful_amount = sum(
            (
                payment.amount
                for payment in successful_payments
            ),
            Decimal("0.00"),
        )

        remaining_amount = (
            bill.total_amount - successful_amount
        )

        if data.amount > remaining_amount:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Payment amount exceeds remaining bill amount",
            )

        payment_date = (
            data.payment_date
            or datetime.now()
        )

        payment = Payment(
            bill_id=bill_id,
            amount=data.amount,
            payment_method=data.payment_method,
            transaction_id=data.transaction_id,
            payment_date=payment_date,
            payment_status=data.payment_status,
        )

        payment = self.payment_repository.create(
            payment
        )

        if data.payment_status == PaymentStatus.SUCCESS:
            new_paid_amount = (
                successful_amount + data.amount
            )

            if new_paid_amount >= bill.total_amount:
                bill.bill_status = BillStatus.PAID

        self.db.flush()

        return payment

    def list_payments(
        self,
        bill_id: int | None = None,
        payment_status=None,
        payment_method=None,
    ) -> list[Payment]:
        return self.payment_repository.list_payments(
            bill_id=bill_id,
            payment_status=payment_status,
            payment_method=payment_method,
        )

    def list_bill_payments(
        self,
        bill_id: int,
    ) -> list[Payment]:
        self.get_bill(bill_id)

        return self.payment_repository.get_by_bill_id(
            bill_id
        )