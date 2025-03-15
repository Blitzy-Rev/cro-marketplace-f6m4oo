import { useState, useEffect } from 'react'; // ^18.0.0

/**
 * A custom React hook that provides debouncing functionality for values that change rapidly,
 * such as search inputs, filter parameters, or form inputs.
 * 
 * This hook delays the update of a value until after a specified delay has passed
 * since the last change, preventing excessive operations like API calls or UI updates.
 * 
 * @template T The type of the value being debounced
 * @param value The value to debounce
 * @param delay The delay in milliseconds before updating the debounced value
 * @returns The debounced value that updates after the specified delay
 * 
 * @example
 * // Basic usage for search input
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearchTerm = useDebounce(searchTerm, 500);
 * 
 * // Effect runs only when debouncedSearchTerm changes (not on every keystroke)
 * useEffect(() => {
 *   if (debouncedSearchTerm) {
 *     searchMolecules(debouncedSearchTerm);
 *   }
 * }, [debouncedSearchTerm]);
 */
function useDebounce<T>(value: T, delay: number): T {
  // State to hold the debounced value
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Create a timeout that will update the debounced value after the specified delay
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Cleanup function that clears the timeout if the value changes
    // before the delay completes or when the component unmounts
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]); // Re-run effect when value or delay changes

  return debouncedValue;
}

export default useDebounce;