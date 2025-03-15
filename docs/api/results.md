# Results API

This document describes the experimental results-related endpoints for the Molecular Data Management and CRO Integration Platform API. These endpoints enable management of experimental results from Contract Research Organizations (CROs), including uploading, processing, and retrieving results data.

## Base URL

All API endpoints are relative to the base URL: `https://api.moleculeflow.com/api/v1`

## Authentication

All results endpoints require authentication. Include the access token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

See the [Authentication API](auth.md) documentation for details on obtaining tokens.

## Result Data Model

A result in the system is represented by the following data structure:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "submission_id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Binding Assay Results",
  "status": "COMPLETED",
  "notes": "Results from binding assay experiment",
  "properties": [
    {
      "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
      "name": "binding_affinity",
      "value": 85.2,
      "units": "%"
    },
    {
      "molecule_id": "123e4567-e89b-12d3-a456-426614174003",
      "name": "binding_affinity",
      "value": 92.7,
      "units": "%"
    }
  ],
  "uploaded_by": "123e4567-e89b-12d3-a456-426614174004",
  "uploaded_at": "2023-09-28T14:30:00Z"
}
```

The detailed result view also includes related data:

```json
{
  // ... all fields from above, plus:
  "submission": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Binding Assay Batch 12",
    "status": "RESULTS_UPLOADED"
  },
  "molecules": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174002",
      "smiles": "CC(C)CCO",
      "properties": [
        {
          "name": "binding_affinity",
          "value": 85.2,
          "units": "%"
        }
      ]
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "smiles": "c1ccccc1",
      "properties": [
        {
          "name": "binding_affinity",
          "value": 92.7,
          "units": "%"
        }
      ]
    }
  ],
  "documents": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174005",
      "name": "Results Report.pdf",
      "document_type": "RESULTS_REPORT"
    }
  ]
}
```

## Result Status Values

Results can have the following status values:

- `PROCESSING`: Results are being processed after upload
- `COMPLETED`: Results have been successfully processed
- `FAILED`: Results processing failed
- `REVIEWED`: Results have been reviewed by the pharma user
- `REJECTED`: Results have been rejected by the pharma user

## Endpoints

### List Results

#### GET /results

List experimental results with pagination and optional filtering.

**Parameters:**

| Name | In | Description | Required | Type | Default |
|------|----|--------------|---------|----|---------|
| submission_id | query | Filter by submission ID | No | UUID | - |
| molecule_id | query | Filter by molecule ID | No | UUID | - |
| status | query | Filter by result status | No | string | - |
| skip | query | Number of records to skip | No | integer | 0 |
| limit | query | Maximum number of records to return | No | integer | 100 |

**Request:**

```
GET /results?submission_id=123e4567-e89b-12d3-a456-426614174001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

200 OK: List of results

```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "submission_id": "123e4567-e89b-12d3-a456-426614174001",
      "name": "Binding Assay Results",
      "status": "COMPLETED",
      "uploaded_by": "123e4567-e89b-12d3-a456-426614174004",
      "uploaded_at": "2023-09-28T14:30:00Z",
      "molecule_count": 2
    }
  ],
  "total": 1,
  "page": 1,
  "size": 100,
  "pages": 1
}
```

401 Unauthorized: Not authenticated

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

This endpoint returns a paginated list of results. Use the query parameters to filter the results by submission, molecule, or status.

### Get Result by ID

#### GET /results/{result_id}

Get detailed information about a specific result.

**Parameters:**

| Name | In | Description | Required | Type |
|------|----|--------------|---------|----|
| result_id | path | ID of the result to retrieve | Yes | UUID |

**Request:**

```
GET /results/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

200 OK: Result details

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "submission_id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Binding Assay Results",
  "status": "COMPLETED",
  "notes": "Results from binding assay experiment",
  "properties": [
    {
      "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
      "name": "binding_affinity",
      "value": 85.2,
      "units": "%"
    },
    {
      "molecule_id": "123e4567-e89b-12d3-a456-426614174003",
      "name": "binding_affinity",
      "value": 92.7,
      "units": "%"
    }
  ],
  "uploaded_by": "123e4567-e89b-12d3-a456-426614174004",
  "uploaded_at": "2023-09-28T14:30:00Z",
  "submission": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Binding Assay Batch 12",
    "status": "RESULTS_UPLOADED"
  },
  "molecules": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174002",
      "smiles": "CC(C)CCO"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "smiles": "c1ccccc1"
    }
  ],
  "documents": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174005",
      "name": "Results Report.pdf",
      "document_type": "RESULTS_REPORT"
    }
  ]
}
```

401 Unauthorized: Not authenticated

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

404 Not Found: Result not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Result not found",
  "details": null,
  "status_code": 404
}
```

The detailed view includes related data such as the submission, molecules, and associated documents.

### Get Results by Submission

#### GET /results/submission/{submission_id}

Get all results for a specific submission.

**Parameters:**

| Name | In | Description | Required | Type |
|------|----|--------------|---------|----|
| submission_id | path | ID of the submission | Yes | UUID |

**Request:**

```
GET /results/submission/123e4567-e89b-12d3-a456-426614174001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

200 OK: List of results for the submission

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "submission_id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Binding Assay Results",
    "status": "COMPLETED",
    "notes": "Results from binding assay experiment",
    "uploaded_by": "123e4567-e89b-12d3-a456-426614174004",
    "uploaded_at": "2023-09-28T14:30:00Z",
    "molecule_count": 2
  }
]
```

401 Unauthorized: Not authenticated

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

404 Not Found: Submission not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Submission not found",
  "details": null,
  "status_code": 404
}
```

This endpoint returns all results associated with a specific submission.

### Get Results by Molecule

#### GET /results/molecule/{molecule_id}

Get all results for a specific molecule.

**Parameters:**

| Name | In | Description | Required | Type |
|------|----|--------------|---------|----|
| molecule_id | path | ID of the molecule | Yes | UUID |

**Request:**

```
GET /results/molecule/123e4567-e89b-12d3-a456-426614174002
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

200 OK: List of results for the molecule

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "submission_id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Binding Assay Results",
    "status": "COMPLETED",
    "property": {
      "name": "binding_affinity",
      "value": 85.2,
      "units": "%"
    },
    "uploaded_at": "2023-09-28T14:30:00Z"
  }
]
```

401 Unauthorized: Not authenticated

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

404 Not Found: Molecule not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Molecule not found",
  "details": null,
  "status_code": 404
}
```

This endpoint returns all experimental results for a specific molecule across all submissions.

### Upload Results

#### POST /results

Upload experimental results for a submission.

**Request:**

```
POST /results
Content-Type: multipart/form-data

file: (binary CSV file)
submission_id: 123e4567-e89b-12d3-a456-426614174001
name: Binding Assay Results
notes: Results from binding assay experiment

Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

202 Accepted: Results accepted for processing

```json
{
  "success": true,
  "message": "Results uploaded and being processed",
  "result_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

400 Bad Request: Invalid results data

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid results data",
  "details": {
    "file": "File must be a CSV file"
  },
  "status_code": 400
}
```

401 Unauthorized: Not authenticated

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

404 Not Found: Submission not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Submission not found",
  "details": null,
  "status_code": 404
}
```

The CSV file should contain columns for molecule identifiers (SMILES or ID) and result properties. The file is processed asynchronously, and the status can be checked using the returned result_id.

### Get Results CSV Preview

#### GET /results/csv-preview

Get a preview of CSV data for column mapping.

**Parameters:**

| Name | In | Description | Required | Type | Default |
|------|----|--------------|---------|----|---------|
| file_url | query | URL of the uploaded CSV file | Yes | string | - |
| num_rows | query | Number of rows to preview | No | integer | 5 |

**Request:**

```
GET /results/csv-preview?file_url=uploads/results/2023-09-28/user123_file.csv&num_rows=2
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

200 OK: CSV preview data

```json
{
  "headers": ["SMILES", "Molecule_ID", "Binding_Affinity", "IC50"],
  "preview_data": [
    ["CC(C)CCO", "MOL-001", "85.2", "4.5"],
    ["c1ccccc1", "MOL-002", "92.7", "3.2"]
  ],
  "mapping_suggestions": {
    "SMILES": "smiles",
    "Molecule_ID": "molecule_id",
    "Binding_Affinity": "binding_affinity",
    "IC50": "ic50"
  }
}
```

400 Bad Request: Invalid request

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request",
  "details": {
    "file_url": "Invalid file URL"
  },
  "status_code": 400
}
```

401 Unauthorized: Not authenticated

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

404 Not Found: CSV file not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "CSV file not found",
  "details": null,
  "status_code": 404
}
```

This endpoint provides a preview of the CSV data and suggests column mappings based on header names. Use this information to create a mapping for the /results/process-csv endpoint.

### Process Results CSV

#### POST /results/process-csv

Process a previously uploaded results CSV file.

**Request:**

```
POST /results/process-csv
Content-Type: application/json

{
  "file_url": "uploads/results/2023-09-28/user123_file.csv",
  "submission_id": "123e4567-e89b-12d3-a456-426614174001",
  "column_mapping": {
    "SMILES": "smiles",
    "Molecule_ID": "molecule_id",
    "Binding_Affinity": {
      "name": "binding_affinity",
      "units": "%"
    },
    "IC50": {
      "name": "ic50",
      "units": "nM"
    }
  },
  "has_header": true,
  "delimiter": ",",
  "name": "Binding Assay Results",
  "notes": "Results from binding assay experiment"
}

Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

200 OK: CSV processing results

```json
{
  "success": true,
  "result_id": "123e4567-e89b-12d3-a456-426614174000",
  "total_rows": 10,
  "processed_rows": 10,
  "failed_rows": 0,
  "errors": [],
  "molecules_updated": 10,
  "submission_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

400 Bad Request: Invalid request

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request",
  "details": {
    "column_mapping": "Molecule identifier column (SMILES or molecule_id) is required"
  },
  "status_code": 400
}
```

401 Unauthorized: Not authenticated

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

404 Not Found: CSV file not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "CSV file not found",
  "details": null,
  "status_code": 404
}
```

The column_mapping must include a mapping for either SMILES or molecule_id to identify molecules. Other columns are mapped to result properties. The submission_id is required to associate the results with a specific submission.

### Update Result Status

#### PUT /results/{result_id}/status

Update the status of a result.

**Parameters:**

| Name | In | Description | Required | Type |
|------|----|--------------|---------|----|
| result_id | path | ID of the result to update | Yes | UUID |

**Request:**

```
PUT /results/123e4567-e89b-12d3-a456-426614174000/status
Content-Type: application/json

{
  "status": "REVIEWED",
  "comment": "Results reviewed and accepted"
}

Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

200 OK: Status updated successfully

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "submission_id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Binding Assay Results",
  "status": "REVIEWED",
  "updated_at": "2023-09-29T10:15:00Z"
}
```

400 Bad Request: Invalid status

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid status",
  "details": {
    "status": "Invalid status value"
  },
  "status_code": 400
}
```

401 Unauthorized: Not authenticated

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

404 Not Found: Result not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Result not found",
  "details": null,
  "status_code": 404
}
```

This endpoint allows updating the status of a result. Valid status transitions depend on the current status and user role.

### Download Results as CSV

#### GET /results/{result_id}/download

Download result data as a CSV file.

**Parameters:**

| Name | In | Description | Required | Type |
|------|----|--------------|---------|----|
| result_id | path | ID of the result to download | Yes | UUID |

**Request:**

```
GET /results/123e4567-e89b-12d3-a456-426614174000/download
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

200 OK: CSV file containing result data

```
SMILES,Molecule_ID,Binding_Affinity,IC50
CC(C)CCO,MOL-001,85.2,4.5
c1ccccc1,MOL-002,92.7,3.2
```

401 Unauthorized: Not authenticated

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

404 Not Found: Result not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Result not found",
  "details": null,
  "status_code": 404
}
```

This endpoint returns the result data as a CSV file. The file includes all molecules and their associated property values.

### Compare Results with Predictions

#### GET /results/{result_id}/compare-predictions

Compare experimental results with AI predictions for the same molecules.

**Parameters:**

| Name | In | Description | Required | Type |
|------|----|--------------|---------|----|
| result_id | path | ID of the result to compare | Yes | UUID |

**Request:**

```
GET /results/123e4567-e89b-12d3-a456-426614174000/compare-predictions
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

200 OK: Comparison of results and predictions

```json
{
  "molecules": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174002",
      "smiles": "CC(C)CCO",
      "experimental": {
        "binding_affinity": {
          "value": 85.2,
          "units": "%"
        }
      },
      "predicted": {
        "binding_affinity": {
          "value": 82.5,
          "units": "%",
          "confidence": 0.92
        }
      },
      "difference": {
        "binding_affinity": {
          "absolute": 2.7,
          "percentage": 3.17
        }
      }
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "smiles": "c1ccccc1",
      "experimental": {
        "binding_affinity": {
          "value": 92.7,
          "units": "%"
        }
      },
      "predicted": {
        "binding_affinity": {
          "value": 90.1,
          "units": "%",
          "confidence": 0.88
        }
      },
      "difference": {
        "binding_affinity": {
          "absolute": 2.6,
          "percentage": 2.8
        }
      }
    }
  ],
  "summary": {
    "property_count": 1,
    "molecule_count": 2,
    "average_difference": {
      "binding_affinity": {
        "absolute": 2.65,
        "percentage": 2.99
      }
    },
    "correlation": {
      "binding_affinity": 0.95
    }
  }
}
```

401 Unauthorized: Not authenticated

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

404 Not Found: Result not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Result not found",
  "details": null,
  "status_code": 404
}
```

This endpoint compares experimental results with AI predictions for the same molecules and properties. It calculates differences and correlations between predicted and experimental values.

## Error Handling

All endpoints return standard error responses with the following structure:

```json
{
  "error_code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": null,
  "status_code": 400
}
```

Common error codes include:

- `UNAUTHORIZED`: Not authenticated or token expired
- `VALIDATION_ERROR`: Invalid request data
- `NOT_FOUND`: Resource not found
- `PROCESSING_ERROR`: Error during results processing
- `INTERNAL_ERROR`: Internal server error

## Rate Limiting

API endpoints are rate-limited to prevent abuse. The current limits are:

- Standard endpoints: 100 requests per minute per user
- CSV processing: 10 requests per minute per user

When rate limits are exceeded, the API returns a 429 Too Many Requests response with a Retry-After header indicating when the client should retry.

## Pagination

List endpoints support pagination using skip and limit parameters:

- skip: Number of records to skip (default: 0)
- limit: Maximum number of records to return (default: 100, max: 1000)

The response includes pagination metadata:

```json
{
  "items": [...],
  "total": 1500,
  "page": 1,
  "size": 100,
  "pages": 15
}
```

## CSV Processing

Results CSV processing follows a two-step workflow:

1. Upload the CSV file using the upload endpoint
2. Process the file using the process-csv endpoint with column mapping

The CSV file should contain at least one column for molecule identification (either SMILES or molecule_id) and one or more columns for result properties. The column mapping defines how CSV columns map to molecule identifiers and result properties.

Example column mapping:

```json
{
  "column_mapping": {
    "SMILES": "smiles",
    "Molecule_ID": "molecule_id",
    "Binding_Affinity": {
      "name": "binding_affinity",
      "units": "%"
    },
    "IC50": {
      "name": "ic50",
      "units": "nM"
    }
  }
}
```

The system will attempt to match molecules based on the provided identifiers. If a molecule cannot be matched, the corresponding row will be reported as an error.

## Result Integration

When results are processed successfully, the system automatically:

1. Updates the submission status to RESULTS_UPLOADED
2. Adds the result properties to the corresponding molecules
3. Creates a result record with all property values
4. Notifies the pharma user that results are available for review

The pharma user can then review the results and update the status to REVIEWED or REJECTED. If the results are reviewed and accepted, the submission status is updated to RESULTS_REVIEWED.

## Permissions

Access to results endpoints is controlled by user roles:

- **CRO Users**: Can upload and view results for submissions assigned to their CRO
- **Pharma Users**: Can view results for their submissions and update result status
- **Administrators**: Have full access to all results

Attempting to access results without proper permissions will result in a 403 Forbidden response.

## Related Documentation

- [Submissions API](submissions.md): API for managing CRO submissions
- [Molecules API](molecules.md): API for managing molecular data
- [Documents API](documents.md): API for managing documents, including result reports