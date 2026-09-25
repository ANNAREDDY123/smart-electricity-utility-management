from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.bill import Bill, BillStatus
from app.models.connection import Connection, ConnectionStatus
from app.models.payment import PaymentStatus
from app.repositories.bill_repository import BillRepository
from app.schemas.bill import BillGenerateRequest, BillUpdate


class BillService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = BillRepository(db)

    def get_bill(
        self,
        bill_id: int,
    ) -> Bill:

        bill = self.repository.get_by_id(bill_id)

        if not bill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bill not found",
            )

        return bill

    def generate_bill(
        self,
        data: BillGenerateRequest,
    ) -> Bill:

        connection = self.db.get(
            Connection,
            data.connection_id,
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        if connection.status == ConnectionStatus.DISCONNECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Disconnected connections cannot generate new bills",
            )

        existing_bill = (
            self.repository.get_by_connection_and_month(
                data.connection_id,
                data.billing_month,
            )
        )

        if existing_bill:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A bill already exists for this connection "
                    f"for billing month {data.billing_month}"
                ),
            )

        energy_charge = (
            data.units_consumed * data.tariff_rate
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        total_amount = (
            energy_charge
            + data.fixed_charge
            + data.tax
            + data.late_fee
            - data.discount
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        if total_amount <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Bill amount must be greater than zero",
            )

        bill = Bill(
            connection_id=data.connection_id,
            billing_month=data.billing_month,
            units_consumed=data.units_consumed,
            energy_charge=energy_charge,
            fixed_charge=data.fixed_charge,
            tax=data.tax,
            late_fee=data.late_fee,
            discount=data.discount,
            total_amount=total_amount,
            due_date=data.due_date,
            bill_status=BillStatus.GENERATED,
        )

        try:
            return self.repository.create(bill)

        except IntegrityError:
            self.db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate bill for this connection and billing month",
            )

    def update_bill(
        self,
        bill_id: int,
        data: BillUpdate,
    ) -> Bill:

        bill = self.get_bill(bill_id)

        if data.late_fee is not None:
            bill.late_fee = data.late_fee

        if data.discount is not None:
            bill.discount = data.discount

        if data.due_date is not None:
            bill.due_date = data.due_date

        if data.bill_status is not None:
            bill.bill_status = data.bill_status

        total_amount = (
            bill.energy_charge
            + bill.fixed_charge
            + bill.tax
            + bill.late_fee
            - bill.discount
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        if total_amount <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Bill amount must be greater than zero",
            )

        bill.total_amount = total_amount

        return self.repository.update(bill)

    def list_bills(
        self,
        page: int,
        limit: int,
        billing_month: str | None = None,
        bill_status: BillStatus | None = None,
        payment_status: PaymentStatus | None = None,
        overdue_status: bool | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        sort_by: str = "id",
        sort_order: str = "desc",
    ):
        return self.repository.list_bills(
            page=page,
            limit=limit,
            billing_month=billing_month,
            bill_status=bill_status,
            payment_status=payment_status,
            overdue_status=overdue_status,
            min_amount=min_amount,
            max_amount=max_amount,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def list_connection_bills(
        self,
        connection_id: int,
        page: int,
        limit: int,
        sort_by: str,
        sort_order: str,
    ):

        connection = self.db.get(
            Connection,
            connection_id,
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        return self.repository.list_by_connection(
            connection_id=connection_id,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def list_customer_bills(
        self,
        customer_id: int,
        page: int,
        limit: int,
        billing_month: str | None,
        bill_status: BillStatus | None,
        sort_by: str,
        sort_order: str,
    ):
        from app.models.customer import Customer

        customer = self.db.get(
            Customer,
            customer_id,
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        return self.repository.list_by_customer(
            customer_id=customer_id,
            page=page,
            limit=limit,
            billing_month=billing_month,
            bill_status=bill_status,
            sort_by=sort_by,
            sort_order=sort_order,
        )