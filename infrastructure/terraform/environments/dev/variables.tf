# AWS region configuration
variable "aws_region" {
  description = "AWS region for primary deployment of the development environment"
  type        = string
  default     = "us-east-1"
}

variable "secondary_aws_region" {
  description = "AWS region for disaster recovery and cross-region replication for development"
  type        = string
  default     = "us-west-2"
}

# Environment identification
variable "environment" {
  description = "Deployment environment identifier"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Name of the project for resource naming and tagging"
  type        = string
  default     = "molecule-platform-dev"
}

# Tagging
variable "tags" {
  description = "Common tags to apply to all resources in the development environment"
  type        = map(string)
  default = {
    Environment = "dev"
    Project     = "molecule-platform"
    ManagedBy   = "terraform"
  }
}

# Networking configuration
variable "networking" {
  description = "Networking configuration for the development environment"
  type = object({
    vpc_cidr             = string
    public_subnet_cidrs  = list(string)
    private_subnet_cidrs = list(string)
    availability_zones   = list(string)
    enable_nat_gateway   = bool
    enable_vpc_endpoints = bool
    interface_endpoints  = list(string)
    enable_flow_logs     = bool
    flow_log_retention   = number
  })

  default = {
    # Smaller CIDR blocks for development
    vpc_cidr             = "10.0.0.0/20"
    public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
    private_subnet_cidrs = ["10.0.3.0/24", "10.0.4.0/24"]
    availability_zones   = ["us-east-1a", "us-east-1b"]
    enable_nat_gateway   = true
    # Minimal VPC endpoints for cost optimization
    enable_vpc_endpoints = true
    interface_endpoints  = ["ecr.api", "ecr.dkr", "secretsmanager", "logs"]
    enable_flow_logs     = true
    flow_log_retention   = 7  # Shorter retention period for dev
  }
}

# Compute configuration
variable "compute" {
  description = "Compute configuration for the development environment"
  type = object({
    ecs_cluster_name    = string
    frontend_service    = object({
      name          = string
      desired_count = number
      port          = number
    })
    api_service         = object({
      name          = string
      desired_count = number
      port          = number
    })
    molecule_service    = object({
      name          = string
      desired_count = number
      port          = number
    })
    worker_service      = object({
      name          = string
      desired_count = number
    })
    fargate_cpu         = map(number)
    fargate_memory      = map(number)
    auto_scaling_settings = map(object({
      min_capacity      = number
      max_capacity      = number
      scale_out_percent = number
      scale_in_percent  = number
    }))
    load_balancer_config = object({
      idle_timeout                = number
      enable_deletion_protection  = bool
      deregistration_delay        = number
      health_check_interval       = number
      health_check_timeout        = number
      healthy_threshold           = number
      unhealthy_threshold         = number
    })
  })

  default = {
    ecs_cluster_name    = "molecule-platform-dev"
    # Smaller service configurations for development
    frontend_service    = {
      name          = "frontend"
      desired_count = 1
      port          = 80
    }
    api_service         = {
      name          = "api"
      desired_count = 1
      port          = 8080
    }
    molecule_service    = {
      name          = "molecule"
      desired_count = 1
      port          = 8081
    }
    worker_service      = {
      name          = "worker"
      desired_count = 1
    }
    # Smaller instance sizes for development
    fargate_cpu         = {
      "frontend"  = 256  # 0.25 vCPU
      "api"       = 512  # 0.5 vCPU
      "molecule"  = 1024 # 1 vCPU
      "worker"    = 1024 # 1 vCPU
    }
    fargate_memory      = {
      "frontend"  = 512  # 0.5 GB
      "api"       = 1024 # 1 GB
      "molecule"  = 2048 # 2 GB
      "worker"    = 2048 # 2 GB
    }
    # Minimal auto-scaling for cost optimization
    auto_scaling_settings = {
      "frontend" = {
        min_capacity      = 1
        max_capacity      = 2
        scale_out_percent = 75
        scale_in_percent  = 25
      }
      "api" = {
        min_capacity      = 1
        max_capacity      = 2
        scale_out_percent = 75
        scale_in_percent  = 25
      }
      "molecule" = {
        min_capacity      = 1
        max_capacity      = 2
        scale_out_percent = 75
        scale_in_percent  = 25
      }
      "worker" = {
        min_capacity      = 1
        max_capacity      = 4
        scale_out_percent = 75
        scale_in_percent  = 25
      }
    }
    load_balancer_config = {
      idle_timeout               = 60
      enable_deletion_protection = false  # No deletion protection in dev
      deregistration_delay       = 30
      health_check_interval      = 30
      health_check_timeout       = 5
      healthy_threshold          = 2
      unhealthy_threshold        = 2
    }
  }
}

# Database configuration
variable "database" {
  description = "Database configuration for the development environment"
  type = object({
    rds_instance_class         = string
    rds_engine                 = string
    rds_engine_version         = string
    rds_allocated_storage      = number
    rds_max_allocated_storage  = number
    rds_multi_az               = bool
    rds_backup_retention_period = number
    create_read_replicas       = bool
    read_replica_count         = number
    elasticache_node_type      = string
    elasticache_engine_version = string
    elasticache_parameter_group_name = string
  })

  default = {
    # Smaller instance sizes for development
    rds_instance_class         = "db.t3.medium"
    rds_engine                 = "postgres"
    rds_engine_version         = "15.4"
    rds_allocated_storage      = 20
    rds_max_allocated_storage  = 100
    # Single-AZ deployment for cost optimization
    rds_multi_az               = false
    # Shorter backup retention period for development
    rds_backup_retention_period = 7
    # No read replicas for development
    create_read_replicas       = false
    read_replica_count         = 0
    # Smaller ElastiCache instance
    elasticache_node_type      = "cache.t3.small"
    elasticache_engine_version = "7.0"
    elasticache_parameter_group_name = "default.redis7" 
  }
}

# Storage configuration
variable "storage" {
  description = "Storage configuration for the development environment"
  type = object({
    document_bucket_name    = string
    csv_bucket_name         = string
    results_bucket_name     = string
    backup_bucket_name      = string
    enable_versioning       = bool
    enable_encryption       = bool
    lifecycle_rules         = list(object({
      prefix                = string
      enabled               = bool
      expiration_days       = number
      transition_to_glacier_days = number
    }))
    cross_region_replication = bool
  })

  default = {
    # Dev-prefixed bucket names
    document_bucket_name    = "dev-molecule-platform-documents"
    csv_bucket_name         = "dev-molecule-platform-csv"
    results_bucket_name     = "dev-molecule-platform-results"
    backup_bucket_name      = "dev-molecule-platform-backups"
    enable_versioning       = true
    enable_encryption       = true
    # Simplified lifecycle policies for development
    lifecycle_rules         = [
      {
        prefix                    = "csv/"
        enabled                   = true
        expiration_days           = 30
        transition_to_glacier_days = null
      },
      {
        prefix                    = "results/"
        enabled                   = true
        expiration_days           = 90
        transition_to_glacier_days = null
      },
      {
        prefix                    = "backups/"
        enabled                   = true
        expiration_days           = 30
        transition_to_glacier_days = null
      }
    ]
    # Disable cross-region replication for cost optimization
    cross_region_replication = false
  }
}

# Security configuration
variable "security" {
  description = "Security configuration for the development environment"
  type = object({
    enable_waf              = bool
    enable_guardduty        = bool
    enable_cloudtrail       = bool
    enable_config           = bool
    kms_key_deletion_window = number
    cognito_user_pool_name  = string
    cognito_identity_pool_name = string
  })

  default = {
    # Basic security features enabled
    enable_waf              = true
    enable_guardduty        = true
    enable_cloudtrail       = true
    enable_config           = false  # Disable Config for cost optimization
    kms_key_deletion_window = 7
    cognito_user_pool_name  = "molecule-platform-dev-users"
    cognito_identity_pool_name = "molecule-platform-dev-identity"
  }
}

# Monitoring configuration
variable "monitoring" {
  description = "Monitoring configuration for the development environment"
  type = object({
    enable_enhanced_monitoring = bool
    cloudwatch_log_retention   = number
    alarm_email                = string
    enable_dashboard           = bool
    metric_alarms              = map(object({
      threshold                = number
      evaluation_periods       = number
      period_seconds           = number
      statistic                = string
    }))
  })

  default = {
    # Basic monitoring for development
    enable_enhanced_monitoring = false
    # Shorter log retention periods
    cloudwatch_log_retention   = 7
    alarm_email                = "dev-alerts@example.com"
    # Enable CloudWatch dashboards for system monitoring
    enable_dashboard           = true
    # Basic alerting for critical metrics only
    metric_alarms              = {
      "cpu_utilization" = {
        threshold           = 80
        evaluation_periods  = 2
        period_seconds      = 300
        statistic           = "Average"
      },
      "memory_utilization" = {
        threshold           = 80
        evaluation_periods  = 2
        period_seconds      = 300
        statistic           = "Average"
      },
      "database_connections" = {
        threshold           = 50
        evaluation_periods  = 2
        period_seconds      = 300
        statistic           = "Maximum"
      }
    }
  }
}

# Disaster recovery configuration
variable "enable_disaster_recovery" {
  description = "Flag to enable disaster recovery configuration in secondary region"
  type        = bool
  default     = false  # Disabled for development environment
}