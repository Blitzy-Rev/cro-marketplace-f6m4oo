# ---------------------------------------------------------------------------------------------------------------------
# S3 BUCKET OUTPUTS
# Defines output variables for the Terraform storage module that expose S3 bucket identifiers,
# ARNs, and regional domain names for use by other modules and the main Terraform configuration.
# ---------------------------------------------------------------------------------------------------------------------

output "document_bucket_id" {
  description = "The ID of the S3 bucket used for document storage (legal documents, specifications, etc.)"
  value       = aws_s3_bucket.document_storage.id
}

output "document_bucket_arn" {
  description = "The ARN of the S3 bucket used for document storage (legal documents, specifications, etc.)"
  value       = aws_s3_bucket.document_storage.arn
}

output "csv_bucket_id" {
  description = "The ID of the S3 bucket used for CSV file storage (molecular data uploads)"
  value       = aws_s3_bucket.csv_storage.id
}

output "csv_bucket_arn" {
  description = "The ARN of the S3 bucket used for CSV file storage (molecular data uploads)"
  value       = aws_s3_bucket.csv_storage.arn
}

output "results_bucket_id" {
  description = "The ID of the S3 bucket used for experimental results storage"
  value       = aws_s3_bucket.results_storage.id
}

output "results_bucket_arn" {
  description = "The ARN of the S3 bucket used for experimental results storage"
  value       = aws_s3_bucket.results_storage.arn
}

output "backup_bucket_id" {
  description = "The ID of the S3 bucket used for backup storage"
  value       = aws_s3_bucket.backup_storage.id
}

output "backup_bucket_arn" {
  description = "The ARN of the S3 bucket used for backup storage"
  value       = aws_s3_bucket.backup_storage.arn
}

# Regional domain names for application integration
output "document_bucket_regional_domain_name" {
  description = "The regional domain name of the document storage S3 bucket for application integration"
  value       = aws_s3_bucket.document_storage.bucket_regional_domain_name
}

output "csv_bucket_regional_domain_name" {
  description = "The regional domain name of the CSV storage S3 bucket for application integration"
  value       = aws_s3_bucket.csv_storage.bucket_regional_domain_name
}

output "results_bucket_regional_domain_name" {
  description = "The regional domain name of the results storage S3 bucket for application integration"
  value       = aws_s3_bucket.results_storage.bucket_regional_domain_name
}

# Replication bucket outputs (conditional on cross-region replication being enabled)
output "document_replication_bucket_arn" {
  description = "The ARN of the S3 bucket used for document replication (DR purposes) - null if cross-region replication is disabled"
  value       = var.cross_region_replication ? aws_s3_bucket.document_replication[0].arn : null
}

output "results_replication_bucket_arn" {
  description = "The ARN of the S3 bucket used for results replication (DR purposes) - null if cross-region replication is disabled"
  value       = var.cross_region_replication ? aws_s3_bucket.results_replication[0].arn : null
}