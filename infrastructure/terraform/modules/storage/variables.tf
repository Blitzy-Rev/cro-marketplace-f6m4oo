variable "document_bucket_name" {
  description = "Name for the S3 bucket that stores legal documents, specifications, and other files"
  type        = string
  default     = null
}

variable "csv_bucket_name" {
  description = "Name for the S3 bucket that stores CSV files containing molecular data"
  type        = string
  default     = null
}

variable "results_bucket_name" {
  description = "Name for the S3 bucket that stores experimental results data"
  type        = string
  default     = null
}

variable "backup_bucket_name" {
  description = "Name for the S3 bucket that stores backups with appropriate lifecycle policies"
  type        = string
  default     = null
}

variable "enable_versioning" {
  description = "Flag to enable versioning for document and results buckets"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Flag to enable server-side encryption for all S3 buckets"
  type        = bool
  default     = true
}

variable "cross_region_replication" {
  description = "Flag to enable cross-region replication for disaster recovery"
  type        = bool
  default     = false
}

variable "replication_region" {
  description = "AWS region for replication buckets if cross-region replication is enabled"
  type        = string
  default     = "us-west-2"
}

variable "document_retention_days" {
  description = "Number of days before transitioning document objects to Standard-IA storage class"
  type        = number
  default     = 90
}

variable "document_glacier_transition_days" {
  description = "Number of days before transitioning document objects to Glacier storage class"
  type        = number
  default     = 365
}

variable "csv_retention_days" {
  description = "Number of days before transitioning CSV objects to Standard-IA storage class"
  type        = number
  default     = 30
}

variable "csv_expiration_days" {
  description = "Number of days before expiring CSV objects"
  type        = number
  default     = 180
}

variable "results_retention_days" {
  description = "Number of days before transitioning results objects to Standard-IA storage class"
  type        = number
  default     = 90
}

variable "results_glacier_transition_days" {
  description = "Number of days before transitioning results objects to Glacier storage class"
  type        = number
  default     = 365
}

variable "backup_glacier_transition_days" {
  description = "Number of days before transitioning backup objects to Glacier storage class"
  type        = number
  default     = 30
}

variable "backup_expiration_days" {
  description = "Number of days before expiring backup objects"
  type        = number
  default     = 730
}

variable "lifecycle_rules" {
  description = "Custom lifecycle rules to apply to S3 buckets"
  type = list(object({
    id                                     = string
    enabled                                = bool
    prefix                                 = string
    abort_incomplete_multipart_upload_days = number
    transition = list(object({
      days          = number
      storage_class = string
    }))
    expiration = object({
      days = number
    })
  }))
  default = []
}

variable "tags" {
  description = "Tags to apply to all S3 buckets and related resources"
  type        = map(string)
  default     = {}
}

variable "project_name" {
  description = "Name of the project for resource naming and tagging"
  type        = string
  default     = "molecule-platform"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "The environment value must be one of: dev, staging, prod."
  }
}