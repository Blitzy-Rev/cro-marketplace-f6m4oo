# Infrastructure for Molecular Data Management and CRO Integration Platform
# AWS Provider Configuration

terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

# Primary AWS provider configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "MoleculeFlow"
      ManagedBy   = "Terraform"
      Owner       = "PharmaTech"
    }
  }
  
  # Use profile if specified, otherwise use default credentials
  profile = var.aws_profile != "" ? var.aws_profile : null
}

# Secondary AWS provider for disaster recovery
provider "aws" {
  alias  = "secondary"
  region = var.secondary_aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "MoleculeFlow"
      ManagedBy   = "Terraform"
      Owner       = "PharmaTech"
    }
  }
  
  # Use profile if specified, otherwise use default credentials
  profile = var.aws_profile != "" ? var.aws_profile : null
}

# Configure random provider for generating unique identifiers
provider "random" {}

# Configure local provider for file operations
provider "local" {}

# Configure null provider for resource dependencies
provider "null" {}