from datetime import date
from decimal import Decimal

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.bill import Bill, BillStatus
from app.models.complaint import Complaint, ComplaintStatus
from app.models.connection import Connection, ConnectionStatus
from app.models.customer import Customer
from app.models.meter import Meter, MeterStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User, UserRole


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    # =========================================================
    # DASHBOARD METRICS
    # =========================================================

    def get_total_customers(self) -> int:
        return (
            self.db.query(func.count(Customer.id))
            .scalar()
            or 0
        )

    def get_active_connections(self) -> int:
        return (
            self.db.query(func.count(Connection.id))
            .filter(
                Connection.status == ConnectionStatus.ACTIVE
            )
            .scalar()
            or 0
        )

    def get_disconnected_connections(self) -> int:
        return (
            self.db.query(func.count(Connection.id))
            .filter(
                Connection.status
                == ConnectionStatus.DISCONNECTED
            )
            .scalar()
            or 0
        )

    def get_total_meters(self) -> int:
        return (
            self.db.query(func.count(Meter.id))
            .scalar()
            or 0
        )

    def get_faulty_meters(self) -> int:
        return (
            self.db.query(func.count(Meter.id))
            .filter(
                Meter.meter_status == MeterStatus.FAULTY
            )
            .scalar()
            or 0
        )

    def get_monthly_units_consumed(
        self,
        billing_month: str,
    ) -> Decimal:
        result = (
            self.db.query(
                func.coalesce(
                    func.sum(Bill.units_consumed),
                    0,
                )
            )
            .filter(
                Bill.billing_month == billing_month
            )
            .scalar()
        )

        return Decimal(str(result or 0))

    def get_monthly_revenue(
        self,
        billing_month: str,
    ) -> Decimal:
        result = (
            self.db.query(
                func.coalesce(
                    func.sum(Bill.total_amount),
                    0,
                )
            )
            .filter(
                Bill.billing_month == billing_month
            )
            .scalar()
        )

        return Decimal(str(result or 0))

    def get_pending_bills(self) -> int:
        return (
            self.db.query(func.count(Bill.id))
            .filter(
                Bill.bill_status == BillStatus.PENDING
            )
            .scalar()
            or 0
        )

    def get_overdue_bills(self) -> int:
        return (
            self.db.query(func.count(Bill.id))
            .filter(
                Bill.due_date < date.today(),
                Bill.bill_status != BillStatus.PAID,
            )
            .scalar()
            or 0
        )

    def get_open_complaints(self) -> int:
        return (
            self.db.query(func.count(Complaint.id))
            .filter(
                Complaint.status.in_(
                    [
                        ComplaintStatus.OPEN,
                        ComplaintStatus.ASSIGNED,
                        ComplaintStatus.IN_PROGRESS,
                    ]
                )
            )
            .scalar()
            or 0
        )

    def get_resolved_complaints(self) -> int:
        return (
            self.db.query(func.count(Complaint.id))
            .filter(
                Complaint.status
                == ComplaintStatus.RESOLVED
            )
            .scalar()
            or 0
        )

    # =========================================================
    # DAILY COLLECTION
    # =========================================================

    def get_daily_collection(
        self,
        collection_date: date,
    ):
        return (
            self.db.query(
                func.coalesce(
                    func.sum(Payment.amount),
                    0,
                ).label("total_collection"),
                func.count(Payment.id).label(
                    "successful_payments"
                ),
            )
            .filter(
                Payment.payment_status
                == PaymentStatus.SUCCESS,
                func.date(Payment.payment_date)
                == collection_date,
            )
            .one()
        )

    # =========================================================
    # MONTHLY REVENUE
    # =========================================================

    def get_monthly_revenue_report(
        self,
        billing_month: str,
    ):
        return (
            self.db.query(
                func.coalesce(
                    func.sum(Bill.total_amount),
                    0,
                ).label("total_revenue"),
                func.count(Bill.id).label(
                    "total_bills"
                ),
                func.coalesce(
                    func.sum(Bill.units_consumed),
                    0,
                ).label("total_units_consumed"),
            )
            .filter(
                Bill.billing_month == billing_month
            )
            .one()
        )

    # =========================================================
    # CUSTOMER-WISE BILLING
    # =========================================================

    def get_customer_billing(self):

        paid_subquery = (
            self.db.query(
                Bill.id.label("bill_id"),
                func.coalesce(
                    func.sum(Payment.amount),
                    0,
                ).label("paid_amount"),
            )
            .outerjoin(
                Payment,
                (
                    Payment.bill_id == Bill.id
                )
                & (
                    Payment.payment_status
                    == PaymentStatus.SUCCESS
                ),
            )
            .group_by(Bill.id)
            .subquery()
        )

        return (
            self.db.query(
                Customer.id.label("customer_id"),
                Customer.customer_number.label(
                    "customer_number"
                ),
                Customer.full_name.label(
                    "customer_name"
                ),
                func.count(
                    Bill.id
                ).label("total_bills"),
                func.coalesce(
                    func.sum(
                        Bill.units_consumed
                    ),
                    0,
                ).label(
                    "total_units_consumed"
                ),
                func.coalesce(
                    func.sum(
                        Bill.total_amount
                    ),
                    0,
                ).label(
                    "total_billed_amount"
                ),
                func.coalesce(
                    func.sum(
                        paid_subquery.c.paid_amount
                    ),
                    0,
                ).label(
                    "total_paid_amount"
                ),
            )
            .outerjoin(
                Connection,
                Connection.customer_id
                == Customer.id,
            )
            .outerjoin(
                Bill,
                Bill.connection_id
                == Connection.id,
            )
            .outerjoin(
                paid_subquery,
                paid_subquery.c.bill_id
                == Bill.id,
            )
            .group_by(
                Customer.id,
                Customer.customer_number,
                Customer.full_name,
            )
            .order_by(Customer.id.asc())
            .all()
        )

    # =========================================================
    # CONNECTION-WISE CONSUMPTION
    # =========================================================

    def get_connection_consumption(self):
        return (
            self.db.query(
                Connection.id.label(
                    "connection_id"
                ),
                Connection.connection_number.label(
                    "connection_number"
                ),
                Connection.customer_id.label(
                    "customer_id"
                ),
                func.coalesce(
                    func.sum(
                        Bill.units_consumed
                    ),
                    0,
                ).label(
                    "units_consumed"
                ),
                func.coalesce(
                    func.sum(
                        Bill.total_amount
                    ),
                    0,
                ).label(
                    "total_billed_amount"
                ),
            )
            .outerjoin(
                Bill,
                Bill.connection_id
                == Connection.id,
            )
            .group_by(
                Connection.id,
                Connection.connection_number,
                Connection.customer_id,
            )
            .order_by(Connection.id.asc())
            .all()
        )

    # =========================================================
    # TECHNICIAN PERFORMANCE
    # =========================================================

    def get_technician_performance(self):
        return (
            self.db.query(
                User.id.label(
                    "technician_id"
                ),
                User.full_name.label(
                    "technician_name"
                ),
                func.count(
                    Complaint.id
                ).label(
                    "assigned_complaints"
                ),
                func.sum(
                    case(
                        (
                            Complaint.status
                            == ComplaintStatus.RESOLVED,
                            1,
                        ),
                        else_=0,
                    )
                ).label(
                    "resolved_complaints"
                ),
                func.sum(
                    case(
                        (
                            Complaint.status.in_(
                                [
                                    ComplaintStatus.OPEN,
                                    ComplaintStatus.ASSIGNED,
                                    ComplaintStatus.IN_PROGRESS,
                                ]
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label(
                    "open_complaints"
                ),
            )
            .join(
                Complaint,
                Complaint.assigned_to == User.id,
            )
            .filter(
                User.role
                == UserRole.FIELD_TECHNICIAN
            )
            .group_by(
                User.id,
                User.full_name,
            )
            .order_by(User.id.asc())
            .all()
        )

    # =========================================================
    # COMPLAINT RESOLUTION
    # =========================================================

    def get_complaint_resolution(self):

        complaints = (
            self.db.query(Complaint)
            .filter(
                Complaint.status.in_(
                    [
                        ComplaintStatus.RESOLVED,
                        ComplaintStatus.CLOSED,
                    ]
                )
            )
            .all()
        )

        total = (
            self.db.query(
                func.count(Complaint.id)
            )
            .scalar()
            or 0
        )

        resolved = (
            self.db.query(
                func.count(Complaint.id)
            )
            .filter(
                Complaint.status
                == ComplaintStatus.RESOLVED
            )
            .scalar()
            or 0
        )

        closed = (
            self.db.query(
                func.count(Complaint.id)
            )
            .filter(
                Complaint.status
                == ComplaintStatus.CLOSED
            )
            .scalar()
            or 0
        )

        open_count = (
            self.db.query(
                func.count(Complaint.id)
            )
            .filter(
                Complaint.status.in_(
                    [
                        ComplaintStatus.OPEN,
                        ComplaintStatus.ASSIGNED,
                        ComplaintStatus.IN_PROGRESS,
                    ]
                )
            )
            .scalar()
            or 0
        )

        resolution_days = []

        for complaint in complaints:
            if (
                complaint.created_at
                and complaint.updated_at
            ):
                difference = (
                    complaint.updated_at
                    - complaint.created_at
                )

                resolution_days.append(
                    difference.total_seconds()
                    / 86400
                )

        if resolution_days:
            average_days = (
                sum(resolution_days)
                / len(resolution_days)
            )
        else:
            average_days = 0.0

        return (
            total,
            resolved,
            closed,
            open_count,
            average_days,
        )

    # =========================================================
    # OUTSTANDING PAYMENTS
    # =========================================================

    def get_outstanding_payments(self):

        paid_subquery = (
            self.db.query(
                Payment.bill_id.label(
                    "bill_id"
                ),
                func.coalesce(
                    func.sum(Payment.amount),
                    0,
                ).label(
                    "paid_amount"
                ),
            )
            .filter(
                Payment.payment_status
                == PaymentStatus.SUCCESS
            )
            .group_by(
                Payment.bill_id
            )
            .subquery()
        )

        return (
            self.db.query(
                Bill.id.label(
                    "bill_id"
                ),
                Bill.connection_id.label(
                    "connection_id"
                ),
                Bill.billing_month.label(
                    "billing_month"
                ),
                Bill.due_date.label(
                    "due_date"
                ),
                Bill.total_amount.label(
                    "total_amount"
                ),
                func.coalesce(
                    paid_subquery.c.paid_amount,
                    0,
                ).label(
                    "paid_amount"
                ),
            )
            .outerjoin(
                paid_subquery,
                paid_subquery.c.bill_id
                == Bill.id,
            )
            .filter(
                Bill.bill_status
                != BillStatus.PAID
            )
            .order_by(
                Bill.due_date.asc(),
                Bill.id.asc(),
            )
            .all()
        )