# Terraform AWS Database Module for Molecular Data Management and CRO Integration Platform
#
# This module provisions and configures the PostgreSQL RDS instances and ElastiCache Redis clusters
# required for the Molecular Data Management platform, with features for high availability,
# performance optimization, and security compliance.

# Required providers
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

locals {
  # Resource naming convention
  name_prefix                = "${var.project_name}-${var.environment}"
  db_subnet_group_name       = "${local.name_prefix}-db-subnet"
  db_parameter_group_name    = "${local.name_prefix}-pg-params"
  cache_subnet_group_name    = "${local.name_prefix}-cache-subnet"
  cache_parameter_group_name = "${local.name_prefix}-redis-params"
  
  # Common tags to be applied to all resources
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = var.project_name
      Module      = "database"
      ManagedBy   = "terraform"
    }
  )
}

# Generate a secure random password for the database
resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
  min_lower        = 2
  min_upper        = 2
  min_numeric      = 2
  min_special      = 2
}

# Create a subnet group for RDS instances
resource "aws_db_subnet_group" "main" {
  name        = local.db_subnet_group_name
  description = "Subnet group for ${var.project_name} PostgreSQL instances in ${var.environment}"
  subnet_ids  = var.subnet_ids
  
  tags = merge(
    local.common_tags,
    {
      Name = local.db_subnet_group_name
    }
  )
}

# Create parameter group for PostgreSQL configuration
resource "aws_db_parameter_group" "main" {
  name        = local.db_parameter_group_name
  family      = "postgres${var.postgresql_version}"
  description = "Parameter group for ${var.project_name} PostgreSQL instances in ${var.environment}"
  
  # Performance optimization parameters based on technical specs section 6.3.4
  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/32768}MB"
  }
  
  parameter {
    name  = "max_connections"
    value = var.environment == "production" ? "500" : "200"
  }
  
  parameter {
    name  = "work_mem"
    value = var.environment == "production" ? "4MB" : "2MB"
  }
  
  parameter {
    name  = "maintenance_work_mem"
    value = var.environment == "production" ? "256MB" : "128MB"
  }
  
  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory/32768*3/4}MB"
  }
  
  # Logging parameters for auditing and troubleshooting
  parameter {
    name  = "log_statement"
    value = var.environment == "production" ? "none" : "ddl"
  }
  
  parameter {
    name  = "log_min_duration_statement"
    value = var.environment == "production" ? "1000" : "100"
  }
  
  # Enable extensions for chemical structure support (as per section 6.3)
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = local.db_parameter_group_name
    }
  )
}

# Create the primary RDS PostgreSQL instance
resource "aws_db_instance" "main" {
  identifier              = "${local.name_prefix}-postgres"
  engine                  = "postgres"
  engine_version          = var.postgresql_version
  instance_class          = var.db_instance_class
  allocated_storage       = var.allocated_storage
  max_allocated_storage   = var.max_allocated_storage
  storage_type            = "gp3"
  storage_encrypted       = true
  kms_key_id              = var.kms_key_id
  
  db_name                 = var.db_name
  username                = var.db_username
  password                = random_password.db_password.result
  port                    = 5432
  
  vpc_security_group_ids  = var.security_group_ids
  db_subnet_group_name    = aws_db_subnet_group.main.name
  parameter_group_name    = aws_db_parameter_group.main.name
  
  # High availability configuration (section 8.2.3)
  multi_az                = var.environment == "production" ? true : false
  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window           = "03:00-05:00"
  maintenance_window      = "sun:05:00-sun:07:00"
  
  # Data protection settings
  copy_tags_to_snapshot   = true
  deletion_protection     = var.environment == "production" ? true : false
  skip_final_snapshot     = var.environment == "production" ? false : true
  final_snapshot_identifier = var.environment == "production" ? "${local.name_prefix}-postgres-final-snapshot" : null
  
  # Monitoring and logging configuration
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval             = 60
  monitoring_role_arn             = var.monitoring_role_arn
  performance_insights_enabled    = true
  performance_insights_retention_period = var.environment == "production" ? 731 : 7
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-postgres"
    }
  )
  
  # Prevent accidental deletion of production database
  lifecycle {
    prevent_destroy = var.environment == "production" ? true : false
  }
}

# Create read replicas for the primary RDS instance
# These provide scale-out capabilities for read-heavy operations (section 6.3.4)
resource "aws_db_instance" "read_replica" {
  count                   = var.read_replica_count
  
  identifier              = "${local.name_prefix}-postgres-replica-${count.index + 1}"
  replicate_source_db     = aws_db_instance.main.identifier
  instance_class          = var.read_replica_instance_class
  
  vpc_security_group_ids  = var.security_group_ids
  parameter_group_name    = aws_db_parameter_group.main.name
  
  # Configure backup settings for replicas
  backup_retention_period = 0
  skip_final_snapshot     = true
  
  copy_tags_to_snapshot   = true
  
  # Monitoring configuration
  monitoring_interval     = 60
  monitoring_role_arn     = var.monitoring_role_arn
  performance_insights_enabled = true
  performance_insights_retention_period = var.environment == "production" ? 731 : 7
  
  # Distribute read replicas across AZs for high availability
  availability_zone       = element(var.availability_zones, count.index % length(var.availability_zones))
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-postgres-replica-${count.index + 1}"
    }
  )
}

# Create a subnet group for ElastiCache Redis clusters
resource "aws_elasticache_subnet_group" "main" {
  name        = local.cache_subnet_group_name
  description = "Subnet group for ${var.project_name} ElastiCache clusters in ${var.environment}"
  subnet_ids  = var.subnet_ids
  
  tags = merge(
    local.common_tags,
    {
      Name = local.cache_subnet_group_name
    }
  )
}

# Create parameter group for Redis configuration
resource "aws_elasticache_parameter_group" "main" {
  name        = local.cache_parameter_group_name
  family      = "redis${var.redis_version}"
  description = "Parameter group for ${var.project_name} Redis clusters in ${var.environment}"
  
  # Configure Redis for optimal caching performance
  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"
  }
  
  parameter {
    name  = "tcp-keepalive"
    value = "300"
  }
  
  # Additional parameters for session management and query caching
  parameter {
    name  = "notify-keyspace-events"
    value = "Ex"
  }
  
  parameter {
    name  = "maxmemory-samples"
    value = "10"
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = local.cache_parameter_group_name
    }
  )
}

# Create ElastiCache Redis cluster for caching and session management
resource "aws_elasticache_replication_group" "main" {
  replication_group_id          = "${local.name_prefix}-redis"
  description                   = "Redis cluster for ${var.project_name} caching in ${var.environment}"
  
  node_type                     = var.cache_node_type
  port                          = 6379
  
  # High availability configuration
  num_cache_clusters            = var.environment == "production" ? 3 : 2
  automatic_failover_enabled    = var.environment == "production" ? true : false
  
  subnet_group_name             = aws_elasticache_subnet_group.main.name
  security_group_ids            = var.security_group_ids
  
  # Redis version and parameter configuration
  engine                        = "redis"
  engine_version                = var.redis_version
  parameter_group_name          = aws_elasticache_parameter_group.main.name
  
  # Enable encryption for data protection (section 6.5.2)
  at_rest_encryption_enabled    = true
  transit_encryption_enabled    = true
  
  # Maintenance and backup configuration
  maintenance_window            = "sun:07:00-sun:09:00"
  snapshot_window               = "05:00-07:00"
  snapshot_retention_limit      = var.environment == "production" ? 7 : 1
  
  auto_minor_version_upgrade    = true
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-redis"
    }
  )
}

# Create a secret in AWS Secrets Manager for database credentials
resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${local.name_prefix}-db-credentials"
  description = "Database credentials for ${var.project_name} in ${var.environment} environment"
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-db-credentials"
    }
  )
}

# Store database credentials in the secret
resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id     = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username             = aws_db_instance.main.username
    password             = random_password.db_password.result
    engine               = "postgres"
    host                 = aws_db_instance.main.address
    port                 = aws_db_instance.main.port
    dbname               = aws_db_instance.main.db_name
    dbInstanceIdentifier = aws_db_instance.main.id
  })
}

# Outputs for downstream modules to use
output "rds_instance_endpoint" {
  description = "The connection endpoint for the primary RDS instance"
  value       = aws_db_instance.main.endpoint
}

output "rds_instance_address" {
  description = "The address of the primary RDS instance"
  value       = aws_db_instance.main.address
}

output "rds_instance_port" {
  description = "The port of the primary RDS instance"
  value       = aws_db_instance.main.port
}

output "rds_instance_username" {
  description = "The master username for the database"
  value       = aws_db_instance.main.username
}

output "rds_instance_name" {
  description = "The database name"
  value       = aws_db_instance.main.db_name
}

output "rds_read_replica_endpoints" {
  description = "List of read replica endpoints"
  value       = aws_db_instance.read_replica[*].endpoint
}

output "elasticache_endpoint" {
  description = "The primary endpoint of the ElastiCache cluster"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "elasticache_reader_endpoint" {
  description = "The reader endpoint of the ElastiCache cluster"
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "database_secret_arn" {
  description = "The ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "rds_instance_id" {
  description = "The RDS instance ID"
  value       = aws_db_instance.main.id
}

output "rds_read_replica_ids" {
  description = "List of read replica IDs"
  value       = aws_db_instance.read_replica[*].id
}

output "elasticache_replication_group_id" {
  description = "The ID of the ElastiCache replication group"
  value       = aws_elasticache_replication_group.main.id
}