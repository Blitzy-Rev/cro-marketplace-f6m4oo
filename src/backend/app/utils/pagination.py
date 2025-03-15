import fastapi
import typing
from fastapi import Depends, Query
from typing import Dict, Optional

# Default pagination settings
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1

def get_pagination_params(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: Optional[int] = Query(
        None, 
        ge=MIN_PAGE_SIZE,
        le=MAX_PAGE_SIZE,
        description=f"Number of items to return (min: {MIN_PAGE_SIZE}, max: {MAX_PAGE_SIZE}, default: {DEFAULT_PAGE_SIZE})"
    )
) -> Dict[str, int]:
    """
    FastAPI dependency that extracts and validates pagination parameters from request query parameters.
    
    Args:
        skip: Number of items to skip (offset)
        limit: Number of items per page to return
        
    Returns:
        Dict[str, int]: Dictionary containing validated skip and limit parameters
    """
    # If limit is not provided or is None, use default page size
    if limit is None:
        limit = DEFAULT_PAGE_SIZE
    
    # Ensure limit is within allowed range
    limit = max(MIN_PAGE_SIZE, min(MAX_PAGE_SIZE, limit))
    
    return {"skip": skip, "limit": limit}

def paginate_response(
    items: list,
    total_count: int,
    skip: int,
    limit: int
) -> Dict[str, object]:
    """
    Creates a standardized paginated response with data and pagination metadata.
    
    Args:
        items: List of items for the current page
        total_count: Total number of items across all pages
        skip: Number of items skipped (offset)
        limit: Number of items per page
        
    Returns:
        Dict[str, object]: Dictionary with data items and pagination metadata
    """
    # Calculate total pages
    total_pages = (total_count + limit - 1) // limit if limit > 0 else 0
    
    # Calculate current page (1-based)
    current_page = (skip // limit) + 1 if limit > 0 else 1
    
    # Determine if there are next/previous pages
    has_next = current_page < total_pages
    has_previous = current_page > 1
    
    return {
        "items": items,
        "pagination": {
            "total_count": total_count,
            "page_size": limit,
            "current_page": current_page,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous
        }
    }

def calculate_skip(page: int, page_size: int) -> int:
    """
    Calculates the skip parameter value from page number and page size.
    
    Args:
        page: Page number (1-based)
        page_size: Number of items per page
        
    Returns:
        int: Skip value for database query
    """
    # Ensure page is at least 1
    page = max(1, page)
    
    # Calculate skip value
    skip = (page - 1) * page_size
    
    return skip