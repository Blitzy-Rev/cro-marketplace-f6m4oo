# Prediction API

This document describes the prediction-related endpoints for the Molecular Data Management and CRO Integration Platform API. These endpoints enable AI-powered property prediction for molecules, including single molecule predictions, batch predictions, job status tracking, and result retrieval.

## Base URL

All API endpoints are relative to the base URL: `https://api.moleculeflow.com/api/v1`

## Authentication

All prediction endpoints require authentication. Include the access token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

See the [Authentication API](auth.md) documentation for details on obtaining tokens.

## Prediction Data Models

### Prediction Job

A prediction job represents an asynchronous request for property predictions:

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "batch_id": "123e4567-e89b-12d3-a456-426614174001",
  "status": "processing",
  "total_count": 5,
  "completed_count": 2,
  "failed_count": 0,
  "progress": 40,
  "message": "Processing predictions",
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:32:00Z"
}
```

### Prediction Result

A prediction result contains the predicted property value and confidence score:

```json
{
  "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
  "property_name": "solubility",
  "value": 0.82,
  "units": "mg/mL",
  "confidence": 0.95,
  "model_name": "SolubilityModel",
  "model_version": "2.1",
  "status": "completed",
  "created_at": "2023-09-15T10:35:00Z"
}
```

### Prediction Status

Prediction jobs can have the following statuses:

- `pending`: Job is queued and waiting to be processed
- `processing`: Job is currently being processed
- `completed`: Job has completed successfully
- `failed`: Job has failed due to an error

## Endpoints

### Predict Properties for a Molecule

**POST /molecules/{molecule_id}/predict**

Request property predictions from AI engine for a single molecule.

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|----|-------|-------------|
| molecule_id | path | string (uuid) | Yes | ID of the molecule |
| wait_for_results | query | boolean | No | Wait for prediction results |

**Request:**

```json
{
  "properties": ["solubility", "permeability", "logp"],
  "model_name": "default",
  "model_version": "latest"
}
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

`202 Accepted` - Prediction job information (when wait_for_results=false)

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "batch_id": "123e4567-e89b-12d3-a456-426614174001",
  "status": "pending",
  "progress": 0,
  "message": "Prediction job queued",
  "created_at": "2023-09-15T12:30:00Z",
  "updated_at": "2023-09-15T12:30:00Z"
}
```

`200 OK` - Prediction results (when wait_for_results=true)

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "batch_id": "123e4567-e89b-12d3-a456-426614174001",
  "status": "completed",
  "results": [
    {
      "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
      "property_name": "solubility",
      "value": 0.82,
      "units": "mg/mL",
      "confidence": 0.95,
      "model_name": "default",
      "model_version": "latest"
    },
    {
      "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
      "property_name": "permeability",
      "value": 8.2e-06,
      "units": "cm/s",
      "confidence": 0.87,
      "model_name": "default",
      "model_version": "latest"
    },
    {
      "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
      "property_name": "logp",
      "value": 1.2,
      "units": null,
      "confidence": 0.91,
      "model_name": "default",
      "model_version": "latest"
    }
  ],
  "created_at": "2023-09-15T12:30:00Z",
  "completed_at": "2023-09-15T12:30:05Z"
}
```

`400 Bad Request` - Invalid request

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request",
  "details": {
    "properties": "Unknown property: invalid_property"
  },
  "status_code": 400
}
```

`401 Unauthorized` - Unauthorized

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

`404 Not Found` - Molecule not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Molecule not found",
  "details": null,
  "status_code": 404
}
```

`503 Service Unavailable` - AI service unavailable

```json
{
  "error_code": "AI_SERVICE_UNAVAILABLE",
  "message": "AI prediction service is currently unavailable",
  "details": null,
  "status_code": 503
}
```

If properties are not specified, all available predictable properties will be calculated. When wait_for_results=false, the endpoint returns immediately with a job ID that can be used to check the status later. When wait_for_results=true, the endpoint waits for the predictions to complete before returning (with a timeout of 30 seconds).

Predictable properties include: logp, solubility, permeability, clearance, half_life, bioavailability, ic50, ec50, binding_affinity, pka, pkb.

### Batch Predict Properties

**POST /molecules/predict/batch**

Request property predictions for multiple molecules in batch.

**Request:**

```json
{
  "molecule_ids": [
    "123e4567-e89b-12d3-a456-426614174002",
    "123e4567-e89b-12d3-a456-426614174003",
    "123e4567-e89b-12d3-a456-426614174004"
  ],
  "properties": ["solubility", "permeability", "logp"],
  "model_name": "default",
  "model_version": "latest"
}
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

`202 Accepted` - Batch prediction job started

```json
{
  "batch_id": "123e4567-e89b-12d3-a456-426614174005",
  "job_id": "123e4567-e89b-12d3-a456-426614174006",
  "status": "pending",
  "total_count": 3,
  "completed_count": 0,
  "failed_count": 0,
  "progress": 0,
  "message": "Batch prediction job queued",
  "created_at": "2023-09-15T13:30:00Z",
  "updated_at": "2023-09-15T13:30:00Z"
}
```

`400 Bad Request` - Invalid request

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request",
  "details": {
    "molecule_ids": "At least one molecule ID is required"
  },
  "status_code": 400
}
```

`401 Unauthorized` - Unauthorized

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

`503 Service Unavailable` - AI service unavailable

```json
{
  "error_code": "AI_SERVICE_UNAVAILABLE",
  "message": "AI prediction service is currently unavailable",
  "details": null,
  "status_code": 503
}
```

This endpoint always operates asynchronously. The batch_id and job_id can be used to check the status and retrieve results using the prediction status endpoint. Maximum batch size is 100 molecules.

### Get Prediction Job Status

**GET /predictions/{batch_id}/status**

Check the status of a prediction job.

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|----|-------|-------------|
| batch_id | path | string (uuid) | Yes | ID of the prediction batch |

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

`200 OK` - Prediction job status

```json
{
  "batch_id": "123e4567-e89b-12d3-a456-426614174005",
  "external_job_id": "123e4567-e89b-12d3-a456-426614174006",
  "status": "processing",
  "total_count": 3,
  "completed_count": 1,
  "failed_count": 0,
  "progress": 33,
  "message": "Processing predictions",
  "created_at": "2023-09-15T13:30:00Z",
  "updated_at": "2023-09-15T13:31:00Z"
}
```

`401 Unauthorized` - Unauthorized

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

`404 Not Found` - Prediction job not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Prediction job not found",
  "details": null,
  "status_code": 404
}
```

Use this endpoint to poll for the status of an asynchronous prediction job. The progress field indicates the percentage of completion. When status is 'completed', all predictions have been processed and can be retrieved.

### Get Molecule Predictions

**GET /molecules/{molecule_id}/predictions**

Get all predictions for a specific molecule.

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|----|-------|-------------|
| molecule_id | path | string (uuid) | Yes | ID of the molecule |
| min_confidence | query | number (float) | No | Minimum confidence threshold |

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

`200 OK` - List of predictions for the molecule

```json
[
  {
    "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
    "property_name": "solubility",
    "value": 0.82,
    "units": "mg/mL",
    "confidence": 0.95,
    "model_name": "default",
    "model_version": "latest",
    "status": "completed",
    "created_at": "2023-09-15T12:30:05Z"
  },
  {
    "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
    "property_name": "permeability",
    "value": 8.2e-06,
    "units": "cm/s",
    "confidence": 0.87,
    "model_name": "default",
    "model_version": "latest",
    "status": "completed",
    "created_at": "2023-09-15T12:30:05Z"
  },
  {
    "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
    "property_name": "logp",
    "value": 1.2,
    "units": null,
    "confidence": 0.91,
    "model_name": "default",
    "model_version": "latest",
    "status": "completed",
    "created_at": "2023-09-15T12:30:05Z"
  }
]
```

`401 Unauthorized` - Unauthorized

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

`404 Not Found` - Molecule not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Molecule not found",
  "details": null,
  "status_code": 404
}
```

This endpoint returns all predictions for a molecule. Use the min_confidence parameter to filter predictions by confidence threshold.

### Get Latest Molecule Predictions

**GET /molecules/{molecule_id}/predictions/latest**

Get the latest predictions for each property of a molecule.

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|----|-------|-------------|
| molecule_id | path | string (uuid) | Yes | ID of the molecule |
| properties | query | string | No | Comma-separated list of properties to retrieve |

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

`200 OK` - Latest predictions by property

```json
{
  "solubility": {
    "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
    "property_name": "solubility",
    "value": 0.82,
    "units": "mg/mL",
    "confidence": 0.95,
    "model_name": "default",
    "model_version": "latest",
    "status": "completed",
    "created_at": "2023-09-15T12:30:05Z"
  },
  "permeability": {
    "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
    "property_name": "permeability",
    "value": 8.2e-06,
    "units": "cm/s",
    "confidence": 0.87,
    "model_name": "default",
    "model_version": "latest",
    "status": "completed",
    "created_at": "2023-09-15T12:30:05Z"
  },
  "logp": {
    "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
    "property_name": "logp",
    "value": 1.2,
    "units": null,
    "confidence": 0.91,
    "model_name": "default",
    "model_version": "latest",
    "status": "completed",
    "created_at": "2023-09-15T12:30:05Z"
  }
}
```

`401 Unauthorized` - Unauthorized

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

`404 Not Found` - Molecule not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Molecule not found",
  "details": null,
  "status_code": 404
}
```

This endpoint returns the latest prediction for each property of a molecule. If the properties parameter is provided, only the specified properties will be returned. Otherwise, all predicted properties will be returned.

### Filter Predictions

**POST /predictions/filter**

Filter predictions based on various criteria.

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|----|-------|-------------|
| skip | query | integer | No | Number of records to skip |
| limit | query | integer | No | Maximum number of records to return |

**Request:**

```json
{
  "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
  "property_names": ["solubility", "permeability"],
  "model_name": "default",
  "model_version": "latest",
  "status": "completed",
  "min_confidence": 0.8,
  "created_after": "2023-09-01T00:00:00Z",
  "created_before": "2023-09-30T23:59:59Z"
}
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

`200 OK` - Filtered predictions with pagination info

```json
{
  "items": [
    {
      "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
      "property_name": "solubility",
      "value": 0.82,
      "units": "mg/mL",
      "confidence": 0.95,
      "model_name": "default",
      "model_version": "latest",
      "status": "completed",
      "created_at": "2023-09-15T12:30:05Z"
    },
    {
      "molecule_id": "123e4567-e89b-12d3-a456-426614174002",
      "property_name": "permeability",
      "value": 8.2e-06,
      "units": "cm/s",
      "confidence": 0.87,
      "model_name": "default",
      "model_version": "latest",
      "status": "completed",
      "created_at": "2023-09-15T12:30:05Z"
    }
  ],
  "total": 2,
  "page": 1,
  "size": 100,
  "pages": 1
}
```

`400 Bad Request` - Invalid filter criteria

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid filter criteria",
  "details": {
    "property_names": "Unknown property: invalid_property"
  },
  "status_code": 400
}
```

`401 Unauthorized` - Unauthorized

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

All filter criteria are optional and combined with AND logic. The min_confidence parameter filters predictions by confidence threshold.

### Cancel Prediction Job

**DELETE /predictions/{batch_id}**

Cancel an ongoing prediction job.

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|----|-------|-------------|
| batch_id | path | string (uuid) | Yes | ID of the prediction batch to cancel |

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

`200 OK` - Prediction job cancelled successfully

```json
{
  "batch_id": "123e4567-e89b-12d3-a456-426614174005",
  "status": "failed",
  "message": "Job cancelled by user",
  "updated_at": "2023-09-15T13:35:00Z"
}
```

`400 Bad Request` - Cannot cancel job

```json
{
  "error_code": "INVALID_OPERATION",
  "message": "Cannot cancel job with status: completed",
  "details": null,
  "status_code": 400
}
```

`401 Unauthorized` - Unauthorized

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

`404 Not Found` - Prediction job not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Prediction job not found",
  "details": null,
  "status_code": 404
}
```

Only jobs with status 'pending' or 'processing' can be cancelled. Cancelled jobs will have their status set to 'failed' with an appropriate message.

### Retry Failed Prediction

**POST /predictions/{batch_id}/retry**

Retry a failed prediction job.

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|----|-------|-------------|
| batch_id | path | string (uuid) | Yes | ID of the failed prediction batch to retry |

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

`200 OK` - Prediction job retry initiated

```json
{
  "batch_id": "123e4567-e89b-12d3-a456-426614174005",
  "status": "pending",
  "message": "Job retry initiated",
  "updated_at": "2023-09-15T14:00:00Z"
}
```

`400 Bad Request` - Cannot retry job

```json
{
  "error_code": "INVALID_OPERATION",
  "message": "Cannot retry job with status: processing",
  "details": null,
  "status_code": 400
}
```

`401 Unauthorized` - Unauthorized

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

`404 Not Found` - Prediction job not found

```json
{
  "error_code": "NOT_FOUND",
  "message": "Prediction job not found",
  "details": null,
  "status_code": 404
}
```

Only jobs with status 'failed' can be retried. Retried jobs will have their status reset to 'pending' and will be resubmitted to the AI engine.

### Get Available Prediction Properties

**GET /predictions/properties**

Get the list of properties that can be predicted by AI.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

`200 OK` - List of predictable properties

```json
{
  "properties": [
    "logp",
    "solubility",
    "permeability",
    "clearance",
    "half_life",
    "bioavailability",
    "ic50",
    "ec50",
    "binding_affinity",
    "pka",
    "pkb"
  ]
}
```

`401 Unauthorized` - Unauthorized

```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

This endpoint returns the list of properties that can be predicted by the AI engine. These properties can be used in the prediction endpoints.

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

Common error codes for prediction endpoints include:

- `UNAUTHORIZED`: Not authenticated or token expired
- `VALIDATION_ERROR`: Invalid request data
- `NOT_FOUND`: Resource not found
- `INVALID_OPERATION`: Operation not allowed in current state
- `AI_ENGINE_ERROR`: Error from AI prediction engine
- `AI_SERVICE_UNAVAILABLE`: AI prediction service is unavailable
- `INTERNAL_ERROR`: Internal server error

## Rate Limiting

Prediction endpoints are rate-limited to prevent abuse. The current limits are:

- Single molecule prediction: 50 requests per minute per user
- Batch prediction: 10 requests per minute per user
- Status and result endpoints: 100 requests per minute per user

When rate limits are exceeded, the API returns a 429 Too Many Requests response with a Retry-After header indicating when the client should retry.

## Pagination

The filter endpoint supports pagination using skip and limit parameters:

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

## Asynchronous Processing

Most prediction operations are processed asynchronously due to the computational intensity of AI predictions. The workflow is as follows:

1. Submit a prediction request (single or batch)
2. Receive a job ID and batch ID
3. Poll the job status endpoint until the status is 'completed' or 'failed'
4. Retrieve the prediction results

For single molecule predictions, you can set wait_for_results=true to wait for the predictions to complete synchronously, but this is only recommended for simple predictions that can complete within the API timeout (30 seconds).

## Confidence Scores

All predictions include a confidence score between 0 and 1, indicating the reliability of the prediction. Higher scores indicate higher confidence.

You can filter predictions by confidence using the min_confidence parameter in the relevant endpoints. This is useful for ensuring that only high-confidence predictions are used in decision-making processes.

## Predictable Properties

The following properties can be predicted by the AI engine:

- logp: Octanol-water partition coefficient
- solubility: Aqueous solubility (mg/mL)
- permeability: Cell permeability (cm/s)
- clearance: Metabolic clearance (mL/min/kg)
- half_life: Half-life in plasma (h)
- bioavailability: Oral bioavailability (%)
- ic50: Half maximal inhibitory concentration (nM)
- ec50: Half maximal effective concentration (nM)
- binding_affinity: Binding affinity to target (nM)
- pka: Acid dissociation constant
- pkb: Base dissociation constant

The list of available properties may be expanded over time. Use the /predictions/properties endpoint to get the current list of predictable properties.

## Related Resources

- [Molecules API](molecules.md): Manage molecular data
- [Libraries API](libraries.md): Organize molecules into libraries
- [CRO API](cro.md): Manage CRO services
- [Submissions API](submissions.md): Submit molecules for experimental testing
- [Results API](results.md): Manage experimental results