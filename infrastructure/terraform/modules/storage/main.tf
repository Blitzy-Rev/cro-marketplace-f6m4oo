# AWS S3 storage module for the Molecular Data Management and CRO Integration Platform
# Provisions and configures S3 buckets for document storage, CSV uploads, experimental results, and backups

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# Local variables for bucket naming and common tags
locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
    Application = "MoleculeFlow"
  }
  
  # Generate bucket names with environment and project info for uniqueness
  document_bucket_name = var.document_bucket_name != "" ? var.document_bucket_name : "${var.project}-${var.environment}-document-${random_string.bucket_suffix.result}"
  csv_bucket_name      = var.csv_bucket_name != "" ? var.csv_bucket_name : "${var.project}-${var.environment}-csv-${random_string.bucket_suffix.result}"
  results_bucket_name  = var.results_bucket_name != "" ? var.results_bucket_name : "${var.project}-${var.environment}-results-${random_string.bucket_suffix.result}"
  backup_bucket_name   = var.backup_bucket_name != "" ? var.backup_bucket_name : "${var.project}-${var.environment}-backup-${random_string.bucket_suffix.result}"
  
  # For replication bucket names
  document_replication_bucket_name = "${local.document_bucket_name}-replication"
  results_replication_bucket_name  = "${local.results_bucket_name}-replication"
}

# Random suffix for bucket names to ensure global uniqueness
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

#------------------------------------------------------------------------------
# S3 Bucket Resources
#------------------------------------------------------------------------------

# Document Storage Bucket - for legal documents, specifications, and other files
resource "aws_s3_bucket" "document_storage" {
  bucket = local.document_bucket_name
  tags   = merge(var.tags, local.common_tags, { 
    BucketType = "DocumentStorage",
    Description = "Legal documents, specifications, and experimental documentation"
  })
  
  # Prevent accidental bucket deletion
  force_destroy = false
}

# CSV Storage Bucket - for molecule CSV file uploads
resource "aws_s3_bucket" "csv_storage" {
  bucket = local.csv_bucket_name
  tags   = merge(var.tags, local.common_tags, { 
    BucketType = "CSVStorage",
    Description = "Temporary storage for molecule CSV file uploads"
  })
  
  # Allow destruction since this is temporary storage
  force_destroy = true
}

# Results Storage Bucket - for experimental results data
resource "aws_s3_bucket" "results_storage" {
  bucket = local.results_bucket_name
  tags   = merge(var.tags, local.common_tags, { 
    BucketType = "ResultsStorage",
    Description = "Experimental results from CROs"
  })
  
  # Prevent accidental bucket deletion
  force_destroy = false
}

# Backup Storage Bucket - for backups with lifecycle policies
resource "aws_s3_bucket" "backup_storage" {
  bucket = local.backup_bucket_name
  tags   = merge(var.tags, local.common_tags, { 
    BucketType = "BackupStorage",
    Description = "Long-term storage for system backups" 
  })
  
  # Prevent accidental bucket deletion
  force_destroy = false
}

#------------------------------------------------------------------------------
# Bucket Versioning Configuration
#------------------------------------------------------------------------------

# Document Storage Bucket Versioning - maintain version history for legal documents
resource "aws_s3_bucket_versioning" "document_storage" {
  bucket = aws_s3_bucket.document_storage.id
  
  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Results Storage Bucket Versioning - maintain version history for experimental results
resource "aws_s3_bucket_versioning" "results_storage" {
  bucket = aws_s3_bucket.results_storage.id
  
  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

#------------------------------------------------------------------------------
# Bucket Encryption Configuration
#------------------------------------------------------------------------------

# Document Storage Bucket Encryption - AES256 for all documents
resource "aws_s3_bucket_server_side_encryption_configuration" "document_storage" {
  count  = var.enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.document_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CSV Storage Bucket Encryption - AES256 for all uploaded CSVs
resource "aws_s3_bucket_server_side_encryption_configuration" "csv_storage" {
  count  = var.enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.csv_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Results Storage Bucket Encryption - AES256 for all experimental results
resource "aws_s3_bucket_server_side_encryption_configuration" "results_storage" {
  count  = var.enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.results_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Backup Storage Bucket Encryption - AES256 for all backups
resource "aws_s3_bucket_server_side_encryption_configuration" "backup_storage" {
  count  = var.enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.backup_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

#------------------------------------------------------------------------------
# Bucket Lifecycle Configuration
#------------------------------------------------------------------------------

# Document Storage Lifecycle Rules - transition to cheaper storage over time
resource "aws_s3_bucket_lifecycle_configuration" "document_storage" {
  count  = var.document_retention_days > 0 ? 1 : 0
  bucket = aws_s3_bucket.document_storage.id
  
  # Ensure versioning is configured first
  depends_on = [aws_s3_bucket_versioning.document_storage]

  # Transition documents to Standard-IA after specified days
  rule {
    id     = "document-transition"
    status = "Enabled"

    transition {
      days          = var.document_retention_days
      storage_class = "STANDARD_IA"
    }

    # Transition to Glacier for long-term retention (7 years for compliance)
    transition {
      days          = var.document_glacier_transition_days
      storage_class = "GLACIER"
    }

    # Non-current version management
    noncurrent_version_transition {
      noncurrent_days = var.document_retention_days
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = var.document_glacier_transition_days
      storage_class   = "GLACIER"
    }
  }

  # Add any custom lifecycle rules
  dynamic "rule" {
    for_each = var.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.status

      dynamic "transition" {
        for_each = rule.value.transitions != null ? rule.value.transitions : []
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      dynamic "expiration" {
        for_each = rule.value.expiration != null ? [rule.value.expiration] : []
        content {
          days = expiration.value.days
        }
      }
    }
  }
}

# CSV Storage Lifecycle Rules - temporary storage with expiration
resource "aws_s3_bucket_lifecycle_configuration" "csv_storage" {
  count  = var.csv_retention_days > 0 ? 1 : 0
  bucket = aws_s3_bucket.csv_storage.id

  # Transition CSV files to Standard-IA after specified days, then expire
  rule {
    id     = "csv-transition"
    status = "Enabled"

    transition {
      days          = var.csv_retention_days
      storage_class = "STANDARD_IA"
    }

    # Expire CSV files after specified days (usually 30-90 days)
    expiration {
      days = var.csv_expiration_days
    }
  }

  # Add any custom lifecycle rules
  dynamic "rule" {
    for_each = var.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.status

      dynamic "transition" {
        for_each = rule.value.transitions != null ? rule.value.transitions : []
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      dynamic "expiration" {
        for_each = rule.value.expiration != null ? [rule.value.expiration] : []
        content {
          days = expiration.value.days
        }
      }
    }
  }
}

# Results Storage Lifecycle Rules - transition to Glacier for long-term retention
resource "aws_s3_bucket_lifecycle_configuration" "results_storage" {
  count  = var.results_retention_days > 0 ? 1 : 0
  bucket = aws_s3_bucket.results_storage.id
  
  # Ensure versioning is configured first
  depends_on = [aws_s3_bucket_versioning.results_storage]

  # Transition results to Standard-IA after specified days
  rule {
    id     = "results-transition"
    status = "Enabled"

    transition {
      days          = var.results_retention_days
      storage_class = "STANDARD_IA"
    }

    # Transition to Glacier for long-term retention (7 years for compliance)
    transition {
      days          = var.results_glacier_transition_days
      storage_class = "GLACIER"
    }

    # Non-current version management
    noncurrent_version_transition {
      noncurrent_days = var.results_retention_days
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = var.results_glacier_transition_days
      storage_class   = "GLACIER"
    }
  }

  # Add any custom lifecycle rules
  dynamic "rule" {
    for_each = var.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.status

      dynamic "transition" {
        for_each = rule.value.transitions != null ? rule.value.transitions : []
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      dynamic "expiration" {
        for_each = rule.value.expiration != null ? [rule.value.expiration] : []
        content {
          days = expiration.value.days
        }
      }
    }
  }
}

# Backup Storage Lifecycle Rules - archive to Glacier after specified days
resource "aws_s3_bucket_lifecycle_configuration" "backup_storage" {
  count  = var.backup_glacier_transition_days > 0 ? 1 : 0
  bucket = aws_s3_bucket.backup_storage.id

  # Transition backups to Glacier after specified days
  rule {
    id     = "backup-transition"
    status = "Enabled"

    transition {
      days          = var.backup_glacier_transition_days
      storage_class = "GLACIER"
    }

    # Expire backups after specified days (usually 365 days or more)
    dynamic "expiration" {
      for_each = var.backup_expiration_days > 0 ? [1] : []
      content {
        days = var.backup_expiration_days
      }
    }
  }

  # Add any custom lifecycle rules
  dynamic "rule" {
    for_each = var.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.status

      dynamic "transition" {
        for_each = rule.value.transitions != null ? rule.value.transitions : []
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      dynamic "expiration" {
        for_each = rule.value.expiration != null ? [rule.value.expiration] : []
        content {
          days = expiration.value.days
        }
      }
    }
  }
}

#------------------------------------------------------------------------------
# Block Public Access - ensure no accidental public exposure
#------------------------------------------------------------------------------

# Block Public Access for Document Storage Bucket
resource "aws_s3_bucket_public_access_block" "document_storage" {
  bucket = aws_s3_bucket.document_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Block Public Access for CSV Storage Bucket
resource "aws_s3_bucket_public_access_block" "csv_storage" {
  bucket = aws_s3_bucket.csv_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Block Public Access for Results Storage Bucket
resource "aws_s3_bucket_public_access_block" "results_storage" {
  bucket = aws_s3_bucket.results_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Block Public Access for Backup Storage Bucket
resource "aws_s3_bucket_public_access_block" "backup_storage" {
  bucket = aws_s3_bucket.backup_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

#------------------------------------------------------------------------------
# Cross-Region Replication Configuration for Disaster Recovery
#------------------------------------------------------------------------------

# Create replication bucket for document storage in another region (DR setup)
resource "aws_s3_bucket" "document_replication" {
  count    = var.cross_region_replication ? 1 : 0
  provider = aws.replication
  bucket   = local.document_replication_bucket_name
  tags     = merge(var.tags, local.common_tags, { 
    BucketType = "DocumentReplication",
    Description = "Cross-region replication of legal documents for disaster recovery" 
  })
  
  # Prevent accidental bucket deletion
  force_destroy = false
}

# Create replication bucket for results storage in another region (DR setup)
resource "aws_s3_bucket" "results_replication" {
  count    = var.cross_region_replication ? 1 : 0
  provider = aws.replication
  bucket   = local.results_replication_bucket_name
  tags     = merge(var.tags, local.common_tags, { 
    BucketType = "ResultsReplication",
    Description = "Cross-region replication of experimental results for disaster recovery" 
  })
  
  # Prevent accidental bucket deletion
  force_destroy = false
}

# Versioning configuration for document replication bucket
resource "aws_s3_bucket_versioning" "document_replication" {
  count    = var.cross_region_replication ? 1 : 0
  provider = aws.replication
  bucket   = aws_s3_bucket.document_replication[0].id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Versioning configuration for results replication bucket
resource "aws_s3_bucket_versioning" "results_replication" {
  count    = var.cross_region_replication ? 1 : 0
  provider = aws.replication
  bucket   = aws_s3_bucket.results_replication[0].id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption for document replication bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "document_replication" {
  count    = var.cross_region_replication && var.enable_encryption ? 1 : 0
  provider = aws.replication
  bucket   = aws_s3_bucket.document_replication[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Encryption for results replication bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "results_replication" {
  count    = var.cross_region_replication && var.enable_encryption ? 1 : 0
  provider = aws.replication
  bucket   = aws_s3_bucket.results_replication[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access for document replication bucket
resource "aws_s3_bucket_public_access_block" "document_replication" {
  count    = var.cross_region_replication ? 1 : 0
  provider = aws.replication
  bucket   = aws_s3_bucket.document_replication[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Block public access for results replication bucket
resource "aws_s3_bucket_public_access_block" "results_replication" {
  count    = var.cross_region_replication ? 1 : 0
  provider = aws.replication
  bucket   = aws_s3_bucket.results_replication[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Create IAM role for S3 replication
resource "aws_iam_role" "replication" {
  count = var.cross_region_replication ? 1 : 0
  name  = "${var.project}-${var.environment}-s3-replication-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, local.common_tags)
}

# Create IAM policy for S3 replication permissions
resource "aws_iam_policy" "replication" {
  count = var.cross_region_replication ? 1 : 0
  name  = "${var.project}-${var.environment}-s3-replication-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          aws_s3_bucket.document_storage.arn,
          aws_s3_bucket.results_storage.arn
        ]
      },
      {
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Effect = "Allow"
        Resource = [
          "${aws_s3_bucket.document_storage.arn}/*",
          "${aws_s3_bucket.results_storage.arn}/*"
        ]
      },
      {
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Effect = "Allow"
        Resource = [
          "${aws_s3_bucket.document_replication[0].arn}/*",
          "${aws_s3_bucket.results_replication[0].arn}/*"
        ]
      }
    ]
  })

  tags = merge(var.tags, local.common_tags)
}

# Attach the replication policy to the replication role
resource "aws_iam_role_policy_attachment" "replication" {
  count      = var.cross_region_replication ? 1 : 0
  role       = aws_iam_role.replication[0].name
  policy_arn = aws_iam_policy.replication[0].arn
}

# Configure replication for document storage bucket
resource "aws_s3_bucket_replication_configuration" "document_storage" {
  count = var.cross_region_replication && var.enable_versioning ? 1 : 0
  
  # Ensure versioning is enabled on the bucket
  depends_on = [aws_s3_bucket_versioning.document_storage]

  role   = aws_iam_role.replication[0].arn
  bucket = aws_s3_bucket.document_storage.id

  rule {
    id     = "document-replication"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.document_replication[0].arn
      storage_class = "STANDARD"
    }
  }
}

# Configure replication for results storage bucket
resource "aws_s3_bucket_replication_configuration" "results_storage" {
  count = var.cross_region_replication && var.enable_versioning ? 1 : 0
  
  # Ensure versioning is enabled on the bucket
  depends_on = [aws_s3_bucket_versioning.results_storage]

  role   = aws_iam_role.replication[0].arn
  bucket = aws_s3_bucket.results_storage.id

  rule {
    id     = "results-replication"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.results_replication[0].arn
      storage_class = "STANDARD"
    }
  }
}

#------------------------------------------------------------------------------
# Outputs
#------------------------------------------------------------------------------

output "document_bucket_id" {
  description = "ID of the document storage S3 bucket for reference by other modules"
  value       = aws_s3_bucket.document_storage.id
}

output "document_bucket_arn" {
  description = "ARN of the document storage S3 bucket for IAM policies and resource references"
  value       = aws_s3_bucket.document_storage.arn
}

output "csv_bucket_id" {
  description = "ID of the CSV storage S3 bucket for reference by other modules"
  value       = aws_s3_bucket.csv_storage.id
}

output "csv_bucket_arn" {
  description = "ARN of the CSV storage S3 bucket for IAM policies and resource references"
  value       = aws_s3_bucket.csv_storage.arn
}

output "results_bucket_id" {
  description = "ID of the results storage S3 bucket for reference by other modules"
  value       = aws_s3_bucket.results_storage.id
}

output "results_bucket_arn" {
  description = "ARN of the results storage S3 bucket for IAM policies and resource references"
  value       = aws_s3_bucket.results_storage.arn
}

output "backup_bucket_id" {
  description = "ID of the backup storage S3 bucket for reference by other modules"
  value       = aws_s3_bucket.backup_storage.id
}

output "backup_bucket_arn" {
  description = "ARN of the backup storage S3 bucket for IAM policies and resource references"
  value       = aws_s3_bucket.backup_storage.arn
}

output "document_bucket_regional_domain_name" {
  description = "Regional domain name of the document storage S3 bucket for application integration"
  value       = aws_s3_bucket.document_storage.bucket_regional_domain_name
}

output "csv_bucket_regional_domain_name" {
  description = "Regional domain name of the CSV storage S3 bucket for application integration"
  value       = aws_s3_bucket.csv_storage.bucket_regional_domain_name
}

output "results_bucket_regional_domain_name" {
  description = "Regional domain name of the results storage S3 bucket for application integration"
  value       = aws_s3_bucket.results_storage.bucket_regional_domain_name
}

output "document_replication_bucket_arn" {
  description = "ARN of the document replication S3 bucket for disaster recovery references"
  value       = var.cross_region_replication ? aws_s3_bucket.document_replication[0].arn : null
}

output "results_replication_bucket_arn" {
  description = "ARN of the results replication S3 bucket for disaster recovery references"
  value       = var.cross_region_replication ? aws_s3_bucket.results_replication[0].arn : null
}