# Molecule API

This document describes the molecule-related endpoints for the Molecular Data Management and CRO Integration Platform API. These endpoints enable management of molecular data, including creation, retrieval, filtering, CSV processing, and AI-powered property prediction.

## Base URL

All API endpoints are relative to the base URL: `https://api.moleculeflow.com/api/v1`

## Authentication

All molecule endpoints require authentication. Include the access token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

See the [Authentication API](auth.md) documentation for details on obtaining tokens.

## Molecule Data Model

A molecule in the system is represented by the following data structure:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "smiles": "CC(C)CCO",
  "inchi_key": "KFZMGEQAYNKOFK-UHFFFAOYSA-N",
  "formula": "C5H12O",
  "molecular_weight": 88.15,
  "status": "available",
  "metadata": {
    "project": "Project X",
    "batch": "Batch 123"
  },
  "properties": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "molecule_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "logP",
      "value": 1.2,
      "units": null,
      "property_type": "NUMERIC",
      "source": "IMPORTED"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174002",
      "molecule_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "activity",
      "value": 4.5,
      "units": "nM",
      "property_type": "NUMERIC",
      "source": "IMPORTED"
    }
  ],
  "created_by": "123e4567-e89b-12d3-a456-426614174003",
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:30:00Z",
  "library_ids": [
    "123e4567-e89b-12d3-a456-426614174004",
    "123e4567-e89b-12d3-a456-426614174005"
  ],
  "structure_image": "https://api.moleculeflow.com/api/v1/molecules/123e4567-e89b-12d3-a456-426614174000/image"
}
```

The detailed molecule view also includes related data:

```json
{
  // ... all fields from above, plus:
  "predictions": [
    {
      "property": "solubility",
      "value": 0.82,
      "units": "mg/mL",
      "confidence": 0.95,
      "model": "SolubilityModel v2.1",
      "predicted_at": "2023-09-15T10:35:00Z"
    }
  ],
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174006",
      "property": "binding_affinity",
      "value": 85.2,
      "units": "%",
      "experiment_id": "123e4567-e89b-12d3-a456-426614174007",
      "measured_at": "2023-09-20T14:30:00Z"
    }
  ],
  "libraries": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174004",
      "name": "High Potency Candidates",
      "description": "Collection of high potency molecules"
    }
  ],
  "submissions": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174008",
      "name": "Binding Assay Batch 12",
      "status": "completed",
      "submitted_at": "2023-09-18T09:15:00Z"
    }
  ]
}
```

## Endpoints

### Create Molecule

**POST /molecules**

Create a new molecule from SMILES string.

**Request:**
```json
{
  "smiles": "CC(C)CCO",
  "properties": [
    {
      "name": "logP",
      "value": 1.2,
      "property_type": "NUMERIC",
      "source": "IMPORTED"
    },
    {
      "name": "activity",
      "value": 4.5,
      "units": "nM",
      "property_type": "NUMERIC",
      "source": "IMPORTED"
    }
  ],
  "library_ids": ["123e4567-e89b-12d3-a456-426614174004"]
}
```

**Response: 201 Created**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "smiles": "CC(C)CCO",
  "inchi_key": "KFZMGEQAYNKOFK-UHFFFAOYSA-N",
  "formula": "C5H12O",
  "molecular_weight": 88.15,
  "status": "available",
  "properties": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "molecule_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "logP",
      "value": 1.2,
      "property_type": "NUMERIC",
      "source": "IMPORTED"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174002",
      "molecule_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "activity",
      "value": 4.5,
      "units": "nM",
      "property_type": "NUMERIC",
      "source": "IMPORTED"
    }
  ],
  "created_by": "123e4567-e89b-12d3-a456-426614174003",
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:30:00Z",
  "library_ids": ["123e4567-e89b-12d3-a456-426614174004"]
}
```

**Response: 400 Bad Request**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid molecule data",
  "details": {
    "smiles": "Invalid SMILES string"
  },
  "status_code": 400
}
```

**Response: 401 Unauthorized**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Notes:**
- The SMILES string is validated for chemical correctness. If the molecule already exists (based on InChI Key), the existing molecule will be returned instead of creating a duplicate.

### Get Molecule

**GET /molecules/{molecule_id}**

Get detailed information about a specific molecule.

**Parameters:**
- `molecule_id` (path, required): ID of the molecule to retrieve

**Response: 200 OK**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "smiles": "CC(C)CCO",
  "inchi_key": "KFZMGEQAYNKOFK-UHFFFAOYSA-N",
  "formula": "C5H12O",
  "molecular_weight": 88.15,
  "status": "available",
  "properties": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "molecule_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "logP",
      "value": 1.2,
      "property_type": "NUMERIC",
      "source": "IMPORTED"
    }
  ],
  "created_by": "123e4567-e89b-12d3-a456-426614174003",
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:30:00Z",
  "predictions": [
    {
      "property": "solubility",
      "value": 0.82,
      "units": "mg/mL",
      "confidence": 0.95,
      "model": "SolubilityModel v2.1",
      "predicted_at": "2023-09-15T10:35:00Z"
    }
  ],
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174006",
      "property": "binding_affinity",
      "value": 85.2,
      "units": "%",
      "experiment_id": "123e4567-e89b-12d3-a456-426614174007",
      "measured_at": "2023-09-20T14:30:00Z"
    }
  ],
  "libraries": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174004",
      "name": "High Potency Candidates",
      "description": "Collection of high potency molecules"
    }
  ],
  "submissions": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174008",
      "name": "Binding Assay Batch 12",
      "status": "completed",
      "submitted_at": "2023-09-18T09:15:00Z"
    }
  ]
}
```

**Response: 401 Unauthorized**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Molecule not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
- The detailed view includes related data such as predictions, experimental results, libraries, and submissions.

### Get Molecule by SMILES

**GET /molecules/by-smiles**

Get a molecule by SMILES string.

**Parameters:**
- `smiles` (query, required): SMILES string of the molecule to retrieve

**Response: 200 OK**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "smiles": "CC(C)CCO",
  "inchi_key": "KFZMGEQAYNKOFK-UHFFFAOYSA-N",
  "formula": "C5H12O",
  "molecular_weight": 88.15,
  "status": "available",
  "properties": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "molecule_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "logP",
      "value": 1.2,
      "property_type": "NUMERIC",
      "source": "IMPORTED"
    }
  ],
  "created_by": "123e4567-e89b-12d3-a456-426614174003",
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:30:00Z"
}
```

**Response: 400 Bad Request**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid SMILES string",
  "details": null,
  "status_code": 400
}
```

**Response: 401 Unauthorized**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Molecule not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
- The SMILES string is normalized before searching, so equivalent representations will match the same molecule.

### Update Molecule

**PUT /molecules/{molecule_id}**

Update an existing molecule.

**Parameters:**
- `molecule_id` (path, required): ID of the molecule to update

**Request:**
```json
{
  "status": "testing",
  "metadata": {
    "project": "Project Y",
    "priority": "high"
  },
  "properties": [
    {
      "name": "solubility",
      "value": 0.82,
      "units": "mg/mL",
      "property_type": "NUMERIC",
      "source": "EXPERIMENTAL"
    }
  ]
}
```

**Response: 200 OK**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "smiles": "CC(C)CCO",
  "inchi_key": "KFZMGEQAYNKOFK-UHFFFAOYSA-N",
  "formula": "C5H12O",
  "molecular_weight": 88.15,
  "status": "testing",
  "metadata": {
    "project": "Project Y",
    "priority": "high"
  },
  "properties": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "molecule_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "logP",
      "value": 1.2,
      "property_type": "NUMERIC",
      "source": "IMPORTED"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174009",
      "molecule_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "solubility",
      "value": 0.82,
      "units": "mg/mL",
      "property_type": "NUMERIC",
      "source": "EXPERIMENTAL"
    }
  ],
  "created_by": "123e4567-e89b-12d3-a456-426614174003",
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T11:45:00Z"
}
```

**Response: 400 Bad Request**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid molecule data",
  "details": {
    "properties": "Invalid property value"
  },
  "status_code": 400
}
```

**Response: 401 Unauthorized**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Molecule not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
- Only the fields included in the request will be updated. To remove a field, set it to null explicitly. Properties are added or updated based on the property name.

### Delete Molecule

**DELETE /molecules/{molecule_id}**

Delete an existing molecule.

**Parameters:**
- `molecule_id` (path, required): ID of the molecule to delete

**Response: 200 OK**
```json
{
  "success": true
}
```

**Response: 401 Unauthorized**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Molecule not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
- Deleting a molecule will remove it from all libraries and submissions. This operation cannot be undone.

### Filter Molecules

**POST /molecules/filter**

Filter molecules based on various criteria.

**Parameters:**
- `skip` (query, optional): Number of records to skip (default: 0, minimum: 0)
- `limit` (query, optional): Maximum number of records to return (default: 100, minimum: 1, maximum: 1000)
- `sort_by` (query, optional): Property to sort by
- `descending` (query, optional): Sort in descending order (default: false)

**Request:**
```json
{
  "smiles_contains": "CCO",
  "formula_contains": "C5",
  "status": "available",
  "library_id": "123e4567-e89b-12d3-a456-426614174004",
  "property_ranges": {
    "logP": {
      "min": 1.0,
      "max": 2.0
    },
    "activity": {
      "min": 0,
      "max": 5.0
    }
  }
}
```

**Response: 200 OK**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "smiles": "CC(C)CCO",
      "inchi_key": "KFZMGEQAYNKOFK-UHFFFAOYSA-N",
      "formula": "C5H12O",
      "molecular_weight": 88.15,
      "status": "available",
      "properties": [
        {
          "id": "123e4567-e89b-12d3-a456-426614174001",
          "molecule_id": "123e4567-e89b-12d3-a456-426614174000",
          "name": "logP",
          "value": 1.2,
          "property_type": "NUMERIC",
          "source": "IMPORTED"
        },
        {
          "id": "123e4567-e89b-12d3-a456-426614174002",
          "molecule_id": "123e4567-e89b-12d3-a456-426614174000",
          "name": "activity",
          "value": 4.5,
          "units": "nM",
          "property_type": "NUMERIC",
          "source": "IMPORTED"
        }
      ],
      "created_by": "123e4567-e89b-12d3-a456-426614174003",
      "created_at": "2023-09-15T10:30:00Z",
      "updated_at": "2023-09-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 100,
  "pages": 1
}
```

**Response: 400 Bad Request**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid filter criteria",
  "details": {
    "property_ranges": "Min value must be less than or equal to max value"
  },
  "status_code": 400
}
```

**Response: 401 Unauthorized**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Notes:**
- All filter criteria are optional and combined with AND logic. The `smiles_contains` parameter performs substructure searching. Property ranges can be specified for numeric properties.

### Upload CSV File

**POST /molecules/upload-csv**

Upload a CSV file containing molecular data.

**Request:**
Content-Type: multipart/form-data
```
file: (binary CSV file)
```

**Response: 202 Accepted**
```json
{
  "success": true,
  "file_url": "uploads/molecules/2023-09-15/user123_file.csv",
  "filename": "molecules.csv",
  "size": 1024
}
```

**Response: 400 Bad Request**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid CSV file",
  "details": {
    "file": "File must be a CSV file"
  },
  "status_code": 400
}
```

**Response: 401 Unauthorized**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Notes:**
- The CSV file should contain a SMILES column and optional property columns. The file is stored temporarily and must be processed with the /molecules/process-csv endpoint. Maximum file size is 100MB.

### Get CSV Preview

**GET /molecules/csv-preview**

Get a preview of CSV data for column mapping.

**Parameters:**
- `file_url` (query, required): URL of the uploaded CSV file
- `num_rows` (query, optional): Number of rows to preview (default: 5, minimum: 1, maximum: 20)

**Response: 200 OK**
```json
{
  "headers": ["SMILES", "MW", "LogP", "Activity"],
  "preview_data": [
    ["CC(C)CCO", "88.15", "1.2", "4.5"],
    ["c1ccccc1", "78.11", "2.1", "3.2"],
    ["CCN(CC)CC", "101.19", "0.8", "5.1"]
  ],
  "mapping_suggestions": {
    "SMILES": "smiles",
    "MW": "molecular_weight",
    "LogP": "logP",
    "Activity": "activity"
  }
}
```

**Response: 400 Bad Request**
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

**Response: 401 Unauthorized**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "CSV file not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
- This endpoint provides a preview of the CSV data and suggests column mappings based on header names. Use this information to create a mapping for the /molecules/process-csv endpoint.

### Process CSV File

**POST /molecules/process-csv**

Process a previously uploaded CSV file.

**Request:**
```json
{
  "file_url": "uploads/molecules/2023-09-15/user123_file.csv",
  "column_mapping": {
    "SMILES": "smiles",
    "MW": "molecular_weight",
    "LogP": "logP",
    "Activity": "activity"
  },
  "has_header": true,
  "delimiter": ",",
  "library_id": "123e4567-e89b-12d3-a456-426614174004"
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "total_rows": 100,
  "processed_rows": 98,
  "failed_rows": 2,
  "errors": [
    {
      "row": 5,
      "error": "Invalid SMILES string"
    },
    {
      "row": 23,
      "error": "Invalid property value for LogP"
    }
  ],
  "molecules_created": 75,
  "molecules_updated": 23,
  "library_id": "123e4567-e89b-12d3-a456-426614174004"
}
```

**Response: 400 Bad Request**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request",
  "details": {
    "column_mapping": "SMILES column mapping is required"
  },
  "status_code": 400
}
```

**Response: 401 Unauthorized**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "CSV file not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
- The column_mapping must include a mapping for the SMILES column. Other columns are optional. If library_id is provided, all successfully processed molecules will be added to that library.

### Predict Properties

**POST /molecules/{molecule_id}/predict**

Request property predictions from AI engine for a molecule.

**Parameters:**
- `molecule_id` (path, required): ID of the molecule
- `wait_for_results` (query, optional): Wait for prediction results (default: false)

**Request:**
```json
{
  "properties": ["solubility", "permeability", "toxicity"]
}
```

**Response: 200 OK** (when wait_for_results=false)
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174010",
  "status": "queued",
  "progress": 0,
  "message": "Prediction job queued",
  "created_at": "2023-09-15T12:30:00Z",
  "updated_at": "2023-09-15T12:30:00Z"
}
```

**Response: 200 OK** (when wait_for_results=true)
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174010",
  "status": "completed",
  "results": [
    {
      "molecule_id": "123e4567-e89b-12d3-a456-426614174000",
      "smiles": "CC(C)CCO",
      "predictions": [
        {
          "property": "solubility",
          "value": 0.82,
          "units": "mg/mL",
          "confidence": 0.95
        },
        {
          "property": "permeability",
          "value": 8.2e-06,
          "units": "cm/s",
          "confidence": 0.87
        },
        {
          "property": "toxicity",
          "value": 0.2,
          "units": null,
          "confidence": 0.91
        }
      ]
    }
  ],
  "model_name": "MoleculeAI",
  "model_version": "2.1",
  "created_at": "2023-09-15T12:30:00Z",
  "completed_at": "2023-09-15T12:30:05Z"
}
```

**Response: 400 Bad Request**
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

**Response: 401 Unauthorized**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Molecule not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
- If properties are not specified, all available predictable properties will be calculated. When wait_for_results=false, the endpoint returns immediately with a job ID that can be used to check the status later. When wait_for_results=true, the endpoint waits for the predictions to complete before returning (with a timeout of 30 seconds).

### Batch Predict Properties

**POST /molecules/batch-predict**

Request property predictions for multiple molecules.

**Request:**
```json
{
  "molecule_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "123e4567-e89b-12d3-a456-426614174011",
    "123e4567-e89b-12d3-a456-426614174012"
  ],
  "properties": ["solubility", "permeability", "toxicity"]
}
```

**Response: 202 Accepted**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174013",
  "status": "queued",
  "progress": 0,
  "message": "Batch prediction job queued",
  "molecule_count": 3,
  "created_at": "2023-09-15T13:30:00Z",
  "updated_at": "2023-09-15T13:30:00Z"
}
```

**Response: 400 Bad Request**
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

**Response: 401 Unauthorized**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Notes:**
- This endpoint always operates asynchronously. The job_id can be used to check the status and retrieve results using the predictions API endpoints. Maximum batch size is 100 molecules.

### Bulk Operation

**POST /molecules/bulk-operation**

Perform bulk operations on multiple molecules.

**Request:**
```json
{
  "molecule_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "123e4567-e89b-12d3-a456-426614174011",
    "123e4567-e89b-12d3-a456-426614174012"
  ],
  "operation": "add_to_library",
  "parameters": {
    "library_id": "123e4567-e89b-12d3-a456-426614174004"
  }
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "operation": "add_to_library",
  "total": 3,
  "successful": 3,
  "failed": 0,
  "errors": []
}
```

**Response: 400 Bad Request**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request",
  "details": {
    "operation": "Unsupported operation: invalid_operation"
  },
  "status_code": 400
}
```

**Response: 401 Unauthorized**
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Notes:**
- Supported operations include:
- add_to_library: Add molecules to a library (requires library_id parameter)
- remove_from_library: Remove molecules from a library (requires library_id parameter)
- predict_properties: Request predictions for molecules (optional properties parameter)
- update_status: Update status for molecules (requires status parameter)

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
- `ALREADY_EXISTS`: Resource already exists
- `PROCESSING_ERROR`: Error during processing
- `AI_ENGINE_ERROR`: Error from AI prediction engine
- `INTERNAL_ERROR`: Internal server error

## Rate Limiting

API endpoints are rate-limited to prevent abuse. The current limits are:

- Standard endpoints: 100 requests per minute per user
- CSV processing: 10 requests per minute per user
- AI prediction: 50 requests per minute per user

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

## Sorting

List and filter endpoints support sorting using sort_by and descending parameters:

- sort_by: Property to sort by (e.g., "molecular_weight", "created_at")
- descending: Sort in descending order (default: false)

For sorting by a specific property, use the format "property:name" (e.g., "property:logP").

## Filtering

The /molecules/filter endpoint supports advanced filtering capabilities:

- smiles_contains: Substructure search using SMILES pattern
- formula_contains: Search by molecular formula substring
- status: Filter by molecule status
- created_by: Filter by creator ID
- library_id: Filter by library membership
- property_ranges: Filter by property value ranges

Property ranges can be specified with min/max for numeric properties, equals for exact matches, or contains for string properties:

```json
{
  "property_ranges": {
    "logP": {
      "min": 1.0,
      "max": 5.0
    },
    "activity": {
      "min": 0,
      "max": 10.0
    },
    "category": {
      "equals": "lead"
    },
    "notes": {
      "contains": "potent"
    }
  }
}
```

## CSV Processing

CSV processing follows a two-step workflow:

1. Upload the CSV file using /molecules/upload-csv
2. Process the file using /molecules/process-csv with column mapping

The CSV file should contain at least a SMILES column and can include additional property columns. The column mapping defines how CSV columns map to molecule properties.

Standard properties include:

- smiles: SMILES string (required)
- inchi_key: InChI Key
- formula: Molecular formula
- molecular_weight: Molecular weight in g/mol
- status: Molecule status

Any other columns will be treated as custom properties. The property_type will be inferred from the data but can be explicitly specified in the column mapping:

```json
{
  "column_mapping": {
    "SMILES": "smiles",
    "MW": "molecular_weight",
    "LogP": "logP",
    "Activity": {
      "name": "activity",
      "property_type": "NUMERIC",
      "units": "nM"
    }
  }
}
```

## AI Property Prediction

The platform integrates with an AI engine to predict molecular properties. Predictions can be requested for individual molecules or in batch mode.

Predictable properties include:

- solubility: Aqueous solubility (mg/mL)
- permeability: Cell permeability (cm/s)
- logD: Distribution coefficient at pH 7.4
- clearance: Metabolic clearance (mL/min/kg)
- plasma_binding: Plasma protein binding (%)
- bioavailability: Oral bioavailability (%)
- toxicity: Toxicity risk (0-1 scale)
- hERG: hERG channel inhibition risk (0-1 scale)

Predictions include confidence scores (0-1) indicating the reliability of the prediction. Higher scores indicate higher confidence.

## Molecule Libraries

Molecules can be organized into libraries for easier management. A molecule can belong to multiple libraries simultaneously.

Libraries can be created and managed using the [Libraries API](libraries.md). Molecules can be added to libraries during creation, through the update endpoint, or using the bulk operation endpoint.

## CRO Submissions

Molecules can be submitted to Contract Research Organizations (CROs) for experimental testing. The submission process and management are handled through the [Submissions API](submissions.md).

Experimental results are associated with molecules and can be viewed in the detailed molecule view.