# EVE Healthcare Backend Architecture

## Layer Responsibilities

### 1. Views / ViewSets (`views/`)
- **Role:** HTTP Interface.
- **Allowed:** Calling serializers, checking permissions, returning HTTP responses, calling Services/Selectors.
- **Forbidden:** Business logic, direct database queries, complex state transitions.

### 2. Serializers (`serializers/`)
- **Role:** Data transformation and basic validation.
- **Allowed:** Validating input types, formatting output data.
- **Forbidden:** Orchestrating workflows, saving complex related models directly without a service.

### 3. Services (`services/`)
- **Role:** Business logic and workflow orchestration.
- **Allowed:** Complex business rules, calling Repositories/Selectors, triggering webhooks, managing database transactions.
- **Forbidden:** Handling HTTP requests/responses directly, returning HTTP status codes.

### 4. Selectors (`selectors/`)
- **Role:** Database Reads.
- **Allowed:** `filter()`, `select_related()`, `prefetch_related()`.
- **Forbidden:** Creating, updating, or deleting data.

### 5. Repositories (`repositories/`)
- **Role:** Database Writes.
- **Allowed:** `create()`, `update()`, `delete()`, `bulk_create()`.
- **Forbidden:** Making business decisions (e.g., checking if a user is allowed to create an object - that belongs in the Service).

## When to bypass layers
- If an endpoint simply reads a list of public Diagnostic Centres with no business logic, the View can call the Selector directly. No Service is needed.
- If a write operation is trivial (e.g., updating a user's name), a Service is still recommended for consistency, but the Repository might just be a standard Django `model.save()`.
