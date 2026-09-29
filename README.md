# EVE Healthcare — Diagnostic Booking & Payment API

A backend service for **diagnostic test discovery, booking, simulated payments, and payment webhooks**, built as part of the EVE Healthcare SDE Intern Backend Engineering assignment.

The project focuses on clean API design, authorization, price consistency, booking/payment state management, and **idempotent payment webhook processing**.

---

## 1. Tech Stack

- **Python**
- **Django**
- **Django REST Framework**
- **PostgreSQL**
- **SimpleJWT** for JWT authentication
- **drf-spectacular / OpenAPI / Swagger UI**
- **Docker & Docker Compose**
- **pytest / pytest-django** for automated tests

---

## 2. Core Features

### Authentication
- User signup
- Email/password login
- JWT access and refresh tokens
- Protected endpoints using JWT authentication

### Diagnostic Centres & Tests
- Create, update, delete and retrieve diagnostic centres
- Create, update, delete and retrieve diagnostic tests
- Associate tests with diagnostic centres
- Maintain centre-specific test prices
- Diagnostic management write operations are restricted to staff users

### Bookings
- Authenticated users can create bookings
- Users can view only their own bookings
- Booking cancellation
- Booking stores the **price snapshot at booking time**
- Booking state management:
  - `PENDING`
  - `CONFIRMED`
  - `FAILED`
  - `CANCELLED`

### Payments
- Initialize a payment for a booking
- Simulate payment success/failure
- Payment amount is derived from the booking
- Successful payment confirms the booking
- Failed payment marks the booking as failed

### Payment Webhooks
- Simulated provider webhook endpoint
- Idempotent webhook processing using a unique event ID
- Repeated webhook events do not create duplicate payment effects
- Provider payment IDs are used to resolve the internal payment

---

## 3. Architecture

The project follows a **Service–Selector oriented architecture**.

```text
                    ┌──────────────────────┐
                    │      API Client      │
                    │   Swagger / Client   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │        Views         │
                    │ HTTP / Auth / Status │
                    └──────────┬───────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
       ┌────────────────┐            ┌────────────────┐
       │    Services    │            │    Selectors   │
       │ Business logic │            │ Read/query     │
       │ State changes  │            │ operations     │
       └────────┬───────┘            └────────┬───────┘
                │                             │
                └──────────────┬──────────────┘
                               ▼
                    ┌──────────────────────┐
                    │       Models         │
                    │   PostgreSQL / ORM   │
                    └──────────────────────┘
```

### Layer responsibilities

**Views**
- Handle HTTP requests and responses
- Apply authentication/permission classes
- Pass validated data to services
- Return serialized responses

**Serializers**
- Validate incoming API data
- Serialize outgoing data

**Services**
- Contain business workflows
- Handle booking/payment state transitions
- Perform transactional operations

**Selectors**
- Encapsulate read/query logic
- Apply user-scoped access to protected resources

**Models**
- Define persistence and database relationships

---

## 4. Database Design

The main entities are:

```text
User
 │
 └──────────────< Booking >────────────── DiagnosticTest
                       │                         │
                       │                         │
                       │                         │
                       ▼                         ▼
                    Payment                 CentreTest
                                               │
                                               ▼
                                      DiagnosticCentre


Payment
   │
   └──────────────< PaymentWebhookEvent
```

### Main relationships

- A user can have multiple bookings.
- A booking belongs to one diagnostic centre and one diagnostic test.
- A diagnostic centre can offer multiple diagnostic tests.
- `CentreTest` stores the **centre-specific price**.
- A booking stores its own `amount` so later price changes do not alter existing bookings.
- A booking has one payment.
- A payment can have multiple webhook events.
- `PaymentWebhookEvent.event_id` is unique for webhook idempotency.
- `Payment.provider_payment_id` is unique.

---

## 5. Booking State Flow

```text
                  ┌──────────────┐
                  │   PENDING    │
                  └──────┬───────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        CONFIRMED      FAILED    CANCELLED
              │
              ▼
          CANCELLED
```

A failed or cancelled booking is not reused for another payment attempt. A new booking can be created when a new attempt is required.

---

## 6. Payment Flow

### Successful payment

```text
Booking PENDING
      │
      ▼
Initialize Payment
      │
      ▼
Payment PENDING
      │
      ▼
Simulate SUCCESS
      │
      ├──────────────► Payment SUCCESS
      │
      └──────────────► Booking CONFIRMED
```

### Failed payment

```text
Booking PENDING
      │
      ▼
Initialize Payment
      │
      ▼
Payment PENDING
      │
      ▼
Simulate FAILED
      │
      ├──────────────► Payment FAILED
      │
      └──────────────► Booking FAILED
```

---

## 7. Webhook Idempotency

The webhook processor is designed so that the same provider event can safely be delivered more than once.

A unique `event_id` is stored in `PaymentWebhookEvent`.

```text
Provider Webhook
       │
       ▼
Check event_id
       │
   ┌───┴───────────────┐
   │                   │
New event          Existing event
   │                   │
   ▼                   ▼
Process event       Ignore duplicate
   │                   │
   └──────────┬────────┘
              ▼
          HTTP 200
```

The webhook resolves the payment using `provider_payment_id`.

Terminal booking/payment states are protected from contradictory late webhook updates.

---

# 8. Project Structure

A simplified structure is:

```text
EVE HEALTHCARE PROJECT/
│
├── apps/
│   ├── users/
│   │   ├── migrations/
│   │   ├── repositories/
│   │   ├── selectors/
│   │   ├── serializers/
│   │   ├── services/
│   │   ├── views/
│   │   ├── models.py
│   │   └── urls.py
│   │
│   ├── diagnostics/
│   │   ├── migrations/
│   │   ├── repositories/
│   │   ├── selectors/
│   │   ├── serializers/
│   │   ├── services/
│   │   ├── views/
│   │   ├── models.py
│   │   └── urls.py
│   │
│   ├── bookings/
│   └── payments/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

# 9. Setup

## Prerequisites

Install:

- Docker Desktop
- Git

The recommended application setup uses **Docker + PostgreSQL**.

---

## 10. Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Fill in the required environment variables in `.env`.

Do **not** commit `.env` to Git.

---

# 11. Run with Docker

From the project root:

```bash
docker compose up --build
```

Keep this terminal running.

In another terminal:

```bash
docker compose exec backend python manage.py migrate
```

If migrations are already applied, Django will report:

```text
No migrations to apply.
```

This is normal.

The backend will be available at:

```text
http://127.0.0.1:8000/
```

---

# 12. Swagger API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/api/schema/swagger-ui/
```

Open Swagger to interactively test the APIs.

The recommended testing flow is provided below.

---

# 13. API Testing Guide

This section is intended to let a reviewer validate the main functionality without needing to inspect the source code first.

## Step 1 — Create a normal user

**POST `/api/auth/signup/`**

```json
{
  "email": "patient@example.com",
  "password": "Test@12345",
  "password_confirm": "Test@12345"
}
```

Expected:

```text
201 Created
```

---

## Step 2 — Login

**POST `/api/auth/login/`**

```json
{
  "email": "patient@example.com",
  "password": "Test@12345"
}
```

Copy the returned `access` token.

In Swagger, click **Authorize** and provide the access token.

---

## Step 3 — Create diagnostic data

Diagnostic centre/test write operations require a **staff/superuser account**.

Authorize Swagger with a staff account.

### Create a test

**POST `/api/tests/`**

```json
{
  "name": "Blood Test",
  "description": "Complete blood count test"
}
```

Note the returned test ID.

### Create a centre

**POST `/api/centres/`**

```json
{
  "name": "EVE Diagnostics",
  "location": "Ahmedabad"
}
```

Note the returned centre ID.

### Add the test to the centre

**POST `/api/centres/{centre_id}/tests/`**

Example:

```text
centre_id = 1
```

```json
{
  "test_id": 2,
  "price": "500.00"
}
```

This creates the centre-test relationship with a price of ₹500.

---

## Step 4 — Switch back to the normal user

Login again as the patient user and authorize Swagger with the patient's access token.

---

## Step 5 — Create a booking

**POST `/api/bookings/`**

```json
{
  "diagnostic_centre": 1,
  "diagnostic_test": 2,
  "appointment_datetime": "2026-10-01T10:00:00Z"
}
```

Expected:

```text
201 Created
status = PENDING
amount = 500.00
```

The amount is stored as a booking-time price snapshot.

---

## Step 6 — Initialize payment

**POST `/api/payments/`**

```json
{
  "booking_id": 1
}
```

Expected:

```text
201 Created
payment.status = PENDING
amount = 500.00
```

Note the returned payment ID and `provider_payment_id`.

---

## Step 7 — Simulate successful payment

**POST `/api/payments/{id}/simulate/`**

For payment ID `1`:

```json
{
  "result": "SUCCESS"
}
```

Expected:

```text
payment.status = SUCCESS
booking.status = CONFIRMED
```

---

## Step 8 — Verify the booking

**GET `/api/bookings/{id}/`**

For booking ID `1`:

```text
200 OK
```

Expected:

```json
{
  "id": 1,
  "amount": "500.00",
  "status": "CONFIRMED"
}
```

---

# 14. Failed Payment Test

Create another booking and initialize its payment.

Then call:

**POST `/api/payments/{id}/simulate/`**

```json
{
  "result": "FAILED"
}
```

Expected:

```text
payment.status = FAILED
booking.status = FAILED
```

This verifies the failure state transition.

---

# 15. Webhook Idempotency Test

Use:

**POST `/api/payments/webhook/`**

Replace `pay_xxxxxxxxx` with the `provider_payment_id` returned by payment initialization.

```json
{
  "event_id": "evt_test_001",
  "provider_payment_id": "pay_xxxxxxxxx",
  "status": "SUCCESS"
}
```

Expected:

```text
200 OK
{
  "received": true
}
```

### Repeat the exact same request

Send the same payload again:

```json
{
  "event_id": "evt_test_001",
  "provider_payment_id": "pay_xxxxxxxxx",
  "status": "SUCCESS"
}
```

Expected:

```text
200 OK
{
  "received": true
}
```

The repeated event must not create a duplicate payment or corrupt the existing booking/payment state.

---

# 16. Authorization Test

Create/login as a second normal user.

Attempt to access a booking belonging to the first user:

**GET `/api/bookings/1/`**

Expected:

```text
404 Not Found
```

The API uses user-scoped queries so that users cannot retrieve another user's booking.

---

# 17. Important API Behaviors

| Scenario | Expected behavior |
|---|---|
| Unauthenticated protected endpoint | `401 Unauthorized` |
| Normal user modifies diagnostic data | `403 Forbidden` |
| User accesses another user's booking | `404 Not Found` |
| Successful payment | Payment `SUCCESS`, Booking `CONFIRMED` |
| Failed payment | Payment `FAILED`, Booking `FAILED` |
| Duplicate webhook | Safely ignored / idempotent |
| Booking creation | Current centre price is captured |
| Invalid booking/payment ID | Appropriate `4xx` response |

---

# 18. Automated Tests

The project includes automated tests covering application behavior.

Run the test suite using the isolated test configuration:

```bash
docker compose exec backend pytest --ds=tests.settings_test
```

The test configuration uses SQLite for isolated automated testing.

The application itself has also been verified separately using the Docker/PostgreSQL runtime.

> Note: the automated SQLite test configuration should not be interpreted as a PostgreSQL concurrency test.

---

# 19. Database Migrations

Create migrations when models change:

```bash
docker compose exec backend python manage.py makemigrations
```

Apply migrations:

```bash
docker compose exec backend python manage.py migrate
```

---

# 20. Create a Staff/Superuser

To create a staff account:

```bash
docker compose exec backend python manage.py createsuperuser
```

Follow Django's prompts.

Use this account to perform diagnostic centre/test management operations through Swagger.

---

# 21. Useful Docker Commands

### Start services

```bash
docker compose up
```

### Start in detached mode

```bash
docker compose up -d
```

### Stop services

```bash
docker compose down
```

### View logs

```bash
docker compose logs -f backend
```

### Open a Django shell

```bash
docker compose exec backend python manage.py shell
```

### Run migrations

```bash
docker compose exec backend python manage.py migrate
```

---

# 22. Security & Data Handling

- JWT authentication protects user-specific APIs.
- Users can access only their own bookings/payments.
- Diagnostic write operations are staff-restricted.
- Booking amount is stored independently of later diagnostic price changes.
- Payment provider IDs are unique.
- Webhook event IDs are unique for idempotency.
- `.env` is excluded from version control.
- The webhook endpoint is intentionally unauthenticated because it represents a simulated external provider callback. In a real payment integration, provider signature/shared-secret verification would be required.

---

# 23. API Endpoint Summary

## Authentication

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/signup/` | Create user |
| POST | `/api/auth/login/` | Obtain JWT tokens |
| GET | `/api/auth/me/` | Current authenticated user |

## Diagnostic Centres

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/centres/` | List centres |
| POST | `/api/centres/` | Create centre |
| GET | `/api/centres/{id}/` | Get centre |
| PATCH | `/api/centres/{id}/` | Update centre |
| DELETE | `/api/centres/{id}/` | Delete centre |
| GET | `/api/centres/{centre_id}/tests/` | List centre tests |
| POST | `/api/centres/{centre_id}/tests/` | Add test to centre |
| PATCH | `/api/centres/{centre_id}/tests/{test_id}/` | Update centre-test price |
| DELETE | `/api/centres/{centre_id}/tests/{test_id}/` | Remove test from centre |

## Diagnostic Tests

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/tests/` | List tests |
| POST | `/api/tests/` | Create test |
| GET | `/api/tests/{id}/` | Get test |
| PATCH | `/api/tests/{id}/` | Update test |
| DELETE | `/api/tests/{id}/` | Delete test |

## Bookings

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/bookings/` | List current user's bookings |
| POST | `/api/bookings/` | Create booking |
| GET | `/api/bookings/{id}/` | Get own booking |
| POST | `/api/bookings/{id}/cancel/` | Cancel own booking |

## Payments

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/payments/` | Initialize payment |
| POST | `/api/payments/{id}/simulate/` | Simulate payment result |
| POST | `/api/payments/webhook/` | Process provider webhook |

---

# 24. Design Decisions

### Why store booking amount?

The centre's test price may change after a booking is created.

Therefore:

```text
CentreTest.price
       │
       │ booking created
       ▼
Booking.amount
```

The booking keeps the amount that was valid when the booking was made.

### Why use services?

Business workflows such as booking creation, cancellation, payment processing, and webhook handling are kept outside the HTTP views.

This keeps views focused on HTTP concerns and makes business logic easier to test.

### Why use selectors?

Selectors centralize database read/query logic and make user-scoped access explicit.

### Why use an idempotency ledger?

Payment providers may retry webhook delivery.

The unique webhook event ID allows the backend to recognize an event that has already been processed.

---

# 25. Submission Checklist

Before submitting the repository, verify:

- [ ] `.env` is not committed
- [ ] `.env.example` is present
- [ ] `requirements.txt` is present
- [ ] `Dockerfile` is present
- [ ] `docker-compose.yml` is present
- [ ] migrations are committed
- [ ] tests are committed
- [ ] README contains setup instructions
- [ ] README contains API testing flow
- [ ] Swagger opens successfully
- [ ] Docker + PostgreSQL startup works
- [ ] JWT authentication works
- [ ] Booking flow works
- [ ] Successful payment flow works
- [ ] Failed payment flow works
- [ ] Webhook idempotency works
- [ ] User authorization works

---

## 26. Quick Reviewer Flow

If you want to verify the main functionality quickly:

```text
1. docker compose up --build
2. migrate
3. Open Swagger
4. Create/Login user
5. Authorize JWT
6. Login staff
7. Create Test
8. Create Centre
9. Attach Test + Price
10. Switch to user
11. Create Booking
12. Initialize Payment
13. Simulate SUCCESS
14. Verify Booking = CONFIRMED
15. Send Webhook
16. Send same Webhook again
17. Verify idempotency
18. Test FAILED payment
19. Test cross-user booking access
```

This flow covers the main functional and security requirements of the assignment.
