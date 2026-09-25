from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.config import settings
from app.database import Base, engine

# Import models so SQLAlchemy registers all tables
from app.models.user import User
from app.models.customer import Customer
from app.models.connection import Connection
from app.models.meter import Meter
from app.models.meter_reading import MeterReading
from app.models.bill import Bill
from app.models.tariff import Tariff
from app.models.payment import Payment
from app.models.complaint import Complaint, ComplaintHistory
from app.models.technician import Technician
from app.models.service_request import ServiceRequest
from app.models.notification import Notification
from app.models.audit_log import AuditLog

# Import routers
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.customers import router as customers_router
from app.routes.connections import router as connections_router
from app.routes.meters import router as meters_router
from app.routes.meter_readings import router as meter_readings_router
from app.routes.analytics import router as analytics_router
from app.routes.dashboard import router as dashboard_router

from app.routes.bills import (
    router as bills_router,
    customer_bills_router,
    connection_bills_router,
)

from app.routes.tariffs import router as tariffs_router

from app.routes.payments import (
    router as payments_router,
    bill_payments_router,
)

from app.routes.complaints import router as complaints_router
from app.routes.technicians import router as technicians_router

from app.routes.service_requests import (
    router as service_requests_router,
)

from app.routes.notifications import router as notifications_router

# Global exception handlers
from app.utils.exception_handlers import (
    database_exception_handler,
    general_exception_handler,
    integrity_error_handler,
    validation_exception_handler,
)

# Rate limiter
from app.utils.rate_limit import rate_limiter


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Smart Electricity Utility Management System",
)


# ============================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    IntegrityError,
    integrity_error_handler,
)

app.add_exception_handler(
    SQLAlchemyError,
    database_exception_handler,
)

app.add_exception_handler(
    Exception,
    general_exception_handler,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# RATE LIMITING
# ============================================================
#
# Rate limiting is intentionally applied only to authentication
# endpoints. Applying the limiter to every API request causes
# normal application traffic and automated tests to be blocked.
#
# Authentication endpoints are the most important endpoints to
# protect against repeated requests such as login/register abuse.
# ============================================================

@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    rate_limited_paths = {
        "/auth/login",
        "/auth/register",
    }

    if request.url.path in rate_limited_paths:
        rate_limiter.check(request)

    response = await call_next(request)

    return response


# ============================================================
# REGISTER ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(customers_router)
app.include_router(connections_router)
app.include_router(meters_router)
app.include_router(meter_readings_router)

app.include_router(bills_router)
app.include_router(customer_bills_router)
app.include_router(connection_bills_router)

app.include_router(tariffs_router)

app.include_router(payments_router)
app.include_router(bill_payments_router)

app.include_router(complaints_router)

app.include_router(technicians_router)
app.include_router(service_requests_router)
app.include_router(analytics_router)
app.include_router(dashboard_router)
app.include_router(notifications_router)


# ============================================================
# ROOT / HEALTH
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Smart Electricity Utility Management System API",
        "version": settings.app_version,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }