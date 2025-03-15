import { useState, useCallback, useEffect } from 'react'; // react v18.0.0
import { PaginationParams } from '../types/api.types';

/**
 * Options for configuring the pagination hook
 */
interface PaginationOptions {
  initialPage?: number;
  initialLimit?: number;
  total: number;
  onPageChange?: (page: number) => void;
  onLimitChange?: (limit: number) => void;
}

/**
 * Return type of the usePagination hook
 */
interface PaginationResult {
  // Current page state
  page: number;
  limit: number;
  totalPages: number;
  
  // Page change handlers
  handlePageChange: (page: number) => void;
  handleLimitChange: (limit: number) => void;
  
  // Navigation functions
  goToFirstPage: () => void;
  goToPreviousPage: () => void;
  goToNextPage: () => void;
  goToLastPage: () => void;
  
  // Pagination metadata (0-based indices for array slicing)
  startIndex: number;
  endIndex: number;
  
  // API params object
  paginationParams: PaginationParams;
}

/**
 * A hook that manages pagination state and provides pagination control functions
 * 
 * @param options - Configuration options for the pagination
 * @returns Pagination state and control functions
 */
export const usePagination = ({
  initialPage = 1,
  initialLimit = 10,
  total = 0,
  onPageChange,
  onLimitChange
}: PaginationOptions): PaginationResult => {
  // Initialize state for page and items per page
  const [page, setPage] = useState<number>(initialPage);
  const [limit, setLimit] = useState<number>(initialLimit);
  
  // Calculate total pages
  const totalPages = Math.max(1, Math.ceil(total / limit));
  
  // Ensure current page is within valid range when dependencies change
  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [total, limit, page, totalPages]);
  
  // Handle page change
  const handlePageChange = useCallback((newPage: number) => {
    const validPage = Math.min(Math.max(1, newPage), totalPages);
    setPage(validPage);
    if (onPageChange) {
      onPageChange(validPage);
    }
  }, [totalPages, onPageChange]);
  
  // Handle items per page change
  const handleLimitChange = useCallback((newLimit: number) => {
    setLimit(newLimit);
    setPage(1); // Reset to first page when changing limit
    if (onLimitChange) {
      onLimitChange(newLimit);
    }
  }, [onLimitChange]);
  
  // Navigation functions
  const goToFirstPage = useCallback(() => {
    handlePageChange(1);
  }, [handlePageChange]);
  
  const goToPreviousPage = useCallback(() => {
    handlePageChange(page - 1);
  }, [handlePageChange, page]);
  
  const goToNextPage = useCallback(() => {
    handlePageChange(page + 1);
  }, [handlePageChange, page]);
  
  const goToLastPage = useCallback(() => {
    handlePageChange(totalPages);
  }, [handlePageChange, totalPages]);
  
  // Calculate start and end indices for the current page (0-based for array slicing)
  const startIndex = (page - 1) * limit;
  const endIndex = Math.min(startIndex + limit - 1, total - 1);
  
  // Create paginationParams object for API requests
  const paginationParams: PaginationParams = {
    page,
    page_size: limit,
    sort_by: null,
    sort_order: null
  };
  
  // Return pagination state and control functions
  return {
    page,
    limit,
    totalPages,
    handlePageChange,
    handleLimitChange,
    goToFirstPage,
    goToPreviousPage,
    goToNextPage,
    goToLastPage,
    startIndex,
    endIndex,
    paginationParams
  };
};