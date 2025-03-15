/**
 * API client module for user-related operations in the Molecular Data Management and CRO Integration Platform.
 * This file provides functions to interact with the backend user management endpoints for retrieving,
 * creating, updating, and deleting users, as well as managing the current user's profile and password.
 */

import { get, post, put, patch, delete } from './apiClient';
import { API_ENDPOINTS } from '../constants/apiEndpoints';
import { User, UserCreate, UserUpdate, UserListParams, UserListResponse, PasswordChange, UserProfile } from '../types/user.types';

/**
 * Retrieves a paginated list of users with optional filtering
 * @param params - Query parameters for filtering and pagination
 * @returns Promise resolving to paginated user list response
 */
export async function getUsers(params: UserListParams): Promise<UserListResponse> {
  // Construct query parameters
  const queryParams = new URLSearchParams();
  if (params.skip !== undefined) queryParams.append('skip', params.skip.toString());
  if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
  if (params.role) queryParams.append('role', params.role);
  if (params.organization_id) queryParams.append('organization_id', params.organization_id);
  if (params.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());
  if (params.search) queryParams.append('search', params.search);

  const url = `${API_ENDPOINTS.USERS.LIST}?${queryParams.toString()}`;
  return get<UserListResponse>(url);
}

/**
 * Retrieves a specific user by ID
 * @param userId - ID of the user to retrieve
 * @returns Promise resolving to user data
 */
export async function getUser(userId: string): Promise<User> {
  const url = API_ENDPOINTS.USERS.GET.replace('{id}', userId);
  return get<User>(url);
}

/**
 * Creates a new user with the provided data
 * @param userData - Data for the new user
 * @returns Promise resolving to the created user data
 */
export async function createUser(userData: UserCreate): Promise<User> {
  return post<User>(API_ENDPOINTS.USERS.CREATE, userData);
}

/**
 * Updates an existing user with the provided data
 * @param userId - ID of the user to update
 * @param userData - Updated user data
 * @returns Promise resolving to the updated user data
 */
export async function updateUser(userId: string, userData: UserUpdate): Promise<User> {
  const url = API_ENDPOINTS.USERS.UPDATE.replace('{id}', userId);
  return put<User>(url, userData);
}

/**
 * Deletes a user by ID
 * @param userId - ID of the user to delete
 * @returns Promise resolving when the user is deleted
 */
export async function deleteUser(userId: string): Promise<void> {
  const url = API_ENDPOINTS.USERS.DELETE.replace('{id}', userId);
  return delete<void>(url);
}

/**
 * Retrieves the current authenticated user's profile
 * @returns Promise resolving to the current user's profile
 */
export async function getCurrentUser(): Promise<UserProfile> {
  return get<UserProfile>(API_ENDPOINTS.USERS.ME);
}

/**
 * Updates the current authenticated user's profile
 * @param userData - Updated user data
 * @returns Promise resolving to the updated user profile
 */
export async function updateCurrentUser(userData: UserUpdate): Promise<UserProfile> {
  return patch<UserProfile>(API_ENDPOINTS.USERS.UPDATE_PROFILE, userData);
}

/**
 * Changes the current authenticated user's password
 * @param passwordData - Password change data
 * @returns Promise resolving when the password is changed
 */
export async function changePassword(passwordData: PasswordChange): Promise<void> {
  return post<void>(API_ENDPOINTS.USERS.CHANGE_PASSWORD, passwordData);
}