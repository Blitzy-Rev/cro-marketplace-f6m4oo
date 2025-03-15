import { AuthToken, JWTPayload } from '../types/auth.types';
import { APP_CONFIG } from '../constants/appConfig';
import { setItem, getItem, removeItem } from './localStorage';
import { handleApiError } from './errorHandler';
import jwtDecode from 'jwt-decode'; // v3.1.2

/**
 * Stores authentication token in localStorage
 * @param token - The authentication token to store
 * @returns True if token was successfully stored, false otherwise
 */
export function setAuthToken(token: AuthToken): boolean {
  try {
    // Store the token
    const tokenStored = setItem(APP_CONFIG.auth.tokenStorageKey, token);
    
    // Calculate and store token expiry time
    const expiryTime = Date.now() + token.expires_in * 1000; // Convert seconds to milliseconds
    const expiryStored = setItem(APP_CONFIG.auth.tokenExpiryStorageKey, expiryTime);
    
    return tokenStored && expiryStored;
  } catch (error) {
    handleApiError(error, false);
    return false;
  }
}

/**
 * Retrieves authentication token from localStorage
 * @returns The stored authentication token or null if not found
 */
export function getAuthToken(): AuthToken | null {
  try {
    return getItem<AuthToken>(APP_CONFIG.auth.tokenStorageKey);
  } catch (error) {
    handleApiError(error, false);
    return null;
  }
}

/**
 * Removes authentication token from localStorage
 * @returns True if token was successfully removed, false otherwise
 */
export function removeAuthToken(): boolean {
  try {
    const tokenRemoved = removeItem(APP_CONFIG.auth.tokenStorageKey);
    const expiryRemoved = removeItem(APP_CONFIG.auth.tokenExpiryStorageKey);
    
    return tokenRemoved && expiryRemoved;
  } catch (error) {
    handleApiError(error, false);
    return false;
  }
}

/**
 * Checks if the current authentication token is expired
 * @returns True if token is expired or not found, false otherwise
 */
export function isTokenExpired(): boolean {
  try {
    const expiry = getItem<number>(APP_CONFIG.auth.tokenExpiryStorageKey);
    
    // If expiry is not found, consider token as expired
    if (expiry === null) {
      return true;
    }
    
    // Check if current time is past the expiry time
    return Date.now() > expiry;
  } catch (error) {
    handleApiError(error, false);
    return true; // Consider token expired in case of error
  }
}

/**
 * Decodes JWT token to access payload data
 * @param token - JWT token string to decode
 * @returns Decoded token payload or null if decoding fails
 */
export function decodeToken(token: string): JWTPayload | null {
  try {
    return jwtDecode<JWTPayload>(token);
  } catch (error) {
    console.error('Failed to decode JWT token:', error);
    return null;
  }
}

/**
 * Extracts user role from JWT token
 * @returns User role or null if token is invalid or not found
 */
export function getUserRoleFromToken(): string | null {
  try {
    const token = getAuthToken();
    if (!token) {
      return null;
    }
    
    const decoded = decodeToken(token.access_token);
    if (!decoded) {
      return null;
    }
    
    return decoded.role;
  } catch (error) {
    handleApiError(error, false);
    return null;
  }
}

/**
 * Checks if current user has required permission based on role
 * @param requiredRoles - Single role or array of roles that have permission
 * @returns True if user has required permission, false otherwise
 */
export function hasPermission(requiredRoles: string | string[]): boolean {
  const userRole = getUserRoleFromToken();
  
  if (!userRole) {
    return false;
  }
  
  // Convert single role to array
  const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
  
  // Check if user role is included in required roles
  return roles.includes(userRole);
}

/**
 * Checks if user is currently authenticated with a valid token
 * @returns True if user is authenticated, false otherwise
 */
export function isAuthenticated(): boolean {
  const token = getAuthToken();
  return !!token && !isTokenExpired();
}