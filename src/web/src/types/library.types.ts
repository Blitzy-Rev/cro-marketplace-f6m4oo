/**
 * TypeScript type definitions for library-related data structures in the
 * Molecular Data Management and CRO Integration Platform.
 */

import { Molecule } from './molecule.types';
import { User } from './user.types';

/**
 * Enumeration of library categories for organization
 */
export enum LibraryCategory {
  GENERAL = 'GENERAL',
  PROJECT = 'PROJECT',
  LEAD_SERIES = 'LEAD_SERIES',
  SCREENING = 'SCREENING',
  REFERENCE = 'REFERENCE',
  CUSTOM = 'CUSTOM'
}

/**
 * Base interface for library data with common fields
 */
export interface LibraryBase {
  /** Library name, must be unique per user */
  name: string;
  /** Optional description of the library content and purpose */
  description: string | null;
  /** Library category for organization */
  category: LibraryCategory | null;
  /** Whether the library is publicly viewable */
  is_public: boolean;
}

/**
 * Interface for creating a new library
 */
export interface LibraryCreate extends LibraryBase {
  /** Optional array of molecule IDs to initially add to the library */
  molecule_ids: string[] | null;
}

/**
 * Interface for updating an existing library
 */
export interface LibraryUpdate {
  /** Updated library name */
  name?: string;
  /** Updated library description */
  description?: string | null | undefined;
  /** Updated library category */
  category?: LibraryCategory | null | undefined;
  /** Updated public visibility setting */
  is_public?: boolean;
}

/**
 * Interface for library data with ID, timestamps, and metadata
 */
export interface Library extends LibraryBase {
  /** Unique identifier for the library */
  id: string;
  /** ID of the user who owns the library */
  owner_id: string;
  /** Number of molecules in the library */
  molecule_count: number;
  /** ISO timestamp when the library was created */
  created_at: string;
  /** ISO timestamp when the library was last updated */
  updated_at: string;
}

/**
 * Interface for library data with included molecule details
 */
export interface LibraryWithMolecules extends Library {
  /** Array of molecules in the library */
  molecules: Molecule[];
}

/**
 * Interface for filtering libraries based on criteria
 */
export interface LibraryFilter {
  /** Filter by library name (partial match) */
  name: string | null;
  /** Filter by library category */
  category: LibraryCategory | null;
  /** Filter by library owner */
  owner_id: string | null;
  /** Filter by public visibility */
  is_public: boolean | null;
  /** Filter libraries containing a specific molecule */
  contains_molecule_id: string | null;
}

/**
 * Interface for adding or removing molecules from a library
 */
export interface MoleculeAddRemove {
  /** Array of molecule IDs to add or remove */
  molecule_ids: string[];
}

/**
 * Interface for paginated library response from API
 */
export interface LibraryResponse {
  /** Array of library objects */
  items: Library[];
  /** Total number of libraries matching the filter criteria */
  total: number;
  /** Current page number */
  page: number;
  /** Number of items per page */
  limit: number;
}

/**
 * Interface for library state in Redux store
 */
export interface LibraryState {
  /** Array of libraries */
  libraries: Library[];
  /** Currently selected library with molecules */
  currentLibrary: LibraryWithMolecules | null;
  /** Loading state indicator */
  loading: boolean;
  /** Error message if present */
  error: string | null;
  /** Total count of libraries */
  totalCount: number;
  /** Current page number */
  currentPage: number;
  /** Number of items per page */
  pageSize: number;
  /** Total number of pages */
  totalPages: number;
}

/**
 * Enumeration of access levels for library permissions
 */
export enum LibraryAccessLevel {
  OWNER = 'OWNER',
  EDITOR = 'EDITOR',
  VIEWER = 'VIEWER',
  NONE = 'NONE'
}

/**
 * Interface for library sharing permissions
 */
export interface LibraryShare {
  /** ID of the library being shared */
  library_id: string;
  /** ID of the user the library is shared with */
  user_id: string;
  /** Access level granted to the user */
  access_level: LibraryAccessLevel;
}

/**
 * Interface for creating library sharing permissions
 */
export interface LibraryShareCreate {
  /** ID of the user to share with */
  user_id: string;
  /** Access level to grant */
  access_level: LibraryAccessLevel;
}

/**
 * Interface for updating library sharing permissions
 */
export interface LibraryShareUpdate {
  /** Updated access level */
  access_level: LibraryAccessLevel;
}