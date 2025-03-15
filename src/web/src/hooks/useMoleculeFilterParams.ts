import { useState, useEffect, useCallback, useMemo } from 'react'; // ^18.0.0
import { useSearchParams, useNavigate } from 'react-router-dom'; // ^6.4.0

import { MoleculeFilter, PropertyFilter, MoleculeStatus } from '../types/molecule.types';
import { FILTERABLE_PROPERTIES, PROPERTY_RANGES } from '../constants/moleculeProperties';
import useDebounce from './useDebounce';
import { validateNumericRange } from '../utils/validators';

/**
 * Parses URL search parameters to extract molecule filter values
 * 
 * @param searchParams Current URL search parameters
 * @param defaultFilters Optional default filter values
 * @returns Molecule filter object parsed from URL parameters
 */
function parseFiltersFromUrl(
  searchParams: URLSearchParams,
  defaultFilters: Partial<MoleculeFilter> = {}
): MoleculeFilter {
  // Initialize with default values
  const filters: MoleculeFilter = {
    search: null,
    library_id: null,
    status: null,
    properties: [],
    sort_by: null,
    sort_order: null,
    ...defaultFilters
  };

  // Extract search term
  const search = searchParams.get('search');
  if (search) {
    filters.search = search;
  }

  // Extract library ID
  const libraryId = searchParams.get('library_id');
  if (libraryId) {
    filters.library_id = libraryId;
  }

  // Extract status
  const status = searchParams.get('status');
  if (status) {
    // Handle single status
    if (Object.values(MoleculeStatus).includes(status as MoleculeStatus)) {
      filters.status = status as MoleculeStatus;
    } 
    // Handle multiple statuses separated by commas
    else if (status.includes(',')) {
      const statusArray = status.split(',').filter(s => 
        Object.values(MoleculeStatus).includes(s as MoleculeStatus)
      ) as MoleculeStatus[];
      
      if (statusArray.length > 0) {
        filters.status = statusArray;
      }
    }
  }

  // Extract sort parameters
  const sortBy = searchParams.get('sort_by');
  if (sortBy) {
    filters.sort_by = sortBy;
  }

  const sortOrder = searchParams.get('sort_order');
  if (sortOrder && (sortOrder === 'asc' || sortOrder === 'desc')) {
    filters.sort_order = sortOrder as 'asc' | 'desc';
  }

  // Extract property filters
  const properties: PropertyFilter[] = [];
  
  // Iterate through filterable properties to look for URL parameters
  for (const propName of FILTERABLE_PROPERTIES) {
    const minParam = searchParams.get(`${propName}_min`);
    const maxParam = searchParams.get(`${propName}_max`);
    const exactParam = searchParams.get(propName);
    const includeNullParam = searchParams.get(`${propName}_include_null`);
    
    // Skip if no parameters found for this property
    if (!minParam && !maxParam && !exactParam && !includeNullParam) {
      continue;
    }
    
    const propertyFilter: PropertyFilter = {
      name: propName,
      min_value: minParam ? parseFloat(minParam) : null,
      max_value: maxParam ? parseFloat(maxParam) : null,
      include_null: includeNullParam === 'true'
    };
    
    // Add exact value if present
    if (exactParam) {
      // Try to parse as number first, otherwise use as string
      const numValue = parseFloat(exactParam);
      if (!isNaN(numValue)) {
        propertyFilter.exact_value = numValue;
      } else if (exactParam === 'true' || exactParam === 'false') {
        propertyFilter.exact_value = exactParam === 'true';
      } else {
        propertyFilter.exact_value = exactParam;
      }
    }
    
    // Validate numeric ranges if applicable
    if (propertyFilter.min_value !== null || propertyFilter.max_value !== null) {
      // If we have predefined ranges for this property, use them to validate
      const propertyRange = PROPERTY_RANGES[propName];
      if (propertyRange) {
        // Validate min value if present
        if (propertyFilter.min_value !== null) {
          const validation = validateNumericRange(
            propertyFilter.min_value,
            propName,
            propertyRange.min,
            propertyFilter.max_value !== null ? propertyFilter.max_value : propertyRange.max
          );
          
          if (!validation.valid) {
            propertyFilter.min_value = propertyRange.min;
          }
        }
        
        // Validate max value if present
        if (propertyFilter.max_value !== null) {
          const validation = validateNumericRange(
            propertyFilter.max_value,
            propName,
            propertyFilter.min_value !== null ? propertyFilter.min_value : propertyRange.min,
            propertyRange.max
          );
          
          if (!validation.valid) {
            propertyFilter.max_value = propertyRange.max;
          }
        }
      }
    }
    
    properties.push(propertyFilter);
  }
  
  if (properties.length > 0) {
    filters.properties = properties;
  }
  
  return filters;
}

/**
 * Updates URL search parameters with molecule filter values
 * 
 * @param searchParams Current URL search parameters
 * @param filters Molecule filter object to serialize to URL
 * @returns Updated URL search parameters
 */
function serializeFiltersToUrl(
  searchParams: URLSearchParams,
  filters: MoleculeFilter
): URLSearchParams {
  // Create a copy of the search params
  const updatedParams = new URLSearchParams(searchParams.toString());
  
  // Update search parameter
  if (filters.search) {
    updatedParams.set('search', filters.search);
  } else {
    updatedParams.delete('search');
  }
  
  // Update library_id parameter
  if (filters.library_id) {
    updatedParams.set('library_id', filters.library_id);
  } else {
    updatedParams.delete('library_id');
  }
  
  // Update status parameter
  if (filters.status) {
    if (Array.isArray(filters.status)) {
      if (filters.status.length > 0) {
        updatedParams.set('status', filters.status.join(','));
      } else {
        updatedParams.delete('status');
      }
    } else {
      updatedParams.set('status', filters.status);
    }
  } else {
    updatedParams.delete('status');
  }
  
  // Update sort parameters
  if (filters.sort_by) {
    updatedParams.set('sort_by', filters.sort_by);
    
    if (filters.sort_order) {
      updatedParams.set('sort_order', filters.sort_order);
    } else {
      updatedParams.delete('sort_order');
    }
  } else {
    updatedParams.delete('sort_by');
    updatedParams.delete('sort_order');
  }
  
  // Clear all existing property filter parameters
  for (const propName of FILTERABLE_PROPERTIES) {
    updatedParams.delete(`${propName}_min`);
    updatedParams.delete(`${propName}_max`);
    updatedParams.delete(propName);
    updatedParams.delete(`${propName}_include_null`);
  }
  
  // Add property filters
  if (filters.properties && filters.properties.length > 0) {
    for (const prop of filters.properties) {
      // Skip if property doesn't have any filter values
      if (
        prop.min_value === null && 
        prop.max_value === null && 
        prop.exact_value === undefined &&
        !prop.include_null
      ) {
        continue;
      }
      
      // Add min value if present
      if (prop.min_value !== null) {
        updatedParams.set(`${prop.name}_min`, prop.min_value.toString());
      }
      
      // Add max value if present
      if (prop.max_value !== null) {
        updatedParams.set(`${prop.name}_max`, prop.max_value.toString());
      }
      
      // Add exact value if present
      if (prop.exact_value !== undefined && prop.exact_value !== null) {
        updatedParams.set(prop.name, prop.exact_value.toString());
      }
      
      // Add include_null flag if true
      if (prop.include_null) {
        updatedParams.set(`${prop.name}_include_null`, 'true');
      }
    }
  }
  
  return updatedParams;
}

/**
 * Builds a query string for API requests based on filter parameters
 * 
 * @param filters Molecule filter object to convert to query string
 * @returns Query string for API requests
 */
function buildFilterQueryString(filters: MoleculeFilter): string {
  const params = new URLSearchParams();
  
  // Add search parameter
  if (filters.search) {
    params.set('search', filters.search);
  }
  
  // Add library_id parameter
  if (filters.library_id) {
    params.set('library_id', filters.library_id);
  }
  
  // Add status parameter
  if (filters.status) {
    if (Array.isArray(filters.status)) {
      if (filters.status.length > 0) {
        // For API requests, use repeated parameter for multiple statuses
        filters.status.forEach(status => {
          params.append('status', status);
        });
      }
    } else {
      params.set('status', filters.status);
    }
  }
  
  // Add sort parameters
  if (filters.sort_by) {
    params.set('sort_by', filters.sort_by);
    
    if (filters.sort_order) {
      params.set('sort_order', filters.sort_order);
    }
  }
  
  // Add property filters
  if (filters.properties && filters.properties.length > 0) {
    for (const prop of filters.properties) {
      // Skip if property doesn't have any filter values
      if (
        prop.min_value === null && 
        prop.max_value === null && 
        prop.exact_value === undefined &&
        !prop.include_null
      ) {
        continue;
      }
      
      // Format property filters for API compatibility
      
      // Add min value if present
      if (prop.min_value !== null) {
        params.set(`property.${prop.name}.min`, prop.min_value.toString());
      }
      
      // Add max value if present
      if (prop.max_value !== null) {
        params.set(`property.${prop.name}.max`, prop.max_value.toString());
      }
      
      // Add exact value if present
      if (prop.exact_value !== undefined && prop.exact_value !== null) {
        params.set(`property.${prop.name}.exact`, prop.exact_value.toString());
      }
      
      // Add include_null flag if true
      if (prop.include_null) {
        params.set(`property.${prop.name}.include_null`, 'true');
      }
    }
  }
  
  return params.toString();
}

/**
 * A hook that manages molecule filtering parameters and synchronizes them with URL search parameters
 * 
 * This hook provides a complete solution for managing filter state, including:
 * - Synchronizing filters with URL parameters for bookmarkable/shareable filter states
 * - Debouncing filter changes to prevent excessive URL updates
 * - Validating property filter ranges
 * - Generating query strings for API requests
 * 
 * @param initialFilters Optional default filter values
 * @returns Object containing filter state and control functions
 */
function useMoleculeFilterParams(initialFilters?: Partial<MoleculeFilter>) {
  // Get URL search parameters and navigation function
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // Parse initial filter values from URL or use provided defaults
  const parsedFilters = useMemo(
    () => parseFiltersFromUrl(searchParams, initialFilters),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [] // Only run on initial render
  );
  
  // Create state for filter parameters
  const [filters, setFiltersState] = useState<MoleculeFilter>(parsedFilters);
  
  // Create a debounced version of the filter state to prevent excessive URL updates
  const debouncedFilters = useDebounce(filters, 500);
  
  // Update URL search parameters when debounced filter state changes
  useEffect(() => {
    const updatedParams = serializeFiltersToUrl(searchParams, debouncedFilters);
    setSearchParams(updatedParams);
  }, [debouncedFilters, searchParams, setSearchParams]);
  
  // Create a memoized query string for API requests
  const filterQueryString = useMemo(
    () => buildFilterQueryString(filters),
    [filters]
  );
  
  // Define filter update functions
  
  /**
   * Updates multiple filter parameters at once
   */
  const setFilters = useCallback((newFilters: Partial<MoleculeFilter>) => {
    setFiltersState(prevFilters => ({
      ...prevFilters,
      ...newFilters
    }));
  }, []);
  
  /**
   * Updates a specific property filter
   */
  const setPropertyFilter = useCallback((
    name: string,
    min?: number | null,
    max?: number | null
  ) => {
    setFiltersState(prevFilters => {
      // Clone the current properties array
      const properties = [...(prevFilters.properties || [])];
      
      // Find existing property filter or create a new one
      const existingIndex = properties.findIndex(p => p.name === name);
      
      if (existingIndex >= 0) {
        // Update existing property filter
        const updatedProperty = {
          ...properties[existingIndex],
          min_value: min !== undefined ? min : properties[existingIndex].min_value,
          max_value: max !== undefined ? max : properties[existingIndex].max_value
        };
        
        // Check if filter now has no constraints
        if (
          updatedProperty.min_value === null && 
          updatedProperty.max_value === null && 
          updatedProperty.exact_value === undefined &&
          !updatedProperty.include_null
        ) {
          // Remove empty filter
          properties.splice(existingIndex, 1);
        } else {
          // Update filter
          properties[existingIndex] = updatedProperty;
        }
      } else if (min !== null || max !== null) {
        // Add new property filter if we have values to filter on
        properties.push({
          name,
          min_value: min || null,
          max_value: max || null,
          include_null: false
        });
      }
      
      return {
        ...prevFilters,
        properties
      };
    });
  }, []);
  
  /**
   * Updates the search term filter
   */
  const setSearchTerm = useCallback((term: string) => {
    setFiltersState(prevFilters => ({
      ...prevFilters,
      search: term || null
    }));
  }, []);
  
  /**
   * Updates the status filter
   */
  const setStatusFilter = useCallback((
    status: MoleculeStatus | MoleculeStatus[] | null
  ) => {
    setFiltersState(prevFilters => ({
      ...prevFilters,
      status
    }));
  }, []);
  
  /**
   * Updates the library filter
   */
  const setLibraryFilter = useCallback((libraryId: string | null) => {
    setFiltersState(prevFilters => ({
      ...prevFilters,
      library_id: libraryId
    }));
  }, []);
  
  /**
   * Updates the sorting parameters
   */
  const setSortBy = useCallback((
    field: string | null,
    order?: 'asc' | 'desc' | null
  ) => {
    setFiltersState(prevFilters => ({
      ...prevFilters,
      sort_by: field,
      sort_order: field ? (order || 'asc') : null
    }));
  }, []);
  
  /**
   * Resets all filters to default values
   */
  const resetFilters = useCallback(() => {
    // Create empty filter object
    const emptyFilters: MoleculeFilter = {
      search: null,
      library_id: null,
      status: null,
      properties: [],
      sort_by: null,
      sort_order: null
    };
    
    // Apply any initial filters provided to the hook
    if (initialFilters) {
      Object.assign(emptyFilters, initialFilters);
    }
    
    setFiltersState(emptyFilters);
  }, [initialFilters]);
  
  return {
    filters,
    setFilters,
    setPropertyFilter,
    setSearchTerm,
    setStatusFilter,
    setLibraryFilter,
    setSortBy,
    resetFilters,
    filterQueryString
  };
}

export default useMoleculeFilterParams;