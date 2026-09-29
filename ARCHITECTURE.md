# EVE Healthcare Backend Architecture

The project follows a Service–Selector oriented architecture. HTTP concerns,
validation, business workflows, and database reads are separated to keep the
API maintainable and testable.

## Layer Responsibilities

### 1. Views (`views/`)

- **Role:** HTTP interface.
- Handle authentication and permissions.
- Receive requests and return HTTP responses.
- Use serializers for input/output.
- Delegate business workflows to Services.
- Delegate read/query operations to Selectors.
- Avoid embedding business rules or complex database workflows.

### 2. Serializers (`serializers/`)

- **Role:** Input validation and output serialization.
- Validate request data and basic field constraints.
- Transform model instances into API responses.
- Do not orchestrate business workflows.

### 3. Services (`services/`)

- **Role:** Business logic and workflow orchestration.
- Implement booking, payment, cancellation, and state-transition rules.
- Coordinate model operations and transactions.
- Do not handle HTTP responses or status codes.

### 4. Selectors (`selectors/`)

- **Role:** Read/query logic.
- Encapsulate database reads.
- Apply filtering, `select_related()`, `prefetch_related()`,
  and user-scoped access where required.
- Do not contain business workflows.

### 5. Repositories (`repositories/`)

Repository modules are available as an abstraction point for persistence
operations where useful. The current implementation does not require every
simple model operation to pass through a repository.

## Layer Flow

Typical write flow:

View → Serializer → Service → Model/Repository

Typical read flow:

View → Selector → Model

For complex workflows:

View → Serializer → Service → Transaction → Model operations

## When layers can be bypassed

For a simple read-only endpoint, a View may call a Selector directly.

A Service is used when business rules, state transitions, authorization
logic, or transactions need to be coordinated.
