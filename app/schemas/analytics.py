from decimal import Decimal

from pydantic import BaseModel


class MonthlyConsumptionResponse(BaseModel):
    month: str
    units_consumed: Decimal
    bill_amount: Decimal


class YearlyConsumptionResponse(BaseModel):
    year: int
    units_consumed: Decimal
    bill_amount: Decimal


class ConnectionUsageResponse(BaseModel):
    connection_id: int
    connection_number: str
    units_consumed: Decimal
    bill_amount: Decimal


class CustomerUsageResponse(BaseModel):
    customer_id: int
    customer_number: str
    customer_name: str
    units_consumed: Decimal
    bill_amount: Decimal


class HighestConsumptionResponse(BaseModel):
    connection_id: int
    connection_number: str
    units_consumed: Decimal
    bill_amount: Decimal


class AverageMonthlyConsumptionResponse(BaseModel):
    average_monthly_consumption: Decimal