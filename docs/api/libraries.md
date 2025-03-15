# Library API

This document describes the library-related endpoints for the Molecular Data Management and CRO Integration Platform API. These endpoints enable management of molecule libraries, including creation, retrieval, filtering, and molecule organization.

## Base URL

All API endpoints are relative to the base URL: `https://api.moleculeflow.com/api/v1`

For example, the full URL for the libraries endpoint would be: `https://api.moleculeflow.com/api/v1/libraries`

## Authentication

All library endpoints require authentication. Include the access token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

See the [Authentication API](auth.md) documentation for details on obtaining tokens.

## Library Data Model

A library in the system is represented by the following data structure:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "High Potency Candidates",
  "description": "Collection of high potency molecules for Project X",
  "owner_id": "123e4567-e89b-12d3-a456-426614174001",
  "organization_id": "123e4567-e89b-12d3-a456-426614174002",
  "is_public": false,
  "metadata": {
    "project": "Project X",
    "priority": "high"
  },
  "molecule_count": 42,
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:30:00Z",
  "owner": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "full_name": "John Smith"
  }
}
```

When retrieving a library with its molecules, the response includes the molecules list:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "High Potency Candidates",
  "description": "Collection of high potency molecules for Project X",
  "owner_id": "123e4567-e89b-12d3-a456-426614174001",
  "organization_id": "123e4567-e89b-12d3-a456-426614174002",
  "is_public": false,
  "metadata": {
    "project": "Project X",
    "priority": "high"
  },
  "molecule_count": 42,
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:30:00Z",
  "owner": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "full_name": "John Smith"
  },
  "molecules": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "smiles": "CC(C)CCO",
      "inchi_key": "KFZMGEQAYNKOFK-UHFFFAOYSA-N",
      "formula": "C5H12O",
      "molecular_weight": 88.15,
      "status": "available"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174004",
      "smiles": "c1ccccc1",
      "inchi_key": "UHOVQNZJYSORNB-UHFFFAOYSA-N",
      "formula": "C6H6",
      "molecular_weight": 78.11,
      "status": "available"
    }
  ]
}
```

## Endpoints

### Create Library

**POST /libraries**

Create a new molecule library.

**Request:**
```json
{
  "name": "High Potency Candidates",
  "description": "Collection of high potency molecules for Project X",
  "is_public": false,
  "metadata": {
    "project": "Project X",
    "priority": "high"
  },
  "organization_id": "123e4567-e89b-12d3-a456-426614174002"
}
```

**Response: 201 Created**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "High Potency Candidates",
  "description": "Collection of high potency molecules for Project X",
  "owner_id": "123e4567-e89b-12d3-a456-426614174001",
  "organization_id": "123e4567-e89b-12d3-a456-426614174002",
  "is_public": false,
  "metadata": {
    "project": "Project X",
    "priority": "high"
  },
  "molecule_count": 0,
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:30:00Z",
  "owner": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "full_name": "John Smith"
  }
}
```

**Response: 400 Bad Request**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid library data",
  "details": {
    "name": "Library name is required and must be between 1 and 100 characters"
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
The library is created with the current user as the owner. The `organization_id` is optional and defaults to the user's organization if not provided.

### Get Library

**GET /libraries/{library_id}**

Get detailed information about a specific library.

**Parameters:**
- `library_id` (path, required): ID of the library to retrieve

**Response: 200 OK**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "High Potency Candidates",
  "description": "Collection of high potency molecules for Project X",
  "owner_id": "123e4567-e89b-12d3-a456-426614174001",
  "organization_id": "123e4567-e89b-12d3-a456-426614174002",
  "is_public": false,
  "metadata": {
    "project": "Project X",
    "priority": "high"
  },
  "molecule_count": 42,
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:30:00Z",
  "owner": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "full_name": "John Smith"
  }
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

**Response: 403 Forbidden**
```json
{
  "error_code": "FORBIDDEN",
  "message": "Insufficient permissions to access this library",
  "details": null,
  "status_code": 403
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Library not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
Users can only access libraries they own, libraries in their organization, or public libraries.

### Get Library with Molecules

**GET /libraries/{library_id}/molecules**

Get a library with its molecules.

**Parameters:**
- `library_id` (path, required): ID of the library to retrieve
- `skip` (query, optional): Number of records to skip
- `limit` (query, optional): Maximum number of records to return
- `sort_by` (query, optional): Property to sort by
- `descending` (query, optional): Sort in descending order

**Response: 200 OK**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "High Potency Candidates",
  "description": "Collection of high potency molecules for Project X",
  "owner_id": "123e4567-e89b-12d3-a456-426614174001",
  "organization_id": "123e4567-e89b-12d3-a456-426614174002",
  "is_public": false,
  "metadata": {
    "project": "Project X",
    "priority": "high"
  },
  "molecule_count": 42,
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T10:30:00Z",
  "owner": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "full_name": "John Smith"
  },
  "molecules": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "smiles": "CC(C)CCO",
      "inchi_key": "KFZMGEQAYNKOFK-UHFFFAOYSA-N",
      "formula": "C5H12O",
      "molecular_weight": 88.15,
      "status": "available"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174004",
      "smiles": "c1ccccc1",
      "inchi_key": "UHOVQNZJYSORNB-UHFFFAOYSA-N",
      "formula": "C6H6",
      "molecular_weight": 78.11,
      "status": "available"
    }
  ],
  "total": 42,
  "page": 1,
  "size": 100,
  "pages": 1
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

**Response: 403 Forbidden**
```json
{
  "error_code": "FORBIDDEN",
  "message": "Insufficient permissions to access this library",
  "details": null,
  "status_code": 403
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Library not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
This endpoint returns the library with its molecules, paginated for performance. The molecules are returned in a simplified format. For detailed molecule information, use the molecule endpoints.

### List Libraries

**GET /libraries**

List libraries accessible to the current user.

**Parameters:**
- `skip` (query, optional): Number of records to skip
- `limit` (query, optional): Maximum number of records to return

**Response: 200 OK**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "High Potency Candidates",
      "description": "Collection of high potency molecules for Project X",
      "owner_id": "123e4567-e89b-12d3-a456-426614174001",
      "organization_id": "123e4567-e89b-12d3-a456-426614174002",
      "is_public": false,
      "metadata": {
        "project": "Project X",
        "priority": "high"
      },
      "molecule_count": 42,
      "created_at": "2023-09-15T10:30:00Z",
      "updated_at": "2023-09-15T10:30:00Z",
      "owner": {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "full_name": "John Smith"
      }
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174005",
      "name": "Fragments",
      "description": "Fragment library for screening",
      "owner_id": "123e4567-e89b-12d3-a456-426614174001",
      "organization_id": "123e4567-e89b-12d3-a456-426614174002",
      "is_public": true,
      "metadata": {},
      "molecule_count": 156,
      "created_at": "2023-09-10T14:20:00Z",
      "updated_at": "2023-09-10T14:20:00Z",
      "owner": {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "full_name": "John Smith"
      }
    }
  ],
  "total": 8,
  "page": 1,
  "size": 100,
  "pages": 1
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
This endpoint returns libraries that the user owns, libraries in the user's organization, and public libraries.

### Update Library

**PUT /libraries/{library_id}**

Update an existing library.

**Parameters:**
- `library_id` (path, required): ID of the library to update

**Request:**
```json
{
  "name": "Updated Library Name",
  "description": "Updated description for the library",
  "is_public": true,
  "metadata": {
    "project": "Project Y",
    "priority": "medium"
  }
}
```

**Response: 200 OK**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Updated Library Name",
  "description": "Updated description for the library",
  "owner_id": "123e4567-e89b-12d3-a456-426614174001",
  "organization_id": "123e4567-e89b-12d3-a456-426614174002",
  "is_public": true,
  "metadata": {
    "project": "Project Y",
    "priority": "medium"
  },
  "molecule_count": 42,
  "created_at": "2023-09-15T10:30:00Z",
  "updated_at": "2023-09-15T11:45:00Z",
  "owner": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "full_name": "John Smith"
  }
}
```

**Response: 400 Bad Request**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid library data",
  "details": {
    "name": "Library name must be between 1 and 100 characters"
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

**Response: 403 Forbidden**
```json
{
  "error_code": "FORBIDDEN",
  "message": "Insufficient permissions to update this library",
  "details": null,
  "status_code": 403
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Library not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
Only the library owner or users with appropriate permissions can update a library. All fields in the request are optional - only the provided fields will be updated.

### Delete Library

**DELETE /libraries/{library_id}**

Delete an existing library.

**Parameters:**
- `library_id` (path, required): ID of the library to delete

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

**Response: 403 Forbidden**
```json
{
  "error_code": "FORBIDDEN",
  "message": "Insufficient permissions to delete this library",
  "details": null,
  "status_code": 403
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Library not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
Only the library owner or users with appropriate permissions can delete a library. Deleting a library does not delete the molecules in the library - it only removes the library and its associations with molecules.

### Filter Libraries

**POST /libraries/filter**

Filter libraries based on various criteria.

**Parameters:**
- `skip` (query, optional): Number of records to skip
- `limit` (query, optional): Maximum number of records to return
- `sort_by` (query, optional): Property to sort by
- `descending` (query, optional): Sort in descending order

**Request:**
```json
{
  "name_contains": "potency",
  "owner_id": "123e4567-e89b-12d3-a456-426614174001",
  "organization_id": "123e4567-e89b-12d3-a456-426614174002",
  "is_public": false,
  "contains_molecule_id": "123e4567-e89b-12d3-a456-426614174003"
}
```

**Response: 200 OK**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "High Potency Candidates",
      "description": "Collection of high potency molecules for Project X",
      "owner_id": "123e4567-e89b-12d3-a456-426614174001",
      "organization_id": "123e4567-e89b-12d3-a456-426614174002",
      "is_public": false,
      "metadata": {
        "project": "Project X",
        "priority": "high"
      },
      "molecule_count": 42,
      "created_at": "2023-09-15T10:30:00Z",
      "updated_at": "2023-09-15T10:30:00Z",
      "owner": {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "full_name": "John Smith"
      }
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
    "owner_id": "Invalid UUID format"
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
All filter criteria are optional and combined with AND logic. The `name_contains` parameter performs a case-insensitive substring search on library names. The `contains_molecule_id` parameter filters libraries that contain the specified molecule.

### Add Molecules to Library

**POST /libraries/molecules/add**

Add molecules to a library.

**Request:**
```json
{
  "library_id": "123e4567-e89b-12d3-a456-426614174000",
  "molecule_ids": [
    "123e4567-e89b-12d3-a456-426614174003",
    "123e4567-e89b-12d3-a456-426614174004",
    "123e4567-e89b-12d3-a456-426614174006"
  ],
  "operation": "add"
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "added": 3,
  "skipped": 0,
  "message": "3 molecules added to library"
}
```

**Response: 400 Bad Request**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request",
  "details": {
    "molecule_ids": "At least one molecule ID is required",
    "operation": "Operation must be 'add'"
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

**Response: 403 Forbidden**
```json
{
  "error_code": "FORBIDDEN",
  "message": "Insufficient permissions to modify this library",
  "details": null,
  "status_code": 403
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Library not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
Only the library owner or users with appropriate permissions can add molecules to a library. If a molecule is already in the library, it will be skipped (not added again).

### Remove Molecules from Library

**POST /libraries/molecules/remove**

Remove molecules from a library.

**Request:**
```json
{
  "library_id": "123e4567-e89b-12d3-a456-426614174000",
  "molecule_ids": [
    "123e4567-e89b-12d3-a456-426614174003",
    "123e4567-e89b-12d3-a456-426614174004"
  ],
  "operation": "remove"
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "removed": 2,
  "skipped": 0,
  "message": "2 molecules removed from library"
}
```

**Response: 400 Bad Request**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request",
  "details": {
    "molecule_ids": "At least one molecule ID is required",
    "operation": "Operation must be 'remove'"
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

**Response: 403 Forbidden**
```json
{
  "error_code": "FORBIDDEN",
  "message": "Insufficient permissions to modify this library",
  "details": null,
  "status_code": 403
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Library not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
Only the library owner or users with appropriate permissions can remove molecules from a library. If a molecule is not in the library, it will be skipped.

### Get User Libraries

**GET /libraries/user/{user_id}**

Get libraries owned by a specific user.

**Parameters:**
- `user_id` (path, required): ID of the user
- `skip` (query, optional): Number of records to skip
- `limit` (query, optional): Maximum number of records to return

**Response: 200 OK**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "High Potency Candidates",
      "description": "Collection of high potency molecules for Project X",
      "owner_id": "123e4567-e89b-12d3-a456-426614174001",
      "organization_id": "123e4567-e89b-12d3-a456-426614174002",
      "is_public": false,
      "metadata": {
        "project": "Project X",
        "priority": "high"
      },
      "molecule_count": 42,
      "created_at": "2023-09-15T10:30:00Z",
      "updated_at": "2023-09-15T10:30:00Z",
      "owner": {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "full_name": "John Smith"
      }
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174005",
      "name": "Fragments",
      "description": "Fragment library for screening",
      "owner_id": "123e4567-e89b-12d3-a456-426614174001",
      "organization_id": "123e4567-e89b-12d3-a456-426614174002",
      "is_public": true,
      "metadata": {},
      "molecule_count": 156,
      "created_at": "2023-09-10T14:20:00Z",
      "updated_at": "2023-09-10T14:20:00Z",
      "owner": {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "full_name": "John Smith"
      }
    }
  ],
  "total": 8,
  "page": 1,
  "size": 100,
  "pages": 1
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
  "message": "User not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
This endpoint returns libraries owned by the specified user. For users outside the owner's organization, only public libraries are returned.

### Get Organization Libraries

**GET /libraries/organization/{organization_id}**

Get libraries belonging to a specific organization.

**Parameters:**
- `organization_id` (path, required): ID of the organization
- `skip` (query, optional): Number of records to skip
- `limit` (query, optional): Maximum number of records to return

**Response: 200 OK**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "High Potency Candidates",
      "description": "Collection of high potency molecules for Project X",
      "owner_id": "123e4567-e89b-12d3-a456-426614174001",
      "organization_id": "123e4567-e89b-12d3-a456-426614174002",
      "is_public": false,
      "metadata": {
        "project": "Project X",
        "priority": "high"
      },
      "molecule_count": 42,
      "created_at": "2023-09-15T10:30:00Z",
      "updated_at": "2023-09-15T10:30:00Z",
      "owner": {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "full_name": "John Smith"
      }
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174005",
      "name": "Fragments",
      "description": "Fragment library for screening",
      "owner_id": "123e4567-e89b-12d3-a456-426614174001",
      "organization_id": "123e4567-e89b-12d3-a456-426614174002",
      "is_public": true,
      "metadata": {},
      "molecule_count": 156,
      "created_at": "2023-09-10T14:20:00Z",
      "updated_at": "2023-09-10T14:20:00Z",
      "owner": {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "full_name": "John Smith"
      }
    }
  ],
  "total": 12,
  "page": 1,
  "size": 100,
  "pages": 1
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

**Response: 403 Forbidden**
```json
{
  "error_code": "FORBIDDEN",
  "message": "Insufficient permissions to access this organization's libraries",
  "details": null,
  "status_code": 403
}
```

**Response: 404 Not Found**
```json
{
  "error_code": "NOT_FOUND",
  "message": "Organization not found",
  "details": null,
  "status_code": 404
}
```

**Notes:**
This endpoint returns libraries belonging to the specified organization. Users can only access libraries from their own organization or public libraries from other organizations.

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
- `FORBIDDEN`: Insufficient permissions to access the resource
- `VALIDATION_ERROR`: Invalid request data
- `NOT_FOUND`: Resource not found
- `ALREADY_EXISTS`: Resource already exists
- `INTERNAL_ERROR`: Internal server error

## Rate Limiting

API endpoints are rate-limited to prevent abuse. The current limits are:

- Standard endpoints: 100 requests per minute per user
- Bulk operations: 20 requests per minute per user

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

- sort_by: Property to sort by (e.g., "name", "created_at", "molecule_count")
- descending: Sort in descending order (default: false)

## Access Control

Libraries have the following access control rules:

- Library owners have full access to their libraries
- Users in the same organization can access all libraries in their organization
- Public libraries are accessible to all authenticated users
- Private libraries are only accessible to users in the same organization

Access control is enforced at the API level for all library operations.

## Related Endpoints

The following endpoints in other API sections are related to library management:

- [GET /molecules/{molecule_id}](molecules.md#get-molecule): Get a molecule with its library memberships
- [POST /molecules/filter](molecules.md#filter-molecules): Filter molecules by library membership
- [POST /molecules/bulk-operation](molecules.md#bulk-operation): Add or remove multiple molecules from libraries

See the [Molecules API](molecules.md) documentation for more details on these endpoints.