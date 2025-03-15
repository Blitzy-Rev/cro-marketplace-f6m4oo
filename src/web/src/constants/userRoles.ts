/**
 * User role constants and role hierarchy for the Molecular Data Management and CRO Integration Platform.
 * This file defines the foundation of the role-based access control (RBAC) system used throughout
 * the frontend application for authorization and permission management.
 */

// Role string constants
export const SYSTEM_ADMIN = "system_admin";
export const PHARMA_ADMIN = "pharma_admin";
export const PHARMA_SCIENTIST = "pharma_scientist";
export const CRO_ADMIN = "cro_admin";
export const CRO_TECHNICIAN = "cro_technician";
export const AUDITOR = "auditor";

// Default role for new users
export const DEFAULT_ROLE = PHARMA_SCIENTIST;

// Complete list of all available roles
export const ALL_ROLES = [
  SYSTEM_ADMIN,
  PHARMA_ADMIN,
  PHARMA_SCIENTIST,
  CRO_ADMIN,
  CRO_TECHNICIAN,
  AUDITOR
];

/**
 * Role hierarchy defining which roles have permissions over others.
 * The key represents a role, and the array value contains all roles it has permissions over.
 * For example, SYSTEM_ADMIN has permissions over all other roles.
 */
export const ROLE_HIERARCHY: Record<string, string[]> = {
  [SYSTEM_ADMIN]: [PHARMA_ADMIN, CRO_ADMIN, PHARMA_SCIENTIST, CRO_TECHNICIAN, AUDITOR],
  [PHARMA_ADMIN]: [PHARMA_SCIENTIST],
  [CRO_ADMIN]: [CRO_TECHNICIAN],
  [PHARMA_SCIENTIST]: [],
  [CRO_TECHNICIAN]: [],
  [AUDITOR]: []
};

// Role groupings for convenience and logical organization
export const PHARMA_ROLES = [PHARMA_ADMIN, PHARMA_SCIENTIST];
export const CRO_ROLES = [CRO_ADMIN, CRO_TECHNICIAN];
export const ADMIN_ROLES = [SYSTEM_ADMIN, PHARMA_ADMIN, CRO_ADMIN];

/**
 * Checks if a user role has permission based on role hierarchy.
 * A role has permission if it either matches any of the required roles or
 * if any of the required roles are subordinate to the user's role in the hierarchy.
 * 
 * @param userRole - The role of the current user
 * @param requiredRoles - One or more roles required for permission
 * @returns True if the user has permission, false otherwise
 */
export const hasRolePermission = (
  userRole: string,
  requiredRoles: string | string[]
): boolean => {
  // Convert requiredRoles to array if it's a single string
  const requiredRolesArray = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
  
  // If userRole is directly included in requiredRoles, return true immediately
  if (requiredRolesArray.includes(userRole)) {
    return true;
  }
  
  // Get subordinate roles for the user's role from hierarchy
  const subordinateRoles = ROLE_HIERARCHY[userRole] || [];
  
  // Check if any of the required roles are subordinate to the user's role
  return requiredRolesArray.some(role => subordinateRoles.includes(role));
};

/**
 * Checks if a role is an administrator role
 * 
 * @param role - The role to check
 * @returns True if the role is an admin role, false otherwise
 */
export const isAdminRole = (role: string): boolean => {
  return ADMIN_ROLES.includes(role);
};

/**
 * Checks if a role is a pharmaceutical company role
 * 
 * @param role - The role to check
 * @returns True if the role is a pharma role, false otherwise
 */
export const isPharmaRole = (role: string): boolean => {
  return PHARMA_ROLES.includes(role);
};

/**
 * Checks if a role is a CRO role
 * 
 * @param role - The role to check
 * @returns True if the role is a CRO role, false otherwise
 */
export const isCRORole = (role: string): boolean => {
  return CRO_ROLES.includes(role);
};