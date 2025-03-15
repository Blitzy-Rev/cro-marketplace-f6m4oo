/**
 * CRO (Contract Research Organization) Types
 * 
 * Defines TypeScript interfaces and types for Contract Research Organization (CRO) 
 * related data structures in the Molecular Data Management and CRO Integration Platform.
 * These types are used throughout the frontend application for type checking, data validation,
 * and API communication related to CRO services.
 */

/**
 * Enumeration of available CRO service types for categorization
 */
export enum ServiceType {
  BINDING_ASSAY = 'binding_assay',
  ADME = 'adme',
  SOLUBILITY = 'solubility',
  PERMEABILITY = 'permeability',
  METABOLIC_STABILITY = 'metabolic_stability',
  TOXICITY = 'toxicity',
  CUSTOM = 'custom',
}

/**
 * Base interface for CRO service data with common fields
 */
export interface CROServiceBase {
  name: string;
  description: string | null;
  provider: string;
  service_type: ServiceType;
  base_price: number;
  price_currency: string;
  typical_turnaround_days: number;
  specifications: Record<string, any> | null;
  active: boolean;
}

/**
 * Interface for creating a new CRO service
 */
export interface CROServiceCreate extends CROServiceBase {}

/**
 * Interface for updating an existing CRO service with partial data
 */
export interface CROServiceUpdate {
  name?: string;
  description?: string | null;
  provider?: string;
  service_type?: ServiceType;
  base_price?: number;
  price_currency?: string;
  typical_turnaround_days?: number;
  specifications?: Record<string, any> | null;
  active?: boolean;
}

/**
 * Interface for CRO service data with ID, timestamps, and relationship counts
 */
export interface CROService extends CROServiceBase {
  id: string;
  created_at: string;
  updated_at: string;
  submission_count: number | null;
}

/**
 * Interface for filtering CRO services in API requests
 */
export interface CROServiceFilter {
  name_contains: string | null;
  provider_contains: string | null;
  service_type: ServiceType | null;
  price_min: number | null;
  price_max: number | null;
  turnaround_max: number | null;
  active_only: boolean | null;
}

/**
 * Mapping of service types to user-friendly display names
 */
export const SERVICE_TYPE_DISPLAY_NAMES: Record<ServiceType, string> = {
  [ServiceType.BINDING_ASSAY]: 'Binding Assay',
  [ServiceType.ADME]: 'ADME Panel',
  [ServiceType.SOLUBILITY]: 'Solubility Testing',
  [ServiceType.PERMEABILITY]: 'Permeability Assay',
  [ServiceType.METABOLIC_STABILITY]: 'Metabolic Stability',
  [ServiceType.TOXICITY]: 'Toxicity Screening',
  [ServiceType.CUSTOM]: 'Custom Service',
};

/**
 * Interface for CRO service state in Redux store
 */
export interface CROServiceState {
  services: CROService[];
  selectedServices: string[];
  currentService: CROService | null;
  loading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
  pageSize: number;
  totalPages: number;
  filters: CROServiceFilter;
}

/**
 * Interface for single CRO service API response
 */
export interface CROServiceResponse {
  service: CROService;
}

/**
 * Interface for paginated CRO services API response
 */
export interface CROServicesResponse {
  items: CROService[];
  total: number;
  page: number;
  size: number;
  pages: number;
}