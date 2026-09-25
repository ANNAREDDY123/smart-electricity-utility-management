from pydantic import BaseModel


class DashboardResponse(BaseModel):
    total_customers: int
    active_connections: int
    disconnected_connections: int
    total_meters: int
    faulty_meters: int
    monthly_units_consumed: float
    monthly_revenue: float
    pending_bills: int
    overdue_bills: int
    open_complaints: int
    resolved_complaints: int


class DailyCollectionResponse(BaseModel):
    collection_date: str
    total_collection: float
    successful_payments: int


class MonthlyRevenueResponse(BaseModel):
    billing_month: str
    total_revenue: float
    total_bills: int
    total_units_consumed: float


class CustomerBillingResponse(BaseModel):
    customer_id: int
    customer_number: str
    customer_name: str
    total_bills: int
    total_units_consumed: float
    total_billed_amount: float
    total_paid_amount: float
    outstanding_amount: float


class ConnectionConsumptionResponse(BaseModel):
    connection_id: int
    connection_number: str
    customer_id: int
    units_consumed: float
    total_billed_amount: float


class TechnicianPerformanceResponse(BaseModel):
    technician_id: int
    technician_name: str
    assigned_complaints: int
    resolved_complaints: int
    open_complaints: int


class ComplaintResolutionResponse(BaseModel):
    total_complaints: int
    resolved_complaints: int
    closed_complaints: int
    open_complaints: int
    average_resolution_days: float


class OutstandingPaymentResponse(BaseModel):
    bill_id: int
    connection_id: int
    billing_month: str
    due_date: str
    total_amount: float
    paid_amount: float
    outstanding_amount: float