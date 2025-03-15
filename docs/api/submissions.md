# CRO Submission API

## Introduction

The Submissions API provides endpoints for managing the complete lifecycle of submissions to Contract Research Organizations (CROs) for experimental testing of molecules. This API supports the workflow from initial submission creation through approval, experimental work, and results processing.

## Authentication

All submission endpoints require authentication using a JWT token obtained from the `/auth/login` endpoint. Include the token in the Authorization header as a Bearer token.

### Example

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Submission Workflow

The submission workflow follows a defined state machine with the following statuses:

### Status Definitions

- `DRAFT`: Initial draft state, editable by pharma user
- `SUBMITTED`: Submitted to CRO but not yet reviewed
- `PENDING_REVIEW`: Under review by CRO
- `PRICING_PROVIDED`: CRO has provided pricing and timeline
- `APPROVED`: Pharma has approved pricing and timeline
- `IN_PROGRESS`: Experimental work in progress at CRO
- `RESULTS_UPLOADED`: CRO has uploaded experimental results
- `RESULTS_REVIEWED`: Pharma has reviewed experimental results
- `COMPLETED`: Submission workflow completed successfully
- `CANCELLED`: Submission cancelled by either party
- `REJECTED`: Submission rejected by CRO or pharma

### Status Transitions

Submissions follow a specific flow of status transitions:

```
DRAFT → SUBMITTED → PENDING_REVIEW → PRICING_PROVIDED → APPROVED → IN_PROGRESS → RESULTS_UPLOADED → RESULTS_REVIEWED → COMPLETED
```

At most stages, a submission can also transition to `CANCELLED` or `REJECTED`.

### Actions

The following actions can be performed on submissions:

- `SUBMIT`: Submit a draft submission to CRO
- `PROVIDE_PRICING`: CRO provides pricing and timeline
- `APPROVE`: Pharma approves pricing and timeline
- `REJECT`: Reject a submission
- `CANCEL`: Cancel a submission
- `START_EXPERIMENT`: CRO starts experimental work
- `UPLOAD_RESULTS`: CRO uploads experimental results
- `REVIEW_RESULTS`: Pharma reviews experimental results
- `COMPLETE`: Mark submission as completed

## Endpoints

The following endpoints are available for managing submissions:

### Create a Submission

```
POST /api/v1/submissions
```

Create a new submission to a CRO.

**Request Body:**

```json
{
  "name": "Binding Assay Batch 12",
  "cro_service_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "molecule_ids": [
    "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "4fa85f64-5717-4562-b3fc-2c963f66afa7"
  ],
  "specifications": {
    "concentration": "10 nM",
    "replicates": 3,
    "controls": ["positive", "negative"]
  },
  "description": "Testing binding affinity for target protein XYZ"
}
```

**Response:**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Binding Assay Batch 12",
  "status": "DRAFT",
  "cro_service_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "created_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:30:00Z",
  "specifications": {
    "concentration": "10 nM",
    "replicates": 3,
    "controls": ["positive", "negative"]
  },
  "description": "Testing binding affinity for target protein XYZ",
  "molecule_count": 2,
  "document_count": 0,
  "is_editable": true
}
```

### Get a Submission

```
GET /api/v1/submissions/{submission_id}
```

Retrieve a submission by ID with all related data.

**Path Parameters:**

- `submission_id` (UUID): ID of the submission to retrieve

**Response:**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Binding Assay Batch 12",
  "status": "DRAFT",
  "cro_service_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "created_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:30:00Z",
  "specifications": {
    "concentration": "10 nM",
    "replicates": 3,
    "controls": ["positive", "negative"]
  },
  "description": "Testing binding affinity for target protein XYZ",
  "cro_service": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Binding Assay",
    "provider": "BioCRO Inc."
  },
  "molecules": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "smiles": "CC(C)CCO"
    },
    {
      "id": "4fa85f64-5717-4562-b3fc-2c963f66afa7",
      "smiles": "c1ccccc1"
    }
  ],
  "documents": [],
  "results": [],
  "status_description": "Initial draft state, editable by pharma user",
  "molecule_count": 2,
  "document_count": 0,
  "is_editable": true
}
```

### Update a Submission

```
PUT /api/v1/submissions/{submission_id}
```

Update an existing submission. Only submissions in editable states can be updated.

**Path Parameters:**

- `submission_id` (UUID): ID of the submission to update

**Request Body:**

```json
{
  "name": "Updated Binding Assay Batch 12",
  "specifications": {
    "concentration": "20 nM",
    "replicates": 4,
    "controls": ["positive", "negative", "vehicle"]
  },
  "molecule_ids": [
    "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "4fa85f64-5717-4562-b3fc-2c963f66afa7",
    "5fa85f64-5717-4562-b3fc-2c963f66afa8"
  ],
  "description": "Updated testing parameters for binding affinity"
}
```

**Response:**

Returns the updated submission object with the same structure as the GET response.

### List Submissions

```
GET /api/v1/submissions
```

List submissions with optional filtering.

**Query Parameters:**

- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum number of records to return (default: 100)
- `name_contains` (string, optional): Filter by name containing text
- `status` (string, optional): Filter by status
- `cro_service_id` (UUID, optional): Filter by CRO service
- `active_only` (boolean, optional): Only return active submissions
- `molecule_id` (UUID, optional): Filter by molecule ID

**Response:**

```json
{
  "items": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Binding Assay Batch 12",
      "status": "DRAFT",
      "cro_service_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "created_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "created_at": "2023-09-15T10:30:00Z",
      "updated_at": "2023-09-15T10:30:00Z",
      "cro_service": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Binding Assay",
        "provider": "BioCRO Inc."
      },
      "molecule_count": 2,
      "document_count": 0,
      "is_editable": true
    }
  ],
  "total": 1,
  "page": 1,
  "size": 100,
  "pages": 1
}
```

### Process Submission Action

```
POST /api/v1/submissions/{submission_id}/actions
```

Process an action on a submission to change its status.

**Path Parameters:**

- `submission_id` (UUID): ID of the submission

**Request Body:**

```json
{
  "action": "SUBMIT",
  "comment": "Ready for CRO review"
}
```

Possible actions: `SUBMIT`, `PROVIDE_PRICING`, `APPROVE`, `REJECT`, `CANCEL`, `START_EXPERIMENT`, `UPLOAD_RESULTS`, `REVIEW_RESULTS`, `COMPLETE`

**Response:**

```json
{
  "success": true,
  "message": "Submission successfully submitted to CRO"
}
```

### Set Submission Pricing (CRO Only)

```
POST /api/v1/submissions/{submission_id}/pricing
```

Set pricing and timeline information for a submission. Only available to CRO users.

**Path Parameters:**

- `submission_id` (UUID): ID of the submission

**Request Body:**

```json
{
  "price": 1500.00,
  "price_currency": "USD",
  "estimated_turnaround_days": 14,
  "comment": "Standard pricing for binding assay with 3 replicates"
}
```

**Response:**

Returns the updated submission object with pricing information.

### Check Required Documents

```
GET /api/v1/submissions/{submission_id}/documents/check
```

Check if a submission has all required documents based on the CRO service type.

**Path Parameters:**

- `submission_id` (UUID): ID of the submission

**Response:**

```json
{
  "required_documents": [
    {
      "type": "MATERIAL_TRANSFER_AGREEMENT",
      "name": "Material Transfer Agreement",
      "description": "Legal agreement for transferring materials"
    },
    {
      "type": "NON_DISCLOSURE_AGREEMENT",
      "name": "Non-Disclosure Agreement",
      "description": "Confidentiality agreement"
    },
    {
      "type": "EXPERIMENT_SPECIFICATION",
      "name": "Experiment Specification",
      "description": "Detailed experimental protocol"
    }
  ],
  "optional_documents": [
    {
      "type": "ADDITIONAL_INSTRUCTIONS",
      "name": "Additional Instructions",
      "description": "Any additional instructions for the CRO"
    }
  ],
  "existing_documents": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "type": "MATERIAL_TRANSFER_AGREEMENT",
      "name": "MTA for Project X",
      "status": "SIGNED"
    }
  ]
}
```

### Get Submission Timeline

```
GET /api/v1/submissions/{submission_id}/timeline
```

Get the timeline of status changes for a submission.

**Path Parameters:**

- `submission_id` (UUID): ID of the submission

**Response:**

```json
[
  {
    "status": "DRAFT",
    "timestamp": "2023-09-15T10:30:00Z",
    "user": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "John Smith"
    },
    "comment": "Submission created"
  },
  {
    "status": "SUBMITTED",
    "timestamp": "2023-09-16T14:20:00Z",
    "user": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "John Smith"
    },
    "comment": "Ready for CRO review"
  }
]
```

### Get Submission Counts by Status

```
GET /api/v1/submissions/counts
```

Get count of submissions grouped by status.

**Response:**

```json
[
  {
    "status": "DRAFT",
    "count": 5
  },
  {
    "status": "SUBMITTED",
    "count": 3
  },
  {
    "status": "PENDING_REVIEW",
    "count": 2
  },
  {
    "status": "COMPLETED",
    "count": 10
  }
]
```

## Error Responses

The API returns standard HTTP status codes and error responses:

### Error Response Format

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid submission data",
  "details": {
    "field": "molecule_ids",
    "error": "At least one molecule must be selected"
  },
  "status_code": 400
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Invalid request data (400)
- `NOT_FOUND`: Resource not found (404)
- `UNAUTHORIZED`: Authentication required (401)
- `FORBIDDEN`: Insufficient permissions (403)
- `INVALID_STATUS_TRANSITION`: Invalid status change (400)
- `MISSING_REQUIRED_DOCUMENTS`: Required documents missing (400)
- `INTERNAL_SERVER_ERROR`: Server error (500)

## Permissions

Access to submission endpoints is controlled by user roles:

### Pharma User Permissions

- Can create new submissions
- Can view and update their own submissions
- Can submit, approve, cancel, and review results for their submissions
- Cannot access other users' submissions

### CRO User Permissions

- Cannot create new submissions
- Can view submissions submitted to their CRO
- Can provide pricing, start experiments, upload results
- Cannot modify submission specifications created by pharma users

### Admin Permissions

- Full access to all submissions
- Can perform any action on any submission
- Can view submissions across all users and CROs

## Pagination

List endpoints support pagination using `skip` and `limit` parameters:

### Parameters

- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100, max: 1000)

### Response Format

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

## Examples

The following examples demonstrate common submission workflows:

### Complete Submission Workflow

1. Create a new submission (Pharma)
2. Upload required documents (Pharma)
3. Submit the submission to CRO (Pharma)
4. Review and provide pricing (CRO)
5. Approve pricing and timeline (Pharma)
6. Start experimental work (CRO)
7. Upload experimental results (CRO)
8. Review results (Pharma)
9. Complete the submission (Pharma)

### Example: Creating and Submitting

```bash
# 1. Create a new submission
POST /api/v1/submissions
{
  "name": "Binding Assay Batch 12",
  "cro_service_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "molecule_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
  "specifications": {
    "concentration": "10 nM",
    "replicates": 3
  }
}

# 2. Upload required documents
POST /api/v1/documents
(multipart/form-data with document file and metadata)

# 3. Submit to CRO
POST /api/v1/submissions/{submission_id}/actions
{
  "action": "SUBMIT",
  "comment": "Ready for review"
}
```