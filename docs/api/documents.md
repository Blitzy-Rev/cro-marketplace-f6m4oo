# Document Management API

This document provides detailed information about the Document Management API endpoints, which enable secure document exchange between pharmaceutical companies and Contract Research Organizations (CROs). The API supports document upload, retrieval, e-signature workflows, and document lifecycle management in compliance with 21 CFR Part 11 requirements.

## Authentication

All document endpoints require authentication using JWT tokens. Include the token in the Authorization header as a Bearer token:

```
Authorization: Bearer <your_jwt_token>
```

Tokens can be obtained from the `/auth/login` endpoint. Most document operations also require appropriate permissions based on the user's role and relationship to the associated submission.

## Document Types

The system supports the following document types:

- `MATERIAL_TRANSFER_AGREEMENT`: Legal agreement for transferring materials between organizations
- `NON_DISCLOSURE_AGREEMENT`: Confidentiality agreement between parties
- `EXPERIMENT_SPECIFICATION`: Detailed specifications for experimental procedures
- `SERVICE_AGREEMENT`: Contract outlining services to be provided
- `RESULTS_REPORT`: Report containing experimental results
- `QUALITY_CONTROL`: Documentation of quality control procedures
- `ADDITIONAL_INSTRUCTIONS`: Supplementary instructions for experiments
- `SAFETY_DATA_SHEET`: Safety information for materials

Document types `MATERIAL_TRANSFER_AGREEMENT`, `NON_DISCLOSURE_AGREEMENT`, and `SERVICE_AGREEMENT` require electronic signatures.

## Document Statuses

Documents can have the following statuses:

- `DRAFT`: Document is in draft state
- `PENDING_SIGNATURE`: Document is awaiting signatures
- `SIGNED`: Document has been signed by all parties
- `REJECTED`: Document has been rejected
- `EXPIRED`: Document has expired
- `ARCHIVED`: Document has been archived

## List Documents

### Endpoint

```
GET /api/v1/documents
```

### Query Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| submission_id | UUID | No | Filter by submission ID |
| document_type | string | No | Filter by document type |
| skip | integer | No | Number of records to skip (default: 0) |
| limit | integer | No | Maximum number of records to return (default: 100, max: 1000) |

### Response

```json
{
  "items": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Non-Disclosure Agreement",
      "document_type": "NON_DISCLOSURE_AGREEMENT",
      "submission_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "status": "SIGNED",
      "url": "https://example.com/presigned-url",
      "uploaded_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "uploaded_at": "2023-09-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 100,
  "pages": 1
}
```

## Filter Documents

### Endpoint

```
POST /api/v1/documents/filter
```

### Request Body

```json
{
  "submission_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "document_type": "NON_DISCLOSURE_AGREEMENT",
  "status": "SIGNED",
  "uploaded_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "date_range": {
    "start_date": "2023-09-01T00:00:00Z",
    "end_date": "2023-09-30T23:59:59Z"
  }
}
```

### Query Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| skip | integer | No | Number of records to skip (default: 0) |
| limit | integer | No | Maximum number of records to return (default: 100, max: 1000) |
| url_expiration | integer | No | Expiration time in seconds for presigned URLs (default: 3600) |

### Response

Same as the List Documents response.

## Get Document by ID

### Endpoint

```
GET /api/v1/documents/{document_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| document_id | UUID | Yes | ID of the document to retrieve |

### Query Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| url_expiration | integer | No | Expiration time in seconds for presigned URL (default: 3600) |

### Response

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Non-Disclosure Agreement",
  "document_type": "NON_DISCLOSURE_AGREEMENT",
  "submission_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "SIGNED",
  "url": "https://example.com/presigned-url",
  "uploaded_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "uploaded_at": "2023-09-15T10:30:00Z",
  "is_signed": true,
  "signed_at": "2023-09-16T14:20:00Z"
}
```

## Get Documents by Submission

### Endpoint

```
GET /api/v1/documents/submission/{submission_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| submission_id | UUID | Yes | ID of the submission |

### Query Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| url_expiration | integer | No | Expiration time in seconds for presigned URLs (default: 3600) |

### Response

```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Non-Disclosure Agreement",
    "document_type": "NON_DISCLOSURE_AGREEMENT",
    "submission_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "status": "SIGNED",
    "url": "https://example.com/presigned-url",
    "uploaded_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "uploaded_at": "2023-09-15T10:30:00Z"
  },
  {
    "id": "4fa85f64-5717-4562-b3fc-2c963f66afa7",
    "name": "Experiment Specification",
    "document_type": "EXPERIMENT_SPECIFICATION",
    "submission_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "status": "DRAFT",
    "url": "https://example.com/presigned-url",
    "uploaded_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "uploaded_at": "2023-09-15T11:45:00Z"
  }
]
```

## Get Required Documents

### Endpoint

```
GET /api/v1/documents/required/{submission_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| submission_id | UUID | Yes | ID of the submission |

### Response

```json
[
  {
    "document_type": "NON_DISCLOSURE_AGREEMENT",
    "description": "Confidentiality agreement between parties",
    "is_completed": true,
    "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "status": "SIGNED"
  },
  {
    "document_type": "MATERIAL_TRANSFER_AGREEMENT",
    "description": "Legal agreement for transferring materials between organizations",
    "is_completed": false,
    "document_id": null,
    "status": null
  },
  {
    "document_type": "EXPERIMENT_SPECIFICATION",
    "description": "Detailed specifications for experimental procedures",
    "is_completed": true,
    "document_id": "4fa85f64-5717-4562-b3fc-2c963f66afa7",
    "status": "DRAFT"
  }
]
```

## Upload Document

### Endpoint

```
POST /api/v1/documents/upload
```

### Request Body (multipart/form-data)

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| file | file | Yes | Document file to upload |
| document_type | string | Yes | Type of document (from DocumentType enum) |
| submission_id | UUID | Yes | ID of the submission this document belongs to |
| name | string | No | Document name (defaults to filename if not provided) |

### Response

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Non-Disclosure Agreement.pdf",
  "document_type": "NON_DISCLOSURE_AGREEMENT",
  "submission_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "DRAFT",
  "url": "https://example.com/presigned-url",
  "uploaded_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "uploaded_at": "2023-09-15T10:30:00Z"
}
```

## Generate Upload URL

### Endpoint

```
POST /api/v1/documents/upload-url
```

### Request Body

```json
{
  "filename": "Non-Disclosure Agreement.pdf",
  "document_type": "NON_DISCLOSURE_AGREEMENT",
  "submission_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "content_type": "application/pdf",
  "expiration": 3600
}
```

### Response

```json
{
  "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "upload_url": "https://example.com/presigned-upload-url",
  "expires_at": "2023-09-15T11:30:00Z"
}
```

After receiving this response, the client should upload the file directly to the provided `upload_url` using an HTTP PUT request with the appropriate content type.

## Download Document

### Endpoint

```
GET /api/v1/documents/{document_id}/download
```

### Path Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| document_id | UUID | Yes | ID of the document to download |

### Response

The document content as a binary stream with the appropriate content type header.

## Update Document

### Endpoint

```
PUT /api/v1/documents/{document_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| document_id | UUID | Yes | ID of the document to update |

### Request Body

```json
{
  "name": "Updated Document Name",
  "description": "Updated document description",
  "status": "DRAFT"
}
```

### Response

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Updated Document Name",
  "document_type": "NON_DISCLOSURE_AGREEMENT",
  "submission_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "DRAFT",
  "description": "Updated document description",
  "url": "https://example.com/presigned-url",
  "uploaded_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "uploaded_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T14:45:00Z"
}
```

## Delete Document

### Endpoint

```
DELETE /api/v1/documents/{document_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| document_id | UUID | Yes | ID of the document to delete |

### Response

```json
{
  "message": "Document successfully deleted"
}
```

## Request Document Signature

### Endpoint

```
POST /api/v1/documents/signature/request
```

### Request Body

```json
{
  "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "signers": [
    {
      "email": "signer1@example.com",
      "name": "John Smith",
      "role": "Pharma Representative"
    },
    {
      "email": "signer2@example.com",
      "name": "Jane Doe",
      "role": "CRO Representative"
    }
  ],
  "message": "Please sign this document at your earliest convenience",
  "return_url": "https://app.example.com/documents/signed"
}
```

### Response

```json
{
  "envelope_id": "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
  "status": "SENT",
  "signing_url": "https://docusign.net/signing-url",
  "expires_at": "2023-09-22T10:30:00Z"
}
```

## Get Signing URL

### Endpoint

```
GET /api/v1/documents/{document_id}/signing-url
```

### Path Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| document_id | UUID | Yes | ID of the document |

### Query Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| recipient_email | string | Yes | Email of the recipient |
| recipient_name | string | Yes | Name of the recipient |
| return_url | string | No | URL to redirect after signing |

### Response

```json
{
  "signing_url": "https://docusign.net/signing-url"
}
```

## Process Signature Webhook

### Endpoint

```
POST /api/v1/documents/signature/webhook
```

### Request Body

The request body contains the DocuSign Connect webhook payload, which varies depending on the event type. The system processes this payload to update document signature status.

### Response

```json
{
  "message": "Webhook processed successfully"
}
```

## Error Responses

### 400 Bad Request

```json
{
  "error_code": "INVALID_REQUEST",
  "message": "Invalid request parameters",
  "details": {
    "document_type": "Value is not a valid document type"
  },
  "status_code": 400
}
```

### 401 Unauthorized

```json
{
  "error_code": "AUTHENTICATION_ERROR",
  "message": "Not authenticated",
  "status_code": 401
}
```

### 403 Forbidden

```json
{
  "error_code": "PERMISSION_DENIED",
  "message": "Not authorized to access this document",
  "status_code": 403
}
```

### 404 Not Found

```json
{
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "Document not found",
  "status_code": 404
}
```

### 500 Internal Server Error

```json
{
  "error_code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred",
  "status_code": 500
}
```

## 21 CFR Part 11 Compliance

The Document Management API implements several features to ensure compliance with 21 CFR Part 11 requirements for electronic records and signatures:

1. **Secure Authentication**: All document operations require authenticated users with appropriate permissions.

2. **Comprehensive Audit Trails**: All document actions (creation, modification, signature, deletion) are logged with user information, timestamp, and action details.

3. **Electronic Signatures**: Integration with DocuSign provides legally binding electronic signatures that include:
   - Signer authentication
   - Signature manifestation (name, date, time, meaning)
   - Signature binding to the document
   - Non-repudiation

4. **Document Controls**:
   - Version control for all documents
   - Status tracking throughout document lifecycle
   - Tamper-evident storage with encryption

5. **System Validation**: The API is part of a validated system with documented testing and validation procedures.