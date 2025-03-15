# ------------------------------------------------------------------------------
# Database Module Variables
# ------------------------------------------------------------------------------
# This file defines input variables for the database Terraform module that
# provisions and configures PostgreSQL RDS instances and ElastiCache Redis
# clusters for the Molecular Data Management and CRO Integration Platform.
# ------------------------------------------------------------------------------

variable "identifier_prefix" {
  description = "Prefix for resource identifiers to ensure uniqueness"
  type        = string
  default     = ""
}

# Network configuration
variable "vpc_id" {
  description = "ID of the VPC where database resources will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs where database resources will be deployed"
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs to associate with database resources"
  type        = list(string)
}

# RDS PostgreSQL Configuration
variable "rds_instance_class" {
  description = "Instance class for the RDS PostgreSQL instance"
  type        = string
  default     = "db.t3.medium"
}

variable "rds_engine" {
  description = "Database engine for RDS instance"
  type        = string
  default     = "postgres"
}

variable "rds_engine_version" {
  description = "Version of the PostgreSQL engine"
  type        = string
  default     = "15.0"
}

variable "rds_allocated_storage" {
  description = "Allocated storage for the RDS instance in GB"
  type        = number
  default     = 20
}

variable "rds_max_allocated_storage" {
  description = "Maximum allocated storage for the RDS instance in GB for autoscaling"
  type        = number
  default     = 100
}

variable "rds_db_name" {
  description = "Name of the database to create in the RDS instance"
  type        = string
  default     = "moleculedb"
}

variable "rds_username" {
  description = "Username for the RDS master user"
  type        = string
  default     = "postgres"
}

variable "rds_password" {
  description = "Password for the RDS master user (if not provided, a random one will be generated)"
  type        = string
  default     = null
  sensitive   = true
}

variable "rds_multi_az" {
  description = "Whether to enable Multi-AZ deployment for RDS"
  type        = bool
  default     = false
}

variable "rds_backup_retention_period" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 7
}

variable "rds_deletion_protection" {
  description = "Whether to enable deletion protection for RDS"
  type        = bool
  default     = false
}

variable "rds_storage_encrypted" {
  description = "Whether to encrypt RDS storage"
  type        = bool
  default     = true
}

variable "rds_parameters" {
  description = "List of DB parameters to apply to the RDS instance"
  type = list(object({
    name         = string
    value        = string
    apply_method = string
  }))
  default = []
}

# Read Replica Configuration
variable "create_read_replicas" {
  description = "Whether to create read replicas for the RDS instance"
  type        = bool
  default     = false
}

variable "read_replica_count" {
  description = "Number of read replicas to create"
  type        = number
  default     = 1
}

variable "read_replica_instance_class" {
  description = "Instance class for read replicas (if different from primary)"
  type        = string
  default     = null
}

# ElastiCache Redis Configuration
variable "elasticache_enabled" {
  description = "Whether to create ElastiCache Redis cluster"
  type        = bool
  default     = true
}

variable "elasticache_node_type" {
  description = "Node type for ElastiCache Redis cluster"
  type        = string
  default     = "cache.t3.small"
}

variable "elasticache_engine_version" {
  description = "Redis engine version for ElastiCache"
  type        = string
  default     = "7.0"
}

variable "elasticache_num_cache_clusters" {
  description = "Number of cache clusters (nodes) in the replication group"
  type        = number
  default     = 2
}

variable "elasticache_automatic_failover_enabled" {
  description = "Whether to enable automatic failover for ElastiCache"
  type        = bool
  default     = true
}

variable "elasticache_at_rest_encryption_enabled" {
  description = "Whether to enable encryption at rest for ElastiCache"
  type        = bool
  default     = true
}

variable "elasticache_transit_encryption_enabled" {
  description = "Whether to enable encryption in transit for ElastiCache"
  type        = bool
  default     = true
}

variable "elasticache_parameters" {
  description = "List of ElastiCache parameters to apply"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

# Secrets Manager Configuration
variable "create_secrets_manager_secret" {
  description = "Whether to create a Secrets Manager secret for database credentials"
  type        = bool
  default     = true
}

# Tags
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}