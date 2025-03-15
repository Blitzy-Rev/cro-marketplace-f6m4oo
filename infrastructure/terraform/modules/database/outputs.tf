# RDS Instance Information
output "rds_instance_endpoint" {
  description = "Endpoint URL for the primary RDS PostgreSQL instance"
  value       = aws_db_instance.primary.endpoint
}

output "rds_instance_address" {
  description = "DNS address of the primary RDS PostgreSQL instance"
  value       = aws_db_instance.primary.address
}

output "rds_instance_port" {
  description = "Port number for connecting to the RDS PostgreSQL instance"
  value       = aws_db_instance.primary.port
}

output "rds_instance_username" {
  description = "Master username for the RDS PostgreSQL instance"
  value       = aws_db_instance.primary.username
}

output "rds_instance_name" {
  description = "Database name for the RDS PostgreSQL instance"
  value       = aws_db_instance.primary.db_name
}

output "rds_instance_id" {
  description = "Identifier of the primary RDS PostgreSQL instance"
  value       = aws_db_instance.primary.id
}

# Read Replica Information
output "rds_read_replica_endpoints" {
  description = "List of endpoint URLs for RDS read replicas"
  value       = var.create_read_replicas ? [for replica in aws_db_instance.read_replica : replica.endpoint] : []
}

output "rds_read_replica_ids" {
  description = "List of identifiers for RDS read replicas"
  value       = var.create_read_replicas ? [for replica in aws_db_instance.read_replica : replica.id] : []
}

# ElastiCache Information
output "elasticache_endpoint" {
  description = "Primary endpoint for the ElastiCache Redis cluster"
  value       = var.elasticache_enabled ? aws_elasticache_replication_group.redis[0].primary_endpoint_address : null
}

output "elasticache_reader_endpoint" {
  description = "Reader endpoint for the ElastiCache Redis cluster"
  value       = var.elasticache_enabled ? aws_elasticache_replication_group.redis[0].reader_endpoint_address : null
}

output "elasticache_replication_group_id" {
  description = "Identifier of the ElastiCache Redis replication group"
  value       = var.elasticache_enabled ? aws_elasticache_replication_group.redis[0].id : null
}

# Secrets Manager Information
output "database_secret_arn" {
  description = "ARN of the Secrets Manager secret containing database credentials"
  value       = var.create_secrets_manager_secret ? aws_secretsmanager_secret.database[0].arn : null
}