# CRO Services API

## Introduction

This document provides detailed information about the CRO (Contract Research Organization) API endpoints in the Molecular Data Management and CRO Integration Platform. These endpoints allow users to manage CRO services, create submissions for experimental testing, and track the complete submission workflow from creation to results.

## Authentication

All CRO API endpoints require authentication using JWT tokens. Tokens can be obtained from the `/auth/login` endpoint. Include the token in the Authorization header of all requests using the Bearer scheme.

```
Authorization: Bearer <your_token>
```

Different endpoints may require specific user roles (pharma user, CRO user, or admin) for access.

## CRO Services Endpoints

### List CRO Services

**Endpoint**: `GET /api/v1/cro`

**Description**: Retrieve a list of available CRO services with optional filtering.

**Query Parameters**:
- `name_contains` (string, optional) - Filter services by name substring
- `provider` (string, optional) - Filter services by provider name
- `service_type` (string, optional) - Filter services by type (BINDING_ASSAY, ADME, SOLUBILITY, PERMEABILITY, METABOLIC_STABILITY, TOXICITY, CUSTOM)
- `active_only` (boolean, optional) - Filter to only active services
- `max_turnaround_days` (integer, optional) - Filter services with turnaround time less than or equal to specified days
- `max_price` (number, optional) - Filter services with base price less than or equal to specified amount
- `skip` (integer, optional, default: 0) - Number of records to skip for pagination
- `limit` (integer, optional, default: 100) - Maximum number of records to return

**Response**: (200 OK)
```json
{
  "items": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Protein Binding Assay",
      "description": "Standard radioligand binding assay for target protein XYZ",
      "provider": "BioCRO Inc.",
      "service_type": "BINDING_ASSAY",
      "base_price": 1500.0,
      "price_currency": "USD",
      "typical_turnaround_days": 14,
      "specifications": {
        "assay_protocol": "Standard Protocol A",
        "controls_included": true,
        "replicates": 3
      },
      "active": true,
      "created_at": "2023-09-15T10:30:00Z",
      "updated_at": "2023-09-15T10:30:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "size": 10,
  "pages": 1
}
```

**Example Request**:
```
GET /api/v1/cro?service_type=BINDING_ASSAY&active_only=true&limit=10
```

### Get Active CRO Services

**Endpoint**: `GET /api/v1/cro/active`

**Description**: Retrieve a list of active CRO services.

**Query Parameters**:
- `skip` (integer, optional, default: 0) - Number of records to skip for pagination
- `limit` (integer, optional, default: 100) - Maximum number of records to return

**Response**: (200 OK)
Same response schema as List CRO Services

### Search CRO Services

**Endpoint**: `GET /api/v1/cro/search`

**Description**: Search for CRO services by name or description.

**Query Parameters**:
- `q` (string, required) - Search term
- `skip` (integer, optional, default: 0) - Number of records to skip for pagination
- `limit` (integer, optional, default: 100) - Maximum number of records to return

**Response**: (200 OK)
Same response schema as List CRO Services

**Example Request**:
```
GET /api/v1/cro/search?q=binding&limit=10
```

### Get CRO Service by ID

**Endpoint**: `GET /api/v1/cro/{service_id}`

**Description**: Retrieve details of a specific CRO service by ID.

**Path Parameters**:
- `service_id` (UUID, required) - ID of the CRO service to retrieve

**Response**: (200 OK)
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Protein Binding Assay",
  "description": "Standard radioligand binding assay for target protein XYZ",
  "provider": "BioCRO Inc.",
  "service_type": "BINDING_ASSAY",
  "base_price": 1500.0,
  "price_currency": "USD",
  "typical_turnaround_days": 14,
  "specifications": {
    "assay_protocol": "Standard Protocol A",
    "controls_included": true,
    "replicates": 3
  },
  "active": true,
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:30:00Z"
}
```

**Error Responses**:
- 404 Not Found - CRO service not found

### Create CRO Service

**Endpoint**: `POST /api/v1/cro`

**Description**: Create a new CRO service. Requires admin privileges.

**Request Body**:
```json
{
  "name": "Protein Binding Assay",
  "description": "Standard radioligand binding assay for target protein XYZ",
  "provider": "BioCRO Inc.",
  "service_type": "BINDING_ASSAY",
  "base_price": 1500.0,
  "price_currency": "USD",
  "typical_turnaround_days": 14,
  "specifications": {
    "assay_protocol": "Standard Protocol A",
    "controls_included": true,
    "replicates": 3
  },
  "active": true
}
```

**Required Fields**:
- `name` (string, max length: 100) - Name of the CRO service
- `provider` (string, max length: 255) - Name of the CRO provider
- `service_type` (string, enum: [BINDING_ASSAY, ADME, SOLUBILITY, PERMEABILITY, METABOLIC_STABILITY, TOXICITY, CUSTOM]) - Type of service offered
- `base_price` (number, minimum: 0) - Base price for the service
- `price_currency` (string, length: 3) - Currency code for the price (e.g., USD)
- `typical_turnaround_days` (integer, minimum: 1) - Typical number of days for service completion

**Optional Fields**:
- `description` (string) - Detailed description of the service
- `specifications` (object) - Additional specifications for the service
- `active` (boolean, default: true) - Whether the service is active and available for selection

**Response**: (201 Created)
Same schema as Get CRO Service by ID

**Error Responses**:
- 400 Bad Request - Invalid request data
- 401 Unauthorized
- 403 Forbidden - Requires admin privileges
- 409 Conflict - Service with same name already exists

### Update CRO Service

**Endpoint**: `PUT /api/v1/cro/{service_id}`

**Description**: Update an existing CRO service. Requires admin privileges.

**Path Parameters**:
- `service_id` (UUID, required) - ID of the CRO service to update

**Request Body**:
All fields are optional. Same schema as Create CRO Service.

**Response**: (200 OK)
Same schema as Get CRO Service by ID

**Error Responses**:
- 400 Bad Request - Invalid request data
- 401 Unauthorized
- 403 Forbidden - Requires admin privileges
- 404 Not Found - CRO service not found
- 409 Conflict - Service with same name already exists

### Update CRO Service Specifications

**Endpoint**: `PATCH /api/v1/cro/{service_id}/specifications`

**Description**: Update specifications for an existing CRO service. Requires admin privileges.

**Path Parameters**:
- `service_id` (UUID, required) - ID of the CRO service to update

**Request Body**:
```json
{
  "assay_protocol": "Updated Protocol B",
  "controls_included": true,
  "replicates": 5,
  "detection_method": "Fluorescence",
  "minimum_sample_amount": "10mg"
}
```

**Response**: (200 OK)
Same schema as Get CRO Service by ID

**Error Responses**:
- 400 Bad Request - Invalid specifications data
- 401 Unauthorized
- 403 Forbidden - Requires admin privileges
- 404 Not Found - CRO service not found

### Activate CRO Service

**Endpoint**: `POST /api/v1/cro/{service_id}/activate`

**Description**: Activate a CRO service. Requires admin privileges.

**Path Parameters**:
- `service_id` (UUID, required) - ID of the CRO service to activate

**Response**: (200 OK)
Same schema as Get CRO Service by ID

**Error Responses**:
- 401 Unauthorized
- 403 Forbidden - Requires admin privileges
- 404 Not Found - CRO service not found

### Deactivate CRO Service

**Endpoint**: `POST /api/v1/cro/{service_id}/deactivate`

**Description**: Deactivate a CRO service. Requires admin privileges.

**Path Parameters**:
- `service_id` (UUID, required) - ID of the CRO service to deactivate

**Response**: (200 OK)
Same schema as Get CRO Service by ID

**Error Responses**:
- 401 Unauthorized
- 403 Forbidden - Requires admin privileges
- 404 Not Found - CRO service not found

### Delete CRO Service

**Endpoint**: `DELETE /api/v1/cro/{service_id}`

**Description**: Delete a CRO service if it has no associated submissions. Requires admin privileges.

**Path Parameters**:
- `service_id` (UUID, required) - ID of the CRO service to delete

**Response**: (200 OK)
```json
{
  "success": true,
  "message": "CRO service deleted successfully"
}
```

**Error Responses**:
- 401 Unauthorized
- 403 Forbidden - Requires admin privileges
- 404 Not Found - CRO service not found
- 409 Conflict - Service has associated submissions

### Get Service Types

**Endpoint**: `GET /api/v1/cro/types`

**Description**: Get a list of available CRO service types.

**Response**: (200 OK)
```json
[
  {
    "id": "BINDING_ASSAY",
    "name": "Binding Assay"
  },
  {
    "id": "ADME",
    "name": "ADME"
  },
  {
    "id": "SOLUBILITY",
    "name": "Solubility"
  },
  {
    "id": "PERMEABILITY",
    "name": "Permeability"
  },
  {
    "id": "METABOLIC_STABILITY",
    "name": "Metabolic Stability"
  },
  {
    "id": "TOXICITY",
    "name": "Toxicity"
  },
  {
    "id": "CUSTOM",
    "name": "Custom"
  }
]
```

### Get Service Counts by Type

**Endpoint**: `GET /api/v1/cro/stats/by-type`

**Description**: Get count of services grouped by service type.

**Response**: (200 OK)
```json
[
  {
    "service_type": "BINDING_ASSAY",
    "count": 5
  },
  {
    "service_type": "ADME",
    "count": 3
  },
  {
    "service_type": "SOLUBILITY",
    "count": 2
  }
]
```

### Get Service Counts by Provider

**Endpoint**: `GET /api/v1/cro/stats/by-provider`

**Description**: Get count of services grouped by provider.

**Response**: (200 OK)
```json
[
  {
    "provider": "BioCRO Inc.",
    "count": 7
  },
  {
    "provider": "ChemTest Labs",
    "count": 4
  },
  {
    "provider": "PharmaServices",
    "count": 3
  }
]
```

## CRO Submission Workflow

The CRO submission workflow involves several steps and status transitions. The following diagram illustrates the complete workflow:

```
DRAFT → SUBMITTED → PENDING_REVIEW → PRICING_PROVIDED → APPROVED → IN_PROGRESS → RESULTS_UPLOADED → RESULTS_REVIEWED → COMPLETED
```

At any point, a submission can be CANCELLED or REJECTED, which are terminal states.

For detailed information about submission-related endpoints, please refer to the [Submissions API documentation](submissions.md).

## Error Handling

All API endpoints follow a consistent error response format:

```json
{
  "error_code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": { /* Additional error details */ },
  "status_code": 400
}
```

Common error codes include:

- `NOT_FOUND`: The requested resource was not found
- `VALIDATION_ERROR`: The request data failed validation
- `UNAUTHORIZED`: Authentication is required
- `FORBIDDEN`: The authenticated user lacks permission
- `CONFLICT`: The request conflicts with the current state
- `INTERNAL_ERROR`: An unexpected error occurred

## Rate Limiting

API endpoints are subject to rate limiting to ensure system stability. The current limits are:

- Standard endpoints: 100 requests per minute per user
- List endpoints: 60 requests per minute per user
- Create/Update endpoints: 30 requests per minute per user

When rate limits are exceeded, the API will respond with a 429 Too Many Requests status code and a Retry-After header indicating when the client should retry.