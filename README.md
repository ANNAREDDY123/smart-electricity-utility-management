# Smart Electricity Utility Management System

A backend REST API for managing electricity utility operations including customers, electricity connections, smart meters, meter readings, tariffs, billing, payments, complaints, technicians, service requests, analytics, dashboards, reports, notifications, authentication, authorization, and audit logging.

## Project Overview

The Smart Electricity Utility Management System is developed using FastAPI and SQLAlchemy with a clean layered architecture.

The system provides secure REST APIs for managing the complete electricity utility lifecycle:

Customer → Connection → Meter → Meter Reading → Tariff → Bill → Payment

It also supports complaints, technicians, service requests, consumption analytics, dashboards, reports, notifications, and security controls.

---

## Technology Stack

- Python 3.14+
- FastAPI
- SQLAlchemy ORM
- Pydantic
- Pydantic Settings
- SQLite / PostgreSQL
- JWT Authentication
- Password Hashing with Argon2
- Alembic
- Pytest
- HTTPX
- Uvicorn

---

## Features

### Authentication & Authorization

- User registration
- User login
- JWT access tokens
- JWT refresh tokens
- Role-based access control
- Active-user validation
- Password hashing
- Protected API endpoints

### Customer Management

- Create customer
- View customers
- View customer by ID
- Update customer
- Soft delete customer
- Search and filtering
- Pagination and sorting

### Connection Management

- Create electricity connection
- View connections
- Update connection
- Disconnect connection
- Connection type management
- Connection status management

### Smart Meter Management

- Install meter
- View meters
- Update meter
- Replace meter
- Meter status management
- Meter reading management

### Meter Readings

- Add meter readings
- Validate reading sequence
- Calculate units consumed
- Prevent duplicate billing-period readings
- Connection-wise reading retrieval
- Meter-wise reading retrieval

### Tariff Management

- Create tariff
- Update tariff
- View tariffs
- Apply applicable tariff
- Tariff slab validation
- Effective-date validation
- Soft deletion through inactive status

### Billing

- Generate electricity bills
- Calculate energy charges
- Fixed charges
- Tax
- Late fees
- Discounts
- Due dates
- Bill status management
- Customer-wise bills
- Connection-wise bills

### Payments

- Record payments
- UPI
- Card
- Net Banking
- Wallet
- Payment status management
- Transaction ID uniqueness
- Payment history

### Complaint Management

- Raise complaints
- Complaint priority
- Complaint assignment
- Complaint status management
- Complaint history
- Complaint resolution

### Technician Management

- Create technicians
- View technicians
- Update technician availability
- Assign technicians to operational activities

### Service Requests

Supported request types include:

- New Connection
- Load Change
- Meter Replacement
- Name Change
- Address Change
- Disconnection
- Reconnection

Supported statuses:

- Submitted
- Under Review
- Approved
- Rejected
- Completed

### Consumption Analytics

- Monthly consumption
- Yearly consumption
- Connection-wise consumption
- Customer-wise consumption
- Highest consuming connections
- Average monthly consumption

### Dashboard & Reports

Dashboard metrics include:

- Total customers
- Active connections
- Disconnected connections
- Total meters
- Faulty meters
- Monthly units consumed
- Monthly revenue
- Pending bills
- Overdue bills
- Open complaints
- Resolved complaints

Reports include:

- Daily collection report
- Monthly revenue report
- Customer-wise billing report
- Connection-wise consumption report
- Technician performance report
- Complaint resolution report
- Outstanding payment report

### Notifications

Notifications are implemented using FastAPI BackgroundTasks.

Supported notification events include:

- Bill generated
- Bill due reminder
- Payment success
- Payment failure
- Bill overdue
- Complaint assigned
- Complaint resolved
- Service request approved
- Meter replacement completed

### Security & Data Integrity

- JWT authentication
- Role-based authorization
- Password hashing
- Foreign key constraints
- Unique constraints
- Database transactions
- Global exception handling
- Audit logging
- Soft delete
- CORS
- Rate limiting
- Request validation

---

## Project Architecture

The project follows a layered clean architecture:

```text
Client
  │
  ▼
FastAPI Routes
  │
  ▼
Pydantic Schemas
  │
  ▼
Service Layer
  │
  ▼
Repository Layer
  │
  ▼
SQLAlchemy ORM / Models
  │
  ▼
SQLite / PostgreSQL

Layers

Routes

Handle HTTP requests, authentication dependencies, authorization and API responses.

Schemas

Provide request validation and response serialization using Pydantic.

Services

Contain business rules and application logic.

Repositories

Handle database queries and persistence operations.

Models

Define SQLAlchemy database tables, relationships, constraints and indexes.

Utils

Contain authentication, security, exception handling and rate-limiting utilities.

Project Structure
smart-electricity-utility-management/
│
├── app/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── routes/
│   ├── utils/
│   └── tests/
│
├── alembic/
│   └── versions/
│
├── docs/
│   ├── screenshots/
│   ├── ER_DIAGRAM.png
│   └── ARCHITECTURE_DIAGRAM.png
│
├── postman/
│   └── Smart-Electricity-Utility-Management.postman_collection.json
│
├── .env.example
├── .gitignore
├── alembic.ini
├── main.py
├── requirements.txt
└── README.md
Environment Configuration

Create a .env file from .env.example.

Example:

APP_NAME=Smart Electricity Utility Management System
APP_VERSION=1.0.0

DATABASE_URL=sqlite:///./electricity_utility.db

SECRET_KEY=replace-with-a-strong-random-secret-key
ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

Do not commit the actual .env file to GitHub.

Installation

Clone the repository:

git clone https://github.com/ANNAREDDY123/smart-electricity-utility-management.git

Navigate into the project:

cd smart-electricity-utility-management

Create a virtual environment:

python -m venv venv

Activate the virtual environment on Windows:

venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Create the environment file:

.env.example → .env

Update the configuration values in .env.

Database

The project supports SQLite for development and PostgreSQL for production environments.

Default SQLite configuration:

DATABASE_URL=sqlite:///./electricity_utility.db

Database tables are managed using SQLAlchemy and Alembic migrations.

Alembic Migrations

Create a migration:

alembic revision --autogenerate -m "Initial migration"

Apply migrations:

alembic upgrade head

Check migration status:

alembic current
Running the Application

Start the FastAPI server:

uvicorn app.main:app --reload

The application will be available at:

http://127.0.0.1:8000
API Documentation
Swagger UI
http://127.0.0.1:8000/docs
ReDoc
http://127.0.0.1:8000/redoc

Swagger UI provides interactive API testing and request/response documentation.

Main API Modules
Module	Endpoint
Authentication	/auth
Users	/users
Customers	/customers
Connections	/connections
Smart Meters	/meters
Meter Readings	/meter-readings
Tariffs	/tariffs
Bills	/bills
Payments	/payments
Complaints	/complaints
Technicians	/technicians
Service Requests	/service-requests
Analytics	/analytics
Dashboard	/dashboard
Reports	/reports
Notifications	/notifications
Mandatory Demo Flow

The complete business workflow is:

Register
   ↓
Create Customer
   ↓
Create Connection
   ↓
Install Meter
   ↓
Add Meter Reading
   ↓
Apply Tariff
   ↓
Generate Bill
   ↓
Make Payment
   ↓
Raise Complaint
   ↓
Assign Technician
   ↓
Resolve Complaint
   ↓
View Consumption Analytics
   ↓
View Dashboard
Testing

The project uses Pytest for automated testing.

Run all tests:

pytest -q

Run a specific test file:

pytest app/tests/test_customers.py -q

Run the security tests:

pytest app/tests/test_level16_security.py -q

The test suite covers authentication, customers, connections, meters, meter readings, billing, tariffs, payments, complaints, technicians, service requests, analytics, dashboards, notifications and security.

Security

The application implements:

JWT access-token authentication
Refresh tokens
Role-based authorization
Password hashing
Request validation
Database constraints
Global exception handling
Rate limiting
CORS
Audit logging
Soft-delete handling
Database Integrity

The application uses:

Foreign key constraints
Unique constraints
Database indexes
Transaction management
SQLAlchemy ORM
Proper database session handling
Validation at the API and service layers

Important indexed fields include:

customer_number
connection_number
meter_number
billing_month
transaction_id
complaint status
Documentation

Project submission documentation includes:

docs/
├── screenshots/
├── ER_DIAGRAM.png
└── ARCHITECTURE_DIAGRAM.png

Additional API testing documentation:

postman/
└── Smart-Electricity-Utility-Management.postman_collection.json
Submission Checklist
 GitHub Repository
 Complete README.md
 .env.example
 Alembic migration files
 Swagger screenshots
 Postman collection
 Unit test cases
 ER Diagram
 Architecture Diagram
Repository

GitHub:

https://github.com/ANNAREDDY123/smart-electricity-utility-management
