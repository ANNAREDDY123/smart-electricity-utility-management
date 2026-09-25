from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bill import Bill
from app.models.connection import Connection
from app.models.customer import Customer


class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_connection_monthly(
        self,
        connection_id: int,
    ):
        return (
            self.db.query(
                Bill.billing_month.label("month"),
                func.sum(Bill.units_consumed).label(
                    "units_consumed"
                ),
                func.sum(Bill.total_amount).label(
                    "bill_amount"
                ),
            )
            .filter(
                Bill.connection_id == connection_id
            )
            .group_by(
                Bill.billing_month
            )
            .order_by(
                Bill.billing_month.asc()
            )
            .all()
        )

    def get_connection_yearly(
        self,
        connection_id: int,
    ):
        year_expression = func.substr(
            Bill.billing_month,
            1,
            4,
        )

        return (
            self.db.query(
                year_expression.label("year"),
                func.sum(Bill.units_consumed).label(
                    "units_consumed"
                ),
                func.sum(Bill.total_amount).label(
                    "bill_amount"
                ),
            )
            .filter(
                Bill.connection_id == connection_id
            )
            .group_by(
                year_expression
            )
            .order_by(
                year_expression.asc()
            )
            .all()
        )

    def get_connection_usage(self):
        return (
            self.db.query(
                Connection.id.label(
                    "connection_id"
                ),
                Connection.connection_number.label(
                    "connection_number"
                ),
                func.coalesce(
                    func.sum(Bill.units_consumed),
                    0,
                ).label("units_consumed"),
                func.coalesce(
                    func.sum(Bill.total_amount),
                    0,
                ).label("bill_amount"),
            )
            .outerjoin(
                Bill,
                Bill.connection_id == Connection.id,
            )
            .group_by(
                Connection.id,
                Connection.connection_number,
            )
            .order_by(
                Connection.id.asc()
            )
            .all()
        )

    def get_customer_usage(self):
        return (
            self.db.query(
                Customer.id.label("customer_id"),
                Customer.customer_number.label(
                    "customer_number"
                ),
                Customer.full_name.label(
                    "customer_name"
                ),
                func.coalesce(
                    func.sum(Bill.units_consumed),
                    0,
                ).label("units_consumed"),
                func.coalesce(
                    func.sum(Bill.total_amount),
                    0,
                ).label("bill_amount"),
            )
            .outerjoin(
                Connection,
                Connection.customer_id == Customer.id,
            )
            .outerjoin(
                Bill,
                Bill.connection_id == Connection.id,
            )
            .group_by(
                Customer.id,
                Customer.customer_number,
                Customer.full_name,
            )
            .order_by(
                Customer.id.asc()
            )
            .all()
        )

    def get_highest_consuming_connections(
        self,
        limit: int = 10,
    ):
        return (
            self.db.query(
                Connection.id.label(
                    "connection_id"
                ),
                Connection.connection_number.label(
                    "connection_number"
                ),
                func.coalesce(
                    func.sum(Bill.units_consumed),
                    0,
                ).label("units_consumed"),
                func.coalesce(
                    func.sum(Bill.total_amount),
                    0,
                ).label("bill_amount"),
            )
            .outerjoin(
                Bill,
                Bill.connection_id == Connection.id,
            )
            .group_by(
                Connection.id,
                Connection.connection_number,
            )
            .order_by(
                func.coalesce(
                    func.sum(Bill.units_consumed),
                    0,
                ).desc(),
                Connection.id.asc(),
            )
            .limit(limit)
            .all()
        )

    def get_average_monthly_consumption(self):
        monthly_totals = (
            self.db.query(
                Bill.billing_month.label("month"),
                func.sum(
                    Bill.units_consumed
                ).label("units_consumed"),
            )
            .group_by(
                Bill.billing_month
            )
            .subquery()
        )

        return (
            self.db.query(
                func.avg(
                    monthly_totals.c.units_consumed
                )
            )
            .scalar()
        )