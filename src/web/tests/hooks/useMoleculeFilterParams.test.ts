import React from 'react';
import { renderHook, act } from '@testing-library/react-hooks';

import useMoleculeFilterParams from '../../src/hooks/useMoleculeFilterParams';
import { MoleculeFilter, MoleculeStatus } from '../../src/types/molecule.types';
import { FILTERABLE_PROPERTIES } from '../../src/constants/moleculeProperties';

// Mock functions for react-router-dom hooks
function mockUseSearchParams() {
  const searchParams = new URLSearchParams();
  const setSearchParams = jest.fn();
  return [searchParams, setSearchParams];
}

function mockUseNavigate() {
  return jest.fn();
}

// Mock dependencies
jest.mock('react-router-dom', () => ({
  useSearchParams: jest.fn(),
  useNavigate: jest.fn()
}));

// Mock useDebounce to avoid dealing with timers
jest.mock('../../src/hooks/useDebounce', () => ({
  __esModule: true,
  default: (value: any) => value // Return value immediately without debouncing
}));

describe('useMoleculeFilterParams', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup mocks
    const { useSearchParams, useNavigate } = require('react-router-dom');
    useSearchParams.mockImplementation(mockUseSearchParams);
    useNavigate.mockImplementation(mockUseNavigate);
  });

  test('should initialize with default filters', () => {
    // Arrange & Act
    const { result } = renderHook(() => useMoleculeFilterParams());
    
    // Assert
    expect(result.current.filters).toEqual({
      search: null,
      library_id: null,
      status: null,
      properties: [],
      sort_by: null,
      sort_order: null
    });
  });

  test('should initialize from URL parameters', () => {
    // Arrange
    const mockParams = new URLSearchParams();
    mockParams.set('search', 'test molecule');
    mockParams.set('library_id', '123');
    mockParams.set('status', 'AVAILABLE');
    mockParams.set('sort_by', 'molecular_weight');
    mockParams.set('sort_order', 'asc');
    mockParams.set('logp_min', '1.5');
    mockParams.set('logp_max', '5.0');
    
    const { useSearchParams } = require('react-router-dom');
    useSearchParams.mockImplementation(() => [mockParams, jest.fn()]);
    
    // Act
    const { result } = renderHook(() => useMoleculeFilterParams());
    
    // Assert
    expect(result.current.filters).toEqual({
      search: 'test molecule',
      library_id: '123',
      status: 'AVAILABLE',
      properties: [
        expect.objectContaining({
          name: 'logp',
          min_value: 1.5,
          max_value: 5.0
        })
      ],
      sort_by: 'molecular_weight',
      sort_order: 'asc'
    });
  });

  test('should update URL when filters change', () => {
    // Arrange
    const setSearchParamsMock = jest.fn();
    const { useSearchParams } = require('react-router-dom');
    useSearchParams.mockImplementation(() => [new URLSearchParams(), setSearchParamsMock]);
    
    // Act
    const { result } = renderHook(() => useMoleculeFilterParams());
    
    act(() => {
      result.current.setFilters({
        search: 'test update',
        status: MoleculeStatus.TESTING
      });
    });
    
    // Assert
    expect(setSearchParamsMock).toHaveBeenCalled();
  });

  test('should update property filters correctly', () => {
    // Arrange
    const { result } = renderHook(() => useMoleculeFilterParams());
    
    // Act & Assert - Add new property filter
    act(() => {
      result.current.setPropertyFilter('logp', 2.0, 4.5);
    });
    
    expect(result.current.filters.properties).toEqual([
      expect.objectContaining({
        name: 'logp',
        min_value: 2.0,
        max_value: 4.5
      })
    ]);
    
    // Act & Assert - Update existing property filter
    act(() => {
      result.current.setPropertyFilter('logp', 1.5, null);
    });
    
    expect(result.current.filters.properties).toEqual([
      expect.objectContaining({
        name: 'logp',
        min_value: 1.5,
        max_value: null
      })
    ]);
    
    // Act & Assert - Add another property filter
    act(() => {
      result.current.setPropertyFilter('molecular_weight', 200, 500);
    });
    
    expect(result.current.filters.properties).toHaveLength(2);
    expect(result.current.filters.properties[1]).toEqual(
      expect.objectContaining({
        name: 'molecular_weight',
        min_value: 200,
        max_value: 500
      })
    );
    
    // Act & Assert - Remove property filter when both min and max are null
    act(() => {
      result.current.setPropertyFilter('logp', null, null);
    });
    
    expect(result.current.filters.properties).toHaveLength(1);
    expect(result.current.filters.properties[0].name).toBe('molecular_weight');
  });

  test('should update search term correctly', () => {
    // Arrange
    const { result } = renderHook(() => useMoleculeFilterParams());
    
    // Act & Assert
    act(() => {
      result.current.setSearchTerm('benzene');
    });
    
    expect(result.current.filters.search).toBe('benzene');
    
    // Act & Assert - Empty search term should be null
    act(() => {
      result.current.setSearchTerm('');
    });
    
    expect(result.current.filters.search).toBeNull();
  });

  test('should update status filter correctly', () => {
    // Arrange
    const { result } = renderHook(() => useMoleculeFilterParams());
    
    // Act & Assert - Single status
    act(() => {
      result.current.setStatusFilter(MoleculeStatus.AVAILABLE);
    });
    
    expect(result.current.filters.status).toBe(MoleculeStatus.AVAILABLE);
    
    // Act & Assert - Multiple statuses
    act(() => {
      result.current.setStatusFilter([MoleculeStatus.AVAILABLE, MoleculeStatus.TESTING]);
    });
    
    expect(result.current.filters.status).toEqual([MoleculeStatus.AVAILABLE, MoleculeStatus.TESTING]);
    
    // Act & Assert - Null status
    act(() => {
      result.current.setStatusFilter(null);
    });
    
    expect(result.current.filters.status).toBeNull();
  });

  test('should update library filter correctly', () => {
    // Arrange
    const { result } = renderHook(() => useMoleculeFilterParams());
    
    // Act & Assert
    act(() => {
      result.current.setLibraryFilter('lib-123');
    });
    
    expect(result.current.filters.library_id).toBe('lib-123');
    
    // Act & Assert - Null library ID
    act(() => {
      result.current.setLibraryFilter(null);
    });
    
    expect(result.current.filters.library_id).toBeNull();
  });

  test('should update sort parameters correctly', () => {
    // Arrange
    const { result } = renderHook(() => useMoleculeFilterParams());
    
    // Act & Assert - Default to ascending order
    act(() => {
      result.current.setSortBy('molecular_weight');
    });
    
    expect(result.current.filters.sort_by).toBe('molecular_weight');
    expect(result.current.filters.sort_order).toBe('asc');
    
    // Act & Assert - Specified order
    act(() => {
      result.current.setSortBy('logp', 'desc');
    });
    
    expect(result.current.filters.sort_by).toBe('logp');
    expect(result.current.filters.sort_order).toBe('desc');
    
    // Act & Assert - Null field clears both parameters
    act(() => {
      result.current.setSortBy(null);
    });
    
    expect(result.current.filters.sort_by).toBeNull();
    expect(result.current.filters.sort_order).toBeNull();
  });

  test('should reset filters correctly', () => {
    // Arrange
    const { result } = renderHook(() => useMoleculeFilterParams());
    
    // Act - Set multiple filters
    act(() => {
      result.current.setSearchTerm('test');
      result.current.setLibraryFilter('lib-123');
      result.current.setStatusFilter(MoleculeStatus.TESTING);
      result.current.setPropertyFilter('logp', 1.0, 5.0);
      result.current.setSortBy('molecular_weight', 'desc');
    });
    
    // Act - Reset all filters
    act(() => {
      result.current.resetFilters();
    });
    
    // Assert
    expect(result.current.filters).toEqual({
      search: null,
      library_id: null,
      status: null,
      properties: [],
      sort_by: null,
      sort_order: null
    });
  });

  test('should generate correct filter query string', () => {
    // Arrange
    const { result } = renderHook(() => useMoleculeFilterParams());
    
    // Act - Set multiple filters
    act(() => {
      result.current.setSearchTerm('test');
      result.current.setLibraryFilter('lib-123');
      result.current.setStatusFilter(MoleculeStatus.TESTING);
      result.current.setPropertyFilter('logp', 1.0, 5.0);
      result.current.setSortBy('molecular_weight', 'desc');
    });
    
    // Assert
    const queryString = result.current.filterQueryString;
    expect(queryString).toContain('search=test');
    expect(queryString).toContain('library_id=lib-123');
    expect(queryString).toContain('status=TESTING');
    expect(queryString).toContain('sort_by=molecular_weight');
    expect(queryString).toContain('sort_order=desc');
    expect(queryString).toContain('property.logp.min=1');
    expect(queryString).toContain('property.logp.max=5');
  });

  test('should debounce URL updates', () => {
    // Arrange
    jest.useFakeTimers();
    
    // Restore real implementation of useDebounce for this test
    jest.unmock('../../src/hooks/useDebounce');
    const originalDebounce = jest.requireActual('../../src/hooks/useDebounce').default;
    jest.mock('../../src/hooks/useDebounce', () => ({
      __esModule: true,
      default: originalDebounce
    }));
    
    const setSearchParamsMock = jest.fn();
    const { useSearchParams } = require('react-router-dom');
    useSearchParams.mockImplementation(() => [new URLSearchParams(), setSearchParamsMock]);
    
    // Act
    const { result } = renderHook(() => useMoleculeFilterParams());
    
    // Make multiple rapid filter changes
    act(() => {
      result.current.setSearchTerm('t');
      result.current.setSearchTerm('te');
      result.current.setSearchTerm('tes');
      result.current.setSearchTerm('test');
    });
    
    // Assert - Before debounce timeout, no URL updates
    expect(setSearchParamsMock).not.toHaveBeenCalled();
    
    // Fast-forward timers
    act(() => {
      jest.runAllTimers();
    });
    
    // Should have been called with the final value
    expect(setSearchParamsMock).toHaveBeenCalledTimes(1);
    
    // Cleanup
    jest.useRealTimers();
    jest.resetModules();
  });
});