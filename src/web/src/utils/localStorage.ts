/**
 * Utility functions for interacting with browser's localStorage API in a type-safe manner.
 * Provides wrapper functions for storing, retrieving, and removing data from localStorage
 * with proper error handling and type safety.
 * 
 * @version 1.0.0
 */

/**
 * Checks if localStorage is available in the current browser environment
 * 
 * This function safely detects whether localStorage is accessible, which may not be the case
 * in private browsing mode, when cookies are disabled, or in certain server-side rendering contexts.
 * 
 * @returns {boolean} True if localStorage is available, false otherwise
 */
export function isLocalStorageAvailable(): boolean {
  try {
    // Check for existence of localStorage in the window object
    return typeof window !== 'undefined' && !!window.localStorage;
  } catch (error) {
    // If accessing localStorage throws an error (e.g., disabled in browser settings)
    return false;
  }
}

/**
 * Stores a value in localStorage with the specified key
 * 
 * The function serializes the provided value to JSON before storing it,
 * allowing for storage of complex data structures like objects and arrays.
 * 
 * @param {string} key - The key to store the value under
 * @param {any} value - The value to store (will be JSON serialized)
 * @returns {boolean} True if storage was successful, false otherwise
 */
export function setItem(key: string, value: any): boolean {
  if (!isLocalStorageAvailable()) {
    console.error('localStorage is not available in this browser environment');
    return false;
  }

  try {
    // Convert value to JSON string
    const serializedValue = JSON.stringify(value);
    localStorage.setItem(key, serializedValue);
    return true;
  } catch (error) {
    // Handle potential errors: quota exceeded, invalid data, etc.
    console.error('Failed to store value in localStorage:', error);
    return false;
  }
}

/**
 * Retrieves a value from localStorage by key with type safety
 * 
 * Uses TypeScript generics to ensure type safety of the retrieved value.
 * The value is deserialized from JSON after retrieval.
 * 
 * @template T The expected type of the stored value
 * @param {string} key - The key to retrieve the value for
 * @param {T | null} defaultValue - Default value to return if key doesn't exist or on error
 * @returns {T | null} The stored value (deserialized from JSON) or defaultValue if not found/on error
 */
export function getItem<T>(key: string, defaultValue: T | null = null): T | null {
  if (!isLocalStorageAvailable()) {
    console.error('localStorage is not available in this browser environment');
    return defaultValue;
  }

  try {
    const value = localStorage.getItem(key);
    
    // If the key doesn't exist in localStorage
    if (value === null) {
      return defaultValue;
    }
    
    // Parse the JSON string
    return JSON.parse(value) as T;
  } catch (error) {
    // Handle parsing errors (e.g., invalid JSON)
    console.error('Failed to retrieve or parse value from localStorage:', error);
    return defaultValue;
  }
}

/**
 * Removes an item from localStorage by key
 * 
 * @param {string} key - The key to remove
 * @returns {boolean} True if removal was successful, false otherwise
 */
export function removeItem(key: string): boolean {
  if (!isLocalStorageAvailable()) {
    console.error('localStorage is not available in this browser environment');
    return false;
  }

  try {
    localStorage.removeItem(key);
    return true;
  } catch (error) {
    console.error('Failed to remove item from localStorage:', error);
    return false;
  }
}

/**
 * Clears all items from localStorage
 * 
 * This will remove all key-value pairs stored in localStorage.
 * Use with caution as it affects all localStorage data for the domain.
 * 
 * @returns {boolean} True if clearing was successful, false otherwise
 */
export function clear(): boolean {
  if (!isLocalStorageAvailable()) {
    console.error('localStorage is not available in this browser environment');
    return false;
  }

  try {
    localStorage.clear();
    return true;
  } catch (error) {
    console.error('Failed to clear localStorage:', error);
    return false;
  }
}