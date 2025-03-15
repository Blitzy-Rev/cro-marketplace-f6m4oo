/**
 * TypeScript type definitions for user-related data structures in the
 * Molecular Data Management and CRO Integration Platform.
 * 
 * This file defines interfaces for user data, user creation, user updates,
 * and user listing that are used throughout the frontend application.
 */

import {
  SYSTEM_ADMIN,
  PHARMA_ADMIN,
  PHARMA_SCIENTIST,
  CRO_ADMIN,
  CRO_TECHNICIAN,
  AUDITOR,
  ALL_ROLES
} from '../constants/userRoles';

/**
 * Union type of all possible user roles in the system.
 * Ensures type safety when working with roles.
 */
export type UserRole = typeof SYSTEM_ADMIN | 
  typeof PHARMA_ADMIN | 
  typeof PHARMA_SCIENTIST | 
  typeof CRO_ADMIN | 
  typeof CRO_TECHNICIAN | 
  typeof AUDITOR;

/**
 * Interface representing a user in the system.
 * Contains all user attributes from the backend User entity.
 */
export interface User {
  /** Unique identifier for the user */
  id: string;
  /** User's email address, used for login */
  email: string;
  /** User's full name */
  full_name: string;
  /** User's role in the system, determines permissions */
  role: UserRole;
  /** Whether the user account is active */
  is_active: boolean;
  /** Whether the user has superuser privileges */
  is_superuser: boolean;
  /** Name of the organization the user belongs to */
  organization_name: string | null;
  /** ID of the organization the user belongs to */
  organization_id: string | null;
  /** Timestamp of the user's last login */
  last_login: string | null;
  /** Timestamp when the user was created */
  created_at: string;
  /** Timestamp when the user was last updated */
  updated_at: string;
}

/**
 * Extended user interface with permissions for authorization.
 * Includes a record of permissions available to the user.
 */
export interface UserWithPermissions extends User {
  /** Map of permission names to boolean values indicating if the user has that permission */
  permissions: Record<string, boolean>;
}

/**
 * Interface for user creation request data.
 * Contains required fields to create a new user in the system.
 */
export interface UserCreate {
  /** User's email address */
  email: string;
  /** User's full name */
  full_name: string;
  /** User's initial password */
  password: string;
  /** User's role in the system */
  role: UserRole;
  /** Name of the organization the user belongs to (optional) */
  organization_name: string | null;
  /** ID of the organization the user belongs to (optional) */
  organization_id: string | null;
}

/**
 * Interface for user update request data with optional fields.
 * Any field can be undefined to indicate it should not be updated.
 */
export interface UserUpdate {
  /** User's full name */
  full_name?: string;
  /** User's password */
  password?: string;
  /** User's role in the system */
  role?: UserRole;
  /** Name of the organization the user belongs to */
  organization_name?: string | null;
  /** ID of the organization the user belongs to */
  organization_id?: string | null;
  /** Whether the user account is active */
  is_active?: boolean;
}

/**
 * Interface for password change request data.
 * Used when a user wants to change their own password.
 */
export interface PasswordChange {
  /** User's current password for verification */
  current_password: string;
  /** User's new password */
  new_password: string;
}

/**
 * Interface for user listing query parameters.
 * Used for filtering and pagination in user listing API requests.
 */
export interface UserListParams {
  /** Number of items to skip (for pagination) */
  skip: number;
  /** Maximum number of items to return (for pagination) */
  limit: number;
  /** Filter users by role */
  role?: UserRole;
  /** Filter users by organization ID */
  organization_id?: string;
  /** Filter users by active status */
  is_active?: boolean;
  /** Search term to filter users by name or email */
  search?: string;
}

/**
 * Interface for paginated user listing response.
 * Contains an array of users and pagination metadata.
 */
export interface UserListResponse {
  /** Array of user objects */
  items: User[];
  /** Total number of users matching the filter criteria */
  total: number;
  /** Number of items skipped (from request) */
  skip: number;
  /** Maximum number of items returned (from request) */
  limit: number;
}

/**
 * Interface for user profile data with limited information.
 * Used when displaying user's own profile information.
 */
export interface UserProfile {
  /** Unique identifier for the user */
  id: string;
  /** User's email address */
  email: string;
  /** User's full name */
  full_name: string;
  /** User's role in the system */
  role: UserRole;
  /** Name of the organization the user belongs to */
  organization_name: string | null;
  /** Timestamp of the user's last login */
  last_login: string | null;
  /** Timestamp when the user was created */
  created_at: string;
}