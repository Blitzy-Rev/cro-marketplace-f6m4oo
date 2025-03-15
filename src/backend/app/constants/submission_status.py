from enum import Enum

class SubmissionStatus(Enum):
    """Enumeration of possible submission statuses throughout the CRO submission workflow."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PENDING_REVIEW = "PENDING_REVIEW"
    PRICING_PROVIDED = "PRICING_PROVIDED"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    RESULTS_UPLOADED = "RESULTS_UPLOADED"
    RESULTS_REVIEWED = "RESULTS_REVIEWED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class SubmissionAction(Enum):
    """Enumeration of possible actions that can be performed on a submission."""
    SUBMIT = "SUBMIT"
    PROVIDE_PRICING = "PROVIDE_PRICING"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    CANCEL = "CANCEL"
    START_EXPERIMENT = "START_EXPERIMENT"
    UPLOAD_RESULTS = "UPLOAD_RESULTS"
    REVIEW_RESULTS = "REVIEW_RESULTS"
    COMPLETE = "COMPLETE"

# List of submission statuses considered active (not terminal)
ACTIVE_STATUSES = [
    "DRAFT", "SUBMITTED", "PENDING_REVIEW", 
    "PRICING_PROVIDED", "APPROVED", "IN_PROGRESS"
]

# List of submission statuses considered terminal (no further actions possible)
TERMINAL_STATUSES = [
    "COMPLETED", "CANCELLED", "REJECTED"
]

# List of submission statuses where submission details can be edited
EDITABLE_STATUSES = [
    "DRAFT"
]

# Dictionary mapping current statuses to lists of valid next statuses
STATUS_TRANSITIONS = {
    "DRAFT": ["SUBMITTED", "CANCELLED"],
    "SUBMITTED": ["PENDING_REVIEW", "CANCELLED", "REJECTED"],
    "PENDING_REVIEW": ["PRICING_PROVIDED", "REJECTED", "CANCELLED"],
    "PRICING_PROVIDED": ["APPROVED", "REJECTED", "CANCELLED"],
    "APPROVED": ["IN_PROGRESS", "CANCELLED"],
    "IN_PROGRESS": ["RESULTS_UPLOADED", "CANCELLED"],
    "RESULTS_UPLOADED": ["RESULTS_REVIEWED", "CANCELLED"],
    "RESULTS_REVIEWED": ["COMPLETED", "CANCELLED"],
    "COMPLETED": [],
    "CANCELLED": [],
    "REJECTED": []
}

# List of submission statuses editable by pharmaceutical users
PHARMA_EDITABLE_STATUSES = [
    "DRAFT"
]

# List of submission statuses editable by CRO users
CRO_EDITABLE_STATUSES = [
    "PENDING_REVIEW", "PRICING_PROVIDED", "IN_PROGRESS"
]

# Dictionary mapping statuses to human-readable descriptions
STATUS_DESCRIPTIONS = {
    "DRAFT": "Initial draft state, editable by pharma user",
    "SUBMITTED": "Submitted to CRO but not yet reviewed",
    "PENDING_REVIEW": "Under review by CRO",
    "PRICING_PROVIDED": "CRO has provided pricing and timeline",
    "APPROVED": "Pharma has approved pricing and timeline",
    "IN_PROGRESS": "Experimental work in progress at CRO",
    "RESULTS_UPLOADED": "CRO has uploaded experimental results",
    "RESULTS_REVIEWED": "Pharma has reviewed experimental results",
    "COMPLETED": "Submission workflow completed successfully",
    "CANCELLED": "Submission cancelled by either party",
    "REJECTED": "Submission rejected by CRO or pharma"
}