from enum import Enum, auto

class DocumentType(Enum):
    """Enumeration of document types used in the system"""
    MATERIAL_TRANSFER_AGREEMENT = auto()
    NON_DISCLOSURE_AGREEMENT = auto()
    EXPERIMENT_SPECIFICATION = auto()
    SERVICE_AGREEMENT = auto()
    RESULTS_REPORT = auto()
    QUALITY_CONTROL = auto()
    ADDITIONAL_INSTRUCTIONS = auto()
    SAFETY_DATA_SHEET = auto()

# Dictionary of possible document statuses
DOCUMENT_STATUS = {
    "DRAFT": "Document is in draft state",
    "PENDING_SIGNATURE": "Document is awaiting signatures",
    "SIGNED": "Document has been signed by all parties",
    "REJECTED": "Document has been rejected",
    "EXPIRED": "Document has expired",
    "ARCHIVED": "Document has been archived"
}

# List of document types that require signatures
SIGNATURE_REQUIRED_TYPES = [
    DocumentType.MATERIAL_TRANSFER_AGREEMENT,
    DocumentType.NON_DISCLOSURE_AGREEMENT,
    DocumentType.SERVICE_AGREEMENT
]

# Human-readable descriptions for each document type
DOCUMENT_TYPE_DESCRIPTIONS = {
    DocumentType.MATERIAL_TRANSFER_AGREEMENT: "Legal agreement governing the transfer of materials between organizations",
    DocumentType.NON_DISCLOSURE_AGREEMENT: "Confidentiality agreement to protect proprietary information",
    DocumentType.EXPERIMENT_SPECIFICATION: "Detailed specifications for the experimental work to be conducted",
    DocumentType.SERVICE_AGREEMENT: "Contract outlining the services to be provided and terms of service",
    DocumentType.RESULTS_REPORT: "Report containing experimental results and analysis",
    DocumentType.QUALITY_CONTROL: "Documentation of quality control procedures and results",
    DocumentType.ADDITIONAL_INSTRUCTIONS: "Supplementary instructions for experimental work",
    DocumentType.SAFETY_DATA_SHEET: "Information about potential hazards and safe handling procedures"
}

# Mapping of required document types for different CRO services
REQUIRED_DOCUMENT_TYPES = {
    "BINDING_ASSAY": [
        DocumentType.MATERIAL_TRANSFER_AGREEMENT,
        DocumentType.NON_DISCLOSURE_AGREEMENT,
        DocumentType.EXPERIMENT_SPECIFICATION
    ],
    "ADME_PANEL": [
        DocumentType.MATERIAL_TRANSFER_AGREEMENT,
        DocumentType.NON_DISCLOSURE_AGREEMENT,
        DocumentType.EXPERIMENT_SPECIFICATION,
        DocumentType.SAFETY_DATA_SHEET
    ],
    "TOXICITY_SCREENING": [
        DocumentType.MATERIAL_TRANSFER_AGREEMENT,
        DocumentType.NON_DISCLOSURE_AGREEMENT,
        DocumentType.EXPERIMENT_SPECIFICATION,
        DocumentType.SAFETY_DATA_SHEET
    ],
    "SOLUBILITY_TESTING": [
        DocumentType.MATERIAL_TRANSFER_AGREEMENT,
        DocumentType.NON_DISCLOSURE_AGREEMENT,
        DocumentType.EXPERIMENT_SPECIFICATION
    ],
    "METABOLIC_STABILITY": [
        DocumentType.MATERIAL_TRANSFER_AGREEMENT,
        DocumentType.NON_DISCLOSURE_AGREEMENT,
        DocumentType.EXPERIMENT_SPECIFICATION
    ],
    "PERMEABILITY_ASSAY": [
        DocumentType.MATERIAL_TRANSFER_AGREEMENT,
        DocumentType.NON_DISCLOSURE_AGREEMENT,
        DocumentType.EXPERIMENT_SPECIFICATION
    ]
}