/**
 * TypeScript type definitions for molecule-related data structures
 * used throughout the frontend application.
 */

/**
 * Enumeration of possible molecule statuses in the workflow
 */
export enum MoleculeStatus {
  AVAILABLE = 'AVAILABLE', // Molecule is available for use
  PENDING = 'PENDING',     // Molecule is pending processing
  TESTING = 'TESTING',     // Molecule is currently in testing
  RESULTS = 'RESULTS',     // Molecule has experimental results
  ARCHIVED = 'ARCHIVED'    // Molecule is archived
}

/**
 * Enumeration of property data types for validation and display
 */
export enum PropertyType {
  STRING = 'STRING',   // String value
  NUMERIC = 'NUMERIC', // Decimal number
  INTEGER = 'INTEGER', // Integer number
  BOOLEAN = 'BOOLEAN'  // Boolean value
}

/**
 * Enumeration of property data sources for tracking data provenance
 */
export enum PropertySource {
  CALCULATED = 'CALCULATED',   // Computed from molecular structure
  IMPORTED = 'IMPORTED',       // Imported from external source
  PREDICTED = 'PREDICTED',     // Predicted by AI model
  EXPERIMENTAL = 'EXPERIMENTAL' // Measured experimentally
}

/**
 * Enumeration of property categories for organization and filtering
 */
export enum PropertyCategory {
  PHYSICAL = 'PHYSICAL',         // Physical properties
  CHEMICAL = 'CHEMICAL',         // Chemical properties
  BIOLOGICAL = 'BIOLOGICAL',     // Biological properties
  COMPUTATIONAL = 'COMPUTATIONAL', // Computational predictions
  EXPERIMENTAL = 'EXPERIMENTAL'    // Experimental results
}

/**
 * Interface for molecule property data with value and metadata
 */
export interface MoleculeProperty {
  /** Property name (e.g., 'molecular_weight', 'logp') */
  name: string;
  /** Property value */
  value: number | string | boolean | null;
  /** Units for the property value (e.g., 'g/mol', 'nM') */
  units?: string | null;
  /** Source of the property data */
  source?: PropertySource;
  /** ISO timestamp when the property was created */
  created_at?: string | null;
}

/**
 * Interface for standard property definitions with metadata
 */
export interface PropertyDefinition {
  /** Property name identifier */
  name: string;
  /** Human-readable property name */
  display_name: string;
  /** Data type of the property */
  property_type: PropertyType;
  /** Category of the property */
  category: PropertyCategory;
  /** Standard units for the property */
  units?: string | null;
  /** Minimum valid value */
  min_value?: number | null;
  /** Maximum valid value */
  max_value?: number | null;
  /** Detailed description of the property */
  description?: string | null;
  /** Whether the property is required for all molecules */
  is_required?: boolean;
  /** Whether the property can be used for filtering */
  is_filterable?: boolean;
  /** Whether the property can be predicted by AI */
  is_predictable?: boolean;
}

/**
 * Core interface for molecule data with structure and properties
 */
export interface Molecule {
  /** Unique identifier for the molecule */
  id: string;
  /** SMILES representation of the molecular structure */
  smiles: string;
  /** InChI Key for the molecule */
  inchi_key: string;
  /** Molecular formula */
  formula?: string | null;
  /** Molecular weight in g/mol */
  molecular_weight?: number | null;
  /** Current status in the workflow */
  status?: MoleculeStatus | null;
  /** Array of molecular properties */
  properties?: MoleculeProperty[] | null;
  /** Array of library IDs the molecule belongs to */
  libraries?: string[] | null;
  /** Additional metadata for the molecule */
  metadata?: Record<string, any> | null;
  /** ISO timestamp when the molecule was created */
  created_at?: string;
  /** ISO timestamp when the molecule was last updated */
  updated_at?: string;
  /** ID of the user who created the molecule */
  created_by?: string | null;
}

/**
 * Interface for creating a new molecule
 */
export interface MoleculeCreate {
  /** SMILES representation of the molecular structure */
  smiles: string;
  /** Key-value pairs of property names and values */
  properties?: Record<string, number | string | boolean> | null;
  /** ID of the library to add the molecule to */
  library_id?: string | null;
  /** Additional metadata for the molecule */
  metadata?: Record<string, any> | null;
}

/**
 * Interface for updating an existing molecule
 */
export interface MoleculeUpdate {
  /** Key-value pairs of property names and values to update */
  properties?: Record<string, number | string | boolean | null>;
  /** Updated status in the workflow */
  status?: MoleculeStatus | null;
  /** Updated metadata for the molecule */
  metadata?: Record<string, any> | null;
}

/**
 * Interface for property-based filtering
 */
export interface PropertyFilter {
  /** Property name to filter by */
  name: string;
  /** Minimum value for range filter */
  min_value?: number | null;
  /** Maximum value for range filter */
  max_value?: number | null;
  /** Exact value to match */
  exact_value?: number | string | boolean | null;
  /** Whether to include molecules with null values for this property */
  include_null?: boolean;
}

/**
 * Interface for molecule filtering criteria
 */
export interface MoleculeFilter {
  /** Text search term for molecule attributes */
  search?: string | null;
  /** Filter by library ID */
  library_id?: string | null;
  /** Filter by molecule status */
  status?: MoleculeStatus | MoleculeStatus[] | null;
  /** Array of property filters */
  properties?: PropertyFilter[];
  /** ISO timestamp to filter molecules created after this date */
  created_after?: string | null;
  /** ISO timestamp to filter molecules created before this date */
  created_before?: string | null;
  /** Filter by creator user ID */
  created_by?: string | null;
  /** Property name to sort by */
  sort_by?: string | null;
  /** Sort order (ascending or descending) */
  sort_order?: 'asc' | 'desc' | null;
}

/**
 * Interface for batch molecule creation
 */
export interface MoleculeBatchCreate {
  /** Array of molecules to create */
  molecules: MoleculeCreate[];
  /** ID of the library to add all molecules to */
  library_id?: string | null;
  /** Whether to skip molecules that already exist */
  skip_duplicates?: boolean;
}

/**
 * Interface for CSV column to property mapping
 */
export interface CSVColumnMapping {
  /** Column name in the CSV file */
  csv_column: string;
  /** Property name to map to */
  property_name: string;
  /** Whether this mapping is required */
  is_required?: boolean;
}

/**
 * Interface for CSV column to property mapping
 */
export interface MoleculeCSVMapping {
  /** Array of column to property mappings */
  column_mappings: CSVColumnMapping[];
  /** ID of the library to add imported molecules to */
  library_id?: string | null;
  /** Whether to skip the header row */
  skip_header?: boolean;
  /** Whether to skip molecules that already exist */
  skip_duplicates?: boolean;
}

/**
 * Interface for CSV processing results
 */
export interface MoleculeCSVProcessResult {
  /** Total number of rows in the CSV */
  total_rows: number;
  /** Number of rows successfully processed */
  processed_rows: number;
  /** Number of rows that failed processing */
  failed_rows: number;
  /** Number of duplicate molecules skipped */
  duplicate_rows: number;
  /** Number of new molecules created */
  created_molecules: number;
  /** Map of row numbers to error messages */
  errors?: Record<string, string[]>;
  /** ID of the background processing job */
  job_id?: string | null;
  /** Status of the CSV processing job */
  status: 'completed' | 'processing' | 'failed';
}

/**
 * Interface for AI prediction requests
 */
export interface MoleculePredictionRequest {
  /** Array of molecule IDs to predict properties for */
  molecule_ids?: string[];
  /** Array of SMILES strings to predict properties for */
  smiles?: string[];
  /** Array of property names to predict */
  properties: string[];
  /** Specific AI model version to use */
  model_version?: string | null;
  /** Minimum confidence threshold for predictions */
  confidence_threshold?: number | null;
}

/**
 * Interface for property prediction result
 */
export interface PropertyPrediction {
  /** Name of the predicted property */
  property_name: string;
  /** Predicted property value */
  value: number | string | boolean;
  /** Confidence score (0-1) for the prediction */
  confidence: number;
  /** Units for the predicted value */
  units?: string | null;
}

/**
 * Interface for AI prediction results
 */
export interface MoleculePrediction {
  /** ID of the molecule if available */
  molecule_id?: string | null;
  /** SMILES string of the molecule */
  smiles: string;
  /** Array of property predictions */
  predictions: PropertyPrediction[];
  /** AI model version used for predictions */
  model_version: string;
  /** ISO timestamp when the prediction was made */
  timestamp: string;
}

/**
 * Interface for prediction job status and results
 */
export interface PredictionJob {
  /** Unique identifier for the prediction job */
  job_id: string;
  /** Current status of the prediction job */
  status: 'pending' | 'processing' | 'completed' | 'failed';
  /** Progress percentage (0-100) */
  progress: number;
  /** ISO timestamp when the job was created */
  created_at: string;
  /** ISO timestamp when the job was last updated */
  updated_at: string;
  /** Number of molecules in the job */
  molecule_count: number;
  /** Number of properties being predicted */
  property_count: number;
  /** Prediction results if completed */
  results?: MoleculePrediction[] | null;
  /** Error message if failed */
  error?: string | null;
}