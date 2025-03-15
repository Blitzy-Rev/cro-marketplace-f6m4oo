# -----------------------------------------------------------------------------
# VPC and Environment Variables
# -----------------------------------------------------------------------------
variable "vpc_id" {
  type        = string
  description = "ID of the VPC where security resources will be deployed"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "The environment value must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  type        = string
  description = "Name of the project for resource naming and tagging"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Additional tags to apply to security resources"
}

# -----------------------------------------------------------------------------
# Security Service Enablement
# -----------------------------------------------------------------------------
variable "enable_waf" {
  type        = bool
  default     = true
  description = "Flag to enable or disable WAF deployment"
}

variable "enable_guardduty" {
  type        = bool
  default     = true
  description = "Flag to enable or disable GuardDuty threat detection"
}

variable "enable_cloudtrail" {
  type        = bool
  default     = true
  description = "Flag to enable or disable CloudTrail audit logging"
}

variable "enable_config" {
  type        = bool
  default     = true
  description = "Flag to enable or disable AWS Config for configuration monitoring"
}

# -----------------------------------------------------------------------------
# KMS Key Configuration
# -----------------------------------------------------------------------------
variable "enable_key_rotation" {
  type        = bool
  default     = true
  description = "Flag to enable automatic KMS key rotation"
}

variable "kms_key_deletion_window" {
  type        = number
  default     = 30
  description = "Waiting period in days before KMS key deletion"
}

# -----------------------------------------------------------------------------
# Cognito Configuration
# -----------------------------------------------------------------------------
variable "cognito_user_pool_name" {
  type        = string
  default     = "molecule-platform-user-pool"
  description = "Name for the Cognito user pool for authentication"
}

variable "cognito_identity_pool_name" {
  type        = string
  default     = "molecule-platform-identity-pool"
  description = "Name for the Cognito identity pool for federated identities"
}

variable "password_policy" {
  type = object({
    minimum_length                   = number
    require_lowercase                = bool
    require_uppercase                = bool
    require_numbers                  = bool
    require_symbols                  = bool
    temporary_password_validity_days = number
  })
  
  default = {
    minimum_length                   = 12
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }
  
  description = "Configuration for Cognito user pool password policy"
}

variable "enable_mfa" {
  type        = bool
  default     = true
  description = "Flag to enable multi-factor authentication for Cognito users"
}

# -----------------------------------------------------------------------------
# OAuth and Authentication Flow
# -----------------------------------------------------------------------------
variable "callback_urls" {
  type        = list(string)
  default     = []
  description = "List of allowed callback URLs for Cognito authentication flow"
}

variable "logout_urls" {
  type        = list(string)
  default     = []
  description = "List of allowed logout URLs for Cognito authentication flow"
}

variable "allowed_oauth_flows" {
  type        = list(string)
  default     = ["code", "implicit"]
  description = "List of allowed OAuth flows for Cognito"
}

variable "allowed_oauth_scopes" {
  type        = list(string)
  default     = ["openid", "email", "profile"]
  description = "List of allowed OAuth scopes for Cognito"
}

variable "allow_unauthenticated_identities" {
  type        = bool
  default     = false
  description = "Flag to allow unauthenticated identities in Cognito identity pool"
}

# -----------------------------------------------------------------------------
# Resource Access Configuration
# -----------------------------------------------------------------------------
variable "s3_bucket_arns" {
  type        = list(string)
  default     = []
  description = "List of S3 bucket ARNs that IAM roles need access to"
}

# -----------------------------------------------------------------------------
# VPN Configuration
# -----------------------------------------------------------------------------
variable "enable_vpn" {
  type        = bool
  default     = false
  description = "Flag to enable VPN security group creation"
}

variable "vpn_cidr_blocks" {
  type        = list(string)
  default     = []
  description = "List of CIDR blocks allowed to connect via VPN"
}