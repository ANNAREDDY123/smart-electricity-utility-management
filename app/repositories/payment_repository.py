from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        payment_id: int,
    ) -> Payment | None:
        return self.db.get(Payment, payment_id)

    def get_by_transaction_id(
        self,
        transaction_id: str,
    ) -> Payment | None:
        query = select(Payment).where(
            Payment.transaction_id == transaction_id
        )

        return self.db.scalars(query).first()

    def get_by_bill_id(
        self,
        bill_id: int,
    ) -> list[Payment]:
        query = (
            select(Payment)
            .where(Payment.bill_id == bill_id)
            .order_by(
                Payment.payment_date.desc(),
                Payment.id.desc(),
            )
        )

        return list(self.db.scalars(query).all())

    def get_successful_payments_by_bill_id(
        self,
        bill_id: int,
    ) -> list[Payment]:
        query = (
            select(Payment)
            .where(
                Payment.bill_id == bill_id,
                Payment.payment_status == PaymentStatus.SUCCESS,
            )
            .order_by(
                Payment.payment_date.asc(),
                Payment.id.asc(),
            )
        )

        return list(self.db.scalars(query).all())

    def list_payments(
        self,
        bill_id: int | None = None,
        payment_status=None,
        payment_method=None,
    ) -> list[Payment]:
        query = select(Payment)

        if bill_id is not None:
            query = query.where(
                Payment.bill_id == bill_id
            )

        if payment_status is not None:
            query = query.where(
                Payment.payment_status == payment_status
            )

        if payment_method is not None:
            query = query.where(
                Payment.payment_method == payment_method
            )

        query = query.order_by(
            Payment.payment_date.desc(),
            Payment.id.desc(),
        )

        return list(self.db.scalars(query).all())

    def create(
        self,
        payment: Payment,
    ) -> Payment:
        self.db.add(payment)
        self.db.flush()
        self.db.refresh(payment)

        return payment