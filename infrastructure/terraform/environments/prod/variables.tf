# ----------------------------------------
# Basic Settings
# ----------------------------------------

variable "aws_region" {
  description = "AWS region for primary deployment of the production environment"
  type        = string
  default     = "us-east-1"
}

variable "secondary_aws_region" {
  description = "AWS region for disaster recovery and cross-region replication for production"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Deployment environment identifier"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Name of the project for resource naming and tagging"
  type        = string
  default     = "molecule-platform"
}

variable "tags" {
  description = "Common tags to apply to all resources in the production environment"
  type        = map(string)
  default     = {
    Environment = "prod"
    Project     = "molecule-platform"
    ManagedBy   = "terraform"
    Compliance  = "21CFRPart11"
    DataClass   = "confidential"
  }
}

# ----------------------------------------
# Networking Configuration
# ----------------------------------------

variable "networking" {
  description = "Networking configuration for the production environment"
  type = object({
    vpc_cidr               = string
    public_subnet_cidrs    = list(string)
    private_subnet_cidrs   = list(string)
    availability_zones     = list(string)
    enable_nat_gateway     = bool
    enable_vpc_endpoints   = bool
    interface_endpoints    = list(string)
    enable_flow_logs       = bool
    flow_log_retention     = number
  })
  
  default = {
    vpc_cidr               = "10.0.0.0/16"
    public_subnet_cidrs    = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
    private_subnet_cidrs   = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24", "10.0.7.0/24", "10.0.8.0/24", "10.0.9.0/24"]
    availability_zones     = ["us-east-1a", "us-east-1b", "us-east-1c"]
    enable_nat_gateway     = true
    enable_vpc_endpoints   = true
    interface_endpoints    = ["ecr.api", "ecr.dkr", "logs", "monitoring", "sqs", "sns", "s3", "secretsmanager", "kms", "elasticloadbalancing", "cloudwatch", "events"]
    enable_flow_logs       = true
    flow_log_retention     = 90
  }
}

# ----------------------------------------
# Compute Configuration
# ----------------------------------------

variable "compute" {
  description = "Compute configuration for the production environment"
  type = object({
    ecs_cluster_name = string
    frontend_service = object({
      name                 = string
      container_port       = number
      host_port            = number
      cpu                  = number
      memory               = number
      desired_count        = number
      deployment_type      = string
      health_check_path    = string
      health_check_timeout = number
      health_check_interval = number
    })
    api_service = object({
      name                 = string
      container_port       = number
      host_port            = number
      cpu                  = number
      memory               = number
      desired_count        = number
      deployment_type      = string
      health_check_path    = string
      health_check_timeout = number
      health_check_interval = number
    })
    molecule_service = object({
      name                 = string
      container_port       = number
      host_port            = number
      cpu                  = number
      memory               = number
      desired_count        = number
      deployment_type      = string
      health_check_path    = string
      health_check_timeout = number
      health_check_interval = number
    })
    worker_service = object({
      name                 = string
      container_port       = number
      host_port            = number
      cpu                  = number
      memory               = number
      desired_count        = number
      deployment_type      = string
    })
    fargate_cpu = map(number)
    fargate_memory = map(number)
    auto_scaling_settings = map(object({
      min_capacity           = number
      max_capacity           = number
      scale_out_threshold    = number
      scale_out_evaluation_periods = number
      scale_in_threshold     = number
      scale_in_evaluation_periods = number
    }))
    load_balancer_config = object({
      idle_timeout           = number
      deletion_protection    = bool
      access_logs_enabled    = bool
      access_logs_bucket     = string
      access_logs_prefix     = string
    })
  })
  
  default = {
    ecs_cluster_name = "molecule-platform-cluster-prod"
    frontend_service = {
      name                 = "frontend"
      container_port       = 80
      host_port            = 80
      cpu                  = 0.5
      memory               = 1024
      desired_count        = 3
      deployment_type      = "rolling"
      health_check_path    = "/"
      health_check_timeout = 5
      health_check_interval = 30
    }
    api_service = {
      name                 = "api"
      container_port       = 8000
      host_port            = 8000
      cpu                  = 1
      memory               = 2048
      desired_count        = 3
      deployment_type      = "blue-green"
      health_check_path    = "/health"
      health_check_timeout = 5
      health_check_interval = 30
    }
    molecule_service = {
      name                 = "molecule"
      container_port       = 8001
      host_port            = 8001
      cpu                  = 2
      memory               = 4096
      desired_count        = 3
      deployment_type      = "blue-green"
      health_check_path    = "/health"
      health_check_timeout = 5
      health_check_interval = 30
    }
    worker_service = {
      name                 = "worker"
      container_port       = 8002
      host_port            = 8002
      cpu                  = 2
      memory               = 8192
      desired_count        = 3
      deployment_type      = "rolling"
    }
    fargate_cpu = {
      "small"  = 256   # 0.25 vCPU
      "medium" = 512   # 0.5 vCPU
      "large"  = 1024  # 1 vCPU
      "xlarge" = 2048  # 2 vCPU
      "2xlarge" = 4096 # 4 vCPU
    }
    fargate_memory = {
      "small"  = 512   # 0.5 GB
      "medium" = 1024  # 1 GB
      "large"  = 2048  # 2 GB
      "xlarge" = 4096  # 4 GB
      "2xlarge" = 8192 # 8 GB
      "4xlarge" = 16384 # 16 GB
    }
    auto_scaling_settings = {
      "frontend" = {
        min_capacity           = 3
        max_capacity           = 10
        scale_out_threshold    = 70
        scale_out_evaluation_periods = 3
        scale_in_threshold     = 30
        scale_in_evaluation_periods = 10
      }
      "api" = {
        min_capacity           = 3
        max_capacity           = 20
        scale_out_threshold    = 60
        scale_out_evaluation_periods = 3
        scale_in_threshold     = 20
        scale_in_evaluation_periods = 10
      }
      "molecule" = {
        min_capacity           = 3
        max_capacity           = 20
        scale_out_threshold    = 60
        scale_out_evaluation_periods = 3
        scale_in_threshold     = 20
        scale_in_evaluation_periods = 10
      }
      "worker" = {
        min_capacity           = 3
        max_capacity           = 50
        scale_out_threshold    = 70
        scale_out_evaluation_periods = 3
        scale_in_threshold     = 30
        scale_in_evaluation_periods = 10
      }
    }
    load_balancer_config = {
      idle_timeout           = 60
      deletion_protection    = true
      access_logs_enabled    = true
      access_logs_bucket     = "molecule-platform-logs-prod"
      access_logs_prefix     = "alb-logs"
    }
  }
}

# ----------------------------------------
# Database Configuration
# ----------------------------------------

variable "database" {
  description = "Database configuration for the production environment"
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
    rds_instance_class         = "db.r5.2xlarge"
    rds_engine                 = "postgres"
    rds_engine_version         = "15.0"
    rds_allocated_storage      = 1000
    rds_max_allocated_storage  = 5000
    rds_multi_az               = true
    rds_backup_retention_period = 30
    create_read_replicas       = true
    read_replica_count         = 2
    elasticache_node_type      = "cache.m5.large"
    elasticache_engine_version = "7.0"
    elasticache_parameter_group_name = "default.redis7.cluster.on"
  }
}

# ----------------------------------------
# Storage Configuration
# ----------------------------------------

variable "storage" {
  description = "Storage configuration for the production environment"
  type = object({
    document_bucket_name     = string
    csv_bucket_name          = string
    results_bucket_name      = string
    backup_bucket_name       = string
    enable_versioning        = bool
    enable_encryption        = bool
    lifecycle_rules          = list(object({
      id                     = string
      prefix                 = string
      enabled                = bool
      expiration_days        = number
      noncurrent_version_expiration_days = number
      transitions            = list(object({
        days                 = number
        storage_class        = string
      }))
    }))
    cross_region_replication = bool
  })
  
  default = {
    document_bucket_name     = "molecule-platform-documents-prod"
    csv_bucket_name          = "molecule-platform-csv-prod"
    results_bucket_name      = "molecule-platform-results-prod"
    backup_bucket_name       = "molecule-platform-backups-prod"
    enable_versioning        = true
    enable_encryption        = true
    lifecycle_rules          = [
      {
        id                     = "csv-lifecycle"
        prefix                 = "uploads/"
        enabled                = true
        expiration_days        = 90
        noncurrent_version_expiration_days = 30
        transitions            = [
          {
            days                 = 30
            storage_class        = "STANDARD_IA"
          },
          {
            days                 = 90
            storage_class        = "GLACIER"
          }
        ]
      },
      {
        id                     = "results-lifecycle"
        prefix                 = "results/"
        enabled                = true
        expiration_days        = 0  # No automatic deletion
        noncurrent_version_expiration_days = 730
        transitions            = [
          {
            days                 = 90
            storage_class        = "STANDARD_IA"
          },
          {
            days                 = 365
            storage_class        = "GLACIER"
          }
        ]
      },
      {
        id                     = "backups-lifecycle"
        prefix                 = "backups/"
        enabled                = true
        expiration_days        = 0  # No automatic deletion
        noncurrent_version_expiration_days = 730
        transitions            = [
          {
            days                 = 30
            storage_class        = "STANDARD_IA"
          },
          {
            days                 = 90
            storage_class        = "GLACIER"
          }
        ]
      }
    ]
    cross_region_replication = true
  }
}

# ----------------------------------------
# Security Configuration
# ----------------------------------------

variable "security" {
  description = "Security configuration for the production environment"
  type = object({
    enable_waf                = bool
    enable_guardduty          = bool
    enable_cloudtrail         = bool
    enable_config             = bool
    kms_key_deletion_window   = number
    cognito_user_pool_name    = string
    cognito_identity_pool_name = string
  })
  
  default = {
    enable_waf                = true
    enable_guardduty          = true
    enable_cloudtrail         = true
    enable_config             = true
    kms_key_deletion_window   = 30
    cognito_user_pool_name    = "molecule-platform-users-prod"
    cognito_identity_pool_name = "molecule-platform-identity-prod"
  }
}

# ----------------------------------------
# Monitoring Configuration
# ----------------------------------------

variable "monitoring" {
  description = "Monitoring configuration for the production environment"
  type = object({
    enable_enhanced_monitoring = bool
    cloudwatch_log_retention   = number
    alarm_email                = string
    enable_dashboard           = bool
    metric_alarms              = map(object({
      comparison_operator      = string
      evaluation_periods       = number
      threshold                = number
      alarm_description        = string
      alarm_actions            = list(string)
      insufficient_data_actions = list(string)
    }))
  })
  
  default = {
    enable_enhanced_monitoring = true
    cloudwatch_log_retention   = 90
    alarm_email                = "prod-alerts@moleculeflow.com"
    enable_dashboard           = true
    metric_alarms              = {
      "high-cpu" = {
        comparison_operator      = "GreaterThanThreshold"
        evaluation_periods       = 2
        threshold                = 80
        alarm_description        = "High CPU utilization"
        alarm_actions            = ["arn:aws:sns:${var.aws_region}:*:molecule-platform-alarms-prod"]
        insufficient_data_actions = []
      },
      "high-memory" = {
        comparison_operator      = "GreaterThanThreshold"
        evaluation_periods       = 2
        threshold                = 85
        alarm_description        = "High memory utilization"
        alarm_actions            = ["arn:aws:sns:${var.aws_region}:*:molecule-platform-alarms-prod"]
        insufficient_data_actions = []
      },
      "high-disk" = {
        comparison_operator      = "GreaterThanThreshold"
        evaluation_periods       = 1
        threshold                = 85
        alarm_description        = "High disk utilization"
        alarm_actions            = ["arn:aws:sns:${var.aws_region}:*:molecule-platform-alarms-prod"]
        insufficient_data_actions = []
      },
      "high-errors" = {
        comparison_operator      = "GreaterThanThreshold"
        evaluation_periods       = 1
        threshold                = 1
        alarm_description        = "High error rate (>1%)"
        alarm_actions            = ["arn:aws:sns:${var.aws_region}:*:molecule-platform-alarms-prod"]
        insufficient_data_actions = []
      },
      "database-cpu" = {
        comparison_operator      = "GreaterThanThreshold"
        evaluation_periods       = 3
        threshold                = 75
        alarm_description        = "High database CPU utilization"
        alarm_actions            = ["arn:aws:sns:${var.aws_region}:*:molecule-platform-alarms-prod"]
        insufficient_data_actions = []
      },
      "database-memory" = {
        comparison_operator      = "GreaterThanThreshold"
        evaluation_periods       = 3
        threshold                = 80
        alarm_description        = "High database memory utilization"
        alarm_actions            = ["arn:aws:sns:${var.aws_region}:*:molecule-platform-alarms-prod"]
        insufficient_data_actions = []
      },
      "api-latency" = {
        comparison_operator      = "GreaterThanThreshold"
        evaluation_periods       = 3
        threshold                = 500
        alarm_description        = "API response time > 500ms"
        alarm_actions            = ["arn:aws:sns:${var.aws_region}:*:molecule-platform-alarms-prod"]
        insufficient_data_actions = []
      }
    }
  }
}

# ----------------------------------------
# Disaster Recovery Configuration
# ----------------------------------------

variable "enable_disaster_recovery" {
  description = "Flag to enable disaster recovery configuration in secondary region"
  type        = bool
  default     = true
}

# ----------------------------------------
# Domain Configuration
# ----------------------------------------

variable "domain_name" {
  description = "Domain name for the production environment"
  type        = string
  default     = "moleculeflow.com"
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for the production domain"
  type        = string
  default     = null # Will be provided during deployment
}