# outputs.tf for the Molecular Data Management and CRO Integration Platform

# Networking outputs
output "vpc_id" {
  description = "The ID of the VPC created for the platform"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.networking.private_subnet_ids
}

# Compute outputs
output "ecs_cluster_id" {
  description = "The ID of the ECS cluster"
  value       = module.compute.cluster_id
}

output "ecs_cluster_arn" {
  description = "The ARN of the ECS cluster"
  value       = module.compute.cluster_arn
}

output "alb_dns_name" {
  description = "The DNS name of the Application Load Balancer"
  value       = module.compute.alb_dns_name
}

output "alb_zone_id" {
  description = "The zone ID of the Application Load Balancer"
  value       = module.compute.alb_zone_id
}

# Database outputs
output "rds_endpoint" {
  description = "The endpoint of the RDS PostgreSQL instance"
  value       = module.database.rds_instance_endpoint
}

output "rds_read_replica_endpoints" {
  description = "The endpoints of the RDS read replicas"
  value       = module.database.rds_read_replica_endpoints
}

output "elasticache_endpoint" {
  description = "The endpoint of the ElastiCache Redis cluster"
  value       = module.database.elasticache_endpoint
}

output "database_secret_arn" {
  description = "The ARN of the Secrets Manager secret containing database credentials"
  value       = module.database.database_secret_arn
}

# Storage outputs
output "document_bucket_id" {
  description = "The ID of the S3 bucket for document storage"
  value       = module.storage.document_bucket_id
}

output "csv_bucket_id" {
  description = "The ID of the S3 bucket for CSV file storage"
  value       = module.storage.csv_bucket_id
}

output "results_bucket_id" {
  description = "The ID of the S3 bucket for experimental results storage"
  value       = module.storage.results_bucket_id
}

# Security outputs
output "kms_key_arn" {
  description = "The ARN of the KMS key used for encryption"
  value       = module.security.kms_key_arn
}

output "cognito_user_pool_id" {
  description = "The ID of the Cognito user pool"
  value       = module.security.cognito_user_pool_id
}

output "cognito_user_pool_client_id" {
  description = "The ID of the Cognito user pool client"
  value       = module.security.cognito_user_pool_client_id
}

output "task_execution_role_arn" {
  description = "The ARN of the ECS task execution role"
  value       = module.security.task_execution_role_arn
}

output "task_role_arns" {
  description = "Map of ARNs for task-specific IAM roles"
  value       = module.security.task_role_arns
}

# Monitoring outputs
output "cloudwatch_dashboard_urls" {
  description = "URLs for accessing CloudWatch dashboards"
  value       = module.monitoring.dashboard_urls
}

output "alarm_topic_arn" {
  description = "The ARN of the SNS topic for CloudWatch alarms"
  value       = module.monitoring.alarm_topic_arn
}

# Environment outputs
output "environment" {
  description = "The deployment environment name (dev, staging, prod)"
  value       = var.environment
}

output "aws_region" {
  description = "The AWS region used for deployment"
  value       = var.aws_region
}

output "secondary_aws_region" {
  description = "The secondary AWS region used for disaster recovery"
  value       = var.enable_disaster_recovery ? var.secondary_aws_region : null
}

# Application URLs
output "frontend_url" {
  description = "The URL for accessing the frontend application"
  value       = local.frontend_url
}

output "api_url" {
  description = "The URL for accessing the API"
  value       = local.api_url
}