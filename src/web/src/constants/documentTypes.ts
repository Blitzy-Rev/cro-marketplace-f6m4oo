/**
 * Constants and utilities for document types in the Molecular Data Management and CRO Integration Platform
 * These definitions ensure consistency with backend document type definitions and provide
 * frontend-specific utilities for document management.
 */

/**
 * Enum of document types used throughout the system
 */
export enum DocumentType {
  MATERIAL_TRANSFER_AGREEMENT = 'MATERIAL_TRANSFER_AGREEMENT',
  NON_DISCLOSURE_AGREEMENT = 'NON_DISCLOSURE_AGREEMENT',
  EXPERIMENT_SPECIFICATION = 'EXPERIMENT_SPECIFICATION',
  SERVICE_AGREEMENT = 'SERVICE_AGREEMENT',
  RESULTS_REPORT = 'RESULTS_REPORT',
  QUALITY_CONTROL = 'QUALITY_CONTROL',
  ADDITIONAL_INSTRUCTIONS = 'ADDITIONAL_INSTRUCTIONS',
  SAFETY_DATA_SHEET = 'SAFETY_DATA_SHEET',
}

/**
 * Possible document status values
 */
export const DOCUMENT_STATUS = {
  DRAFT: 'DRAFT',
  PENDING_SIGNATURE: 'PENDING_SIGNATURE',
  SIGNED: 'SIGNED',
  REJECTED: 'REJECTED',
  EXPIRED: 'EXPIRED',
  ARCHIVED: 'ARCHIVED',
};

/**
 * Document types that require electronic signatures
 * Used to determine document workflow and UI presentation
 */
export const SIGNATURE_REQUIRED_TYPES: DocumentType[] = [
  DocumentType.MATERIAL_TRANSFER_AGREEMENT,
  DocumentType.NON_DISCLOSURE_AGREEMENT,
  DocumentType.SERVICE_AGREEMENT,
];

/**
 * Human-readable descriptions for each document type
 * Used for UI display and tooltips
 */
export const DOCUMENT_TYPE_DESCRIPTIONS: Record<DocumentType, string> = {
  [DocumentType.MATERIAL_TRANSFER_AGREEMENT]: 'Material Transfer Agreement - Legal document outlining terms for transferring materials between organizations',
  [DocumentType.NON_DISCLOSURE_AGREEMENT]: 'Non-Disclosure Agreement - Confidentiality agreement to protect proprietary information',
  [DocumentType.EXPERIMENT_SPECIFICATION]: 'Experiment Specification - Detailed protocol and requirements for experimental testing',
  [DocumentType.SERVICE_AGREEMENT]: 'Service Agreement - Contract outlining the terms of service between parties',
  [DocumentType.RESULTS_REPORT]: 'Results Report - Documentation of experimental results and findings',
  [DocumentType.QUALITY_CONTROL]: 'Quality Control - Documentation verifying quality control procedures were followed',
  [DocumentType.ADDITIONAL_INSTRUCTIONS]: 'Additional Instructions - Supplementary guidance for experiments or handling',
  [DocumentType.SAFETY_DATA_SHEET]: 'Safety Data Sheet - Information regarding safe handling of compounds',
};

/**
 * Required document types for different CRO services
 * Maps each service type to the document types required for that service
 */
export const REQUIRED_DOCUMENT_TYPES: Record<string, DocumentType[]> = {
  'Binding Assay': [
    DocumentType.MATERIAL_TRANSFER_AGREEMENT,
    DocumentType.NON_DISCLOSURE_AGREEMENT,
    DocumentType.EXPERIMENT_SPECIFICATION,
  ],
  'ADME Panel': [
    DocumentType.MATERIAL_TRANSFER_AGREEMENT,
    DocumentType.NON_DISCLOSURE_AGREEMENT,
    DocumentType.EXPERIMENT_SPECIFICATION,
    DocumentType.SAFETY_DATA_SHEET,
  ],
  'Toxicity Screening': [
    DocumentType.MATERIAL_TRANSFER_AGREEMENT,
    DocumentType.NON_DISCLOSURE_AGREEMENT,
    DocumentType.EXPERIMENT_SPECIFICATION,
    DocumentType.SAFETY_DATA_SHEET,
  ],
  'Solubility Testing': [
    DocumentType.MATERIAL_TRANSFER_AGREEMENT,
    DocumentType.NON_DISCLOSURE_AGREEMENT,
    DocumentType.EXPERIMENT_SPECIFICATION,
  ],
  'Permeability Assay': [
    DocumentType.MATERIAL_TRANSFER_AGREEMENT,
    DocumentType.NON_DISCLOSURE_AGREEMENT,
    DocumentType.EXPERIMENT_SPECIFICATION,
  ],
  'Metabolic Stability': [
    DocumentType.MATERIAL_TRANSFER_AGREEMENT,
    DocumentType.NON_DISCLOSURE_AGREEMENT,
    DocumentType.EXPERIMENT_SPECIFICATION,
    DocumentType.SAFETY_DATA_SHEET,
  ],
  'Custom Service': [
    DocumentType.MATERIAL_TRANSFER_AGREEMENT,
    DocumentType.NON_DISCLOSURE_AGREEMENT,
    DocumentType.SERVICE_AGREEMENT,
    DocumentType.EXPERIMENT_SPECIFICATION,
  ],
};

/**
 * Interface for document type information
 */
interface DocumentTypeInfo {
  type: DocumentType;
  description: string;
  required: boolean;
  signature_required: boolean;
}

/**
 * Returns detailed information about a document type
 * @param type The document type to get information for
 * @param serviceType Optional service type to determine if document is required
 * @returns Object containing document type information
 */
export const getDocumentTypeInfo = (
  type: DocumentType,
  serviceType: string | null = null
): DocumentTypeInfo => {
  const description = DOCUMENT_TYPE_DESCRIPTIONS[type];
  const signature_required = SIGNATURE_REQUIRED_TYPES.includes(type);
  let required = false;

  if (serviceType && REQUIRED_DOCUMENT_TYPES[serviceType]) {
    required = REQUIRED_DOCUMENT_TYPES[serviceType].includes(type);
  }

  return {
    type,
    description,
    required,
    signature_required,
  };
};

/**
 * Checks if a document type requires signature
 * @param type The document type to check
 * @returns True if signature is required, false otherwise
 */
export const isSignatureRequired = (type: DocumentType): boolean => {
  return SIGNATURE_REQUIRED_TYPES.includes(type);
};