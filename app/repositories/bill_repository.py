from datetime import date
from decimal import Decimal

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.bill import Bill, BillStatus
from app.models.connection import Connection
from app.models.payment import Payment, PaymentStatus


class BillRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        bill_id: int,
    ) -> Bill | None:
        return self.db.get(Bill, bill_id)

    def get_by_connection_and_month(
        self,
        connection_id: int,
        billing_month: str,
    ) -> Bill | None:

        query = select(Bill).where(
            Bill.connection_id == connection_id,
            Bill.billing_month == billing_month,
        )

        return self.db.scalars(query).first()

    def create(
        self,
        bill: Bill,
    ) -> Bill:
        self.db.add(bill)
        self.db.flush()
        self.db.refresh(bill)

        return bill

    def update(
        self,
        bill: Bill,
    ) -> Bill:
        self.db.flush()
        self.db.refresh(bill)

        return bill

    def list_bills(
        self,
        page: int = 1,
        limit: int = 10,
        billing_month: str | None = None,
        bill_status: BillStatus | None = None,
        payment_status: PaymentStatus | None = None,
        overdue_status: bool | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        sort_by: str = "id",
        sort_order: str = "desc",
    ) -> tuple[list[Bill], int]:

        query = select(Bill)

        if billing_month:
            query = query.where(
                Bill.billing_month == billing_month
            )

        if bill_status:
            query = query.where(
                Bill.bill_status == bill_status
            )

        if min_amount is not None:
            query = query.where(
                Bill.total_amount >= min_amount
            )

        if max_amount is not None:
            query = query.where(
                Bill.total_amount <= max_amount
            )

        if overdue_status is True:
            query = query.where(
                Bill.due_date < date.today(),
                Bill.bill_status != BillStatus.PAID,
            )

        elif overdue_status is False:
            query = query.where(
                (
                    Bill.due_date >= date.today()
                )
                | (
                    Bill.bill_status == BillStatus.PAID
                )
            )

        if payment_status is not None:
            successful_payment_exists = (
                select(Payment.id)
                .where(
                    Payment.bill_id == Bill.id,
                    Payment.payment_status
                    == PaymentStatus.SUCCESS,
                )
                .exists()
            )

            failed_payment_exists = (
                select(Payment.id)
                .where(
                    Payment.bill_id == Bill.id,
                    Payment.payment_status
                    == PaymentStatus.FAILED,
                )
                .exists()
            )

            pending_payment_exists = (
                select(Payment.id)
                .where(
                    Payment.bill_id == Bill.id,
                    Payment.payment_status
                    == PaymentStatus.PENDING,
                )
                .exists()
            )

            refunded_payment_exists = (
                select(Payment.id)
                .where(
                    Payment.bill_id == Bill.id,
                    Payment.payment_status
                    == PaymentStatus.REFUNDED,
                )
                .exists()
            )

            if payment_status == PaymentStatus.SUCCESS:
                query = query.where(
                    successful_payment_exists
                )

            elif payment_status == PaymentStatus.FAILED:
                query = query.where(
                    failed_payment_exists
                )

            elif payment_status == PaymentStatus.PENDING:
                query = query.where(
                    pending_payment_exists
                )

            elif payment_status == PaymentStatus.REFUNDED:
                query = query.where(
                    refunded_payment_exists
                )

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        total = self.db.scalar(count_query) or 0

        sort_columns = {
            "id": Bill.id,
            "billing_month": Bill.billing_month,
            "units_consumed": Bill.units_consumed,
            "total_amount": Bill.total_amount,
            "due_date": Bill.due_date,
            "bill_status": Bill.bill_status,
        }

        sort_column = sort_columns.get(
            sort_by,
            Bill.id,
        )

        if sort_order.lower() == "asc":
            query = query.order_by(
                asc(sort_column)
            )
        else:
            query = query.order_by(
                desc(sort_column)
            )

        offset = (page - 1) * limit

        query = query.offset(offset).limit(limit)

        bills = list(
            self.db.scalars(query).all()
        )

        return bills, total

    def list_by_connection(
        self,
        connection_id: int,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "billing_month",
        sort_order: str = "desc",
    ) -> tuple[list[Bill], int]:

        query = select(Bill).where(
            Bill.connection_id == connection_id
        )

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        total = self.db.scalar(count_query) or 0

        sort_columns = {
            "id": Bill.id,
            "billing_month": Bill.billing_month,
            "units_consumed": Bill.units_consumed,
            "total_amount": Bill.total_amount,
            "due_date": Bill.due_date,
            "bill_status": Bill.bill_status,
        }

        sort_column = sort_columns.get(
            sort_by,
            Bill.billing_month,
        )

        if sort_order.lower() == "asc":
            query = query.order_by(
                asc(sort_column)
            )
        else:
            query = query.order_by(
                desc(sort_column)
            )

        offset = (page - 1) * limit

        query = query.offset(offset).limit(limit)

        bills = list(
            self.db.scalars(query).all()
        )

        return bills, total

    def list_by_customer(
        self,
        customer_id: int,
        page: int = 1,
        limit: int = 10,
        billing_month: str | None = None,
        bill_status: BillStatus | None = None,
        sort_by: str = "billing_month",
        sort_order: str = "desc",
    ) -> tuple[list[Bill], int]:

        query = (
            select(Bill)
            .join(
                Connection,
                Bill.connection_id == Connection.id,
            )
            .where(
                Connection.customer_id == customer_id
            )
        )

        if billing_month:
            query = query.where(
                Bill.billing_month == billing_month
            )

        if bill_status:
            query = query.where(
                Bill.bill_status == bill_status
            )

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        total = self.db.scalar(count_query) or 0

        sort_columns = {
            "id": Bill.id,
            "billing_month": Bill.billing_month,
            "units_consumed": Bill.units_consumed,
            "total_amount": Bill.total_amount,
            "due_date": Bill.due_date,
            "bill_status": Bill.bill_status,
        }

        sort_column = sort_columns.get(
            sort_by,
            Bill.billing_month,
        )

        if sort_order.lower() == "asc":
            query = query.order_by(
                asc(sort_column)
            )
        else:
            query = query.order_by(
                desc(sort_column)
            )

        offset = (page - 1) * limit

        query = query.offset(offset).limit(limit)

        bills = list(
            self.db.scalars(query).all()
        )

        return bills, total