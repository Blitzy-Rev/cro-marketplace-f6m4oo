# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "List of CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
}

variable "availability_zones" {
  description = "List of availability zones to deploy resources across"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# DNS Configuration
variable "enable_dns_support" {
  description = "Boolean flag to enable DNS support in the VPC"
  type        = bool
  default     = true
}

variable "enable_dns_hostnames" {
  description = "Boolean flag to enable DNS hostnames in the VPC"
  type        = bool
  default     = true
}

# NAT Gateway Configuration
variable "enable_nat_gateway" {
  description = "Boolean flag to enable NAT gateways for private subnet internet access"
  type        = bool
  default     = true
}

# VPC Endpoints Configuration
variable "enable_vpc_endpoints" {
  description = "Boolean flag to enable VPC endpoints for AWS service access without internet"
  type        = bool
  default     = true
}

variable "interface_endpoints" {
  description = "List of AWS services to create interface VPC endpoints for"
  type        = list(string)
  default     = ["ecr.api", "ecr.dkr", "logs", "secretsmanager", "ssm"]
}

# Flow Logs Configuration
variable "enable_flow_logs" {
  description = "Boolean flag to enable VPC flow logs for network traffic monitoring"
  type        = bool
  default     = true
}

variable "flow_log_retention" {
  description = "Number of days to retain VPC flow logs"
  type        = number
  default     = 30
}

# General Configuration
variable "environment" {
  description = "Deployment environment for resource naming and tagging"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.value)
    error_message = "The environment value must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  description = "Name of the project for resource naming and tagging"
  type        = string
  default     = "molecule-platform"
}

variable "tags" {
  description = "Map of tags to apply to all resources created by the module"
  type        = map(string)
  default     = {}
}