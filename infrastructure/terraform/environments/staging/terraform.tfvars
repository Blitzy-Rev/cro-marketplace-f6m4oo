# Terraform variables for the Molecular Data Management and CRO Integration Platform - Staging Environment
# This file configures the staging environment to closely mirror production while optimizing costs

# AWS Regions
aws_region = "us-east-1"
secondary_aws_region = "us-west-2"

# Environment Identification
environment = "staging"
project_name = "molecule-platform-staging"

# Common tags for all resources
tags = {
  Environment = "staging"
  Project     = "MoleculeFlow"
  ManagedBy   = "Terraform"
  Owner       = "DevOps"
  CostCenter  = "Research-IT"
  Compliance  = "21CFRPart11"
}

# Networking configuration
networking = {
  vpc_cidr             = "10.0.0.0/16"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
  availability_zones   = ["us-east-1a", "us-east-1b", "us-east-1c"]
  enable_nat_gateway   = true
  enable_vpc_endpoints = true
  interface_endpoints  = ["ecr.api", "ecr.dkr", "logs", "secretsmanager", "ssm"]
  enable_flow_logs     = true
  flow_log_retention   = 30
}

# Compute configuration
compute = {
  ecs_cluster_name = "molecule-platform-staging"
  
  frontend_service = {
    name           = "frontend"
    container_port = 80
    host_port      = 80
    cpu            = 0.5
    memory         = 1024
    desired_count  = 2
    max_count      = 5
    min_count      = 2
  }
  
  api_service = {
    name           = "api"
    container_port = 8000
    host_port      = 8000
    cpu            = 1.0
    memory         = 2048
    desired_count  = 2
    max_count      = 10
    min_count      = 2
  }
  
  molecule_service = {
    name           = "molecule"
    container_port = 8001
    host_port      = 8001
    cpu            = 2.0
    memory         = 4096
    desired_count  = 2
    max_count      = 10
    min_count      = 2
  }
  
  worker_service = {
    name           = "worker"
    container_port = 8002
    host_port      = 8002
    cpu            = 2.0
    memory         = 8192
    desired_count  = 2
    max_count      = 20
    min_count      = 2
  }
  
  fargate_cpu = {
    small  = 512
    medium = 1024
    large  = 2048
    xlarge = 4096
  }
  
  fargate_memory = {
    small  = 1024
    medium = 2048
    large  = 4096
    xlarge = 8192
  }
  
  auto_scaling_settings = {
    frontend = {
      cpu_threshold     = 70
      scale_in_cooldown  = 300
      scale_out_cooldown = 180
    }
    api = {
      cpu_threshold     = 70
      scale_in_cooldown  = 300
      scale_out_cooldown = 180
    }
    molecule = {
      cpu_threshold     = 70
      scale_in_cooldown  = 300
      scale_out_cooldown = 180
    }
    worker = {
      queue_threshold   = 150
      scale_in_cooldown  = 300
      scale_out_cooldown = 180
    }
  }
  
  load_balancer_config = {
    health_check_path                = "/health"
    health_check_interval            = 30
    health_check_timeout             = 5
    health_check_healthy_threshold   = 2
    health_check_unhealthy_threshold = 3
  }
}

# Database configuration
database = {
  rds_instance_class           = "db.r5.large"
  rds_engine                   = "postgres"
  rds_engine_version           = "15.0"
  rds_allocated_storage        = 50
  rds_max_allocated_storage    = 200
  rds_multi_az                 = true
  rds_backup_retention_period  = 14
  rds_deletion_protection      = true
  rds_storage_encrypted        = true
  rds_db_name                  = "moleculedb"
  rds_username                 = "postgres"
  create_read_replicas         = true
  read_replica_count           = 1
  elasticache_enabled          = true
  elasticache_node_type        = "cache.t3.medium"
  elasticache_engine_version   = "7.0"
  elasticache_num_cache_clusters = 2
  elasticache_automatic_failover_enabled = true
  elasticache_at_rest_encryption_enabled = true
  elasticache_transit_encryption_enabled = true
  create_secrets_manager_secret = true
}

# Storage configuration
storage = {
  document_bucket_name  = "molecule-platform-staging-documents"
  csv_bucket_name       = "molecule-platform-staging-csv"
  results_bucket_name   = "molecule-platform-staging-results"
  backup_bucket_name    = "molecule-platform-staging-backups"
  enable_versioning     = true
  enable_encryption     = true
  cross_region_replication = true
  lifecycle_rules = [
    {
      id                        = "document-transition"
      prefix                    = "documents/"
      enabled                   = true
      transition_days           = 90
      transition_storage_class  = "STANDARD_IA"
      expiration_days           = 0
    },
    {
      id                        = "csv-transition"
      prefix                    = "csv/"
      enabled                   = true
      transition_days           = 60
      transition_storage_class  = "STANDARD_IA"
      expiration_days           = 0
    },
    {
      id                        = "results-transition"
      prefix                    = "results/"
      enabled                   = true
      transition_days           = 90
      transition_storage_class  = "STANDARD_IA"
      expiration_days           = 0
    },
    {
      id                        = "backups-transition"
      prefix                    = "backups/"
      enabled                   = true
      transition_days           = 30
      transition_storage_class  = "GLACIER"
      expiration_days           = 365
    }
  ]
}

# Security configuration
security = {
  enable_waf               = true
  enable_guardduty         = true
  enable_cloudtrail        = true
  enable_config            = true
  kms_key_deletion_window  = 14
  cognito_user_pool_name   = "molecule-platform-staging-users"
  cognito_identity_pool_name = "molecule-platform-staging-identity"
}

# Monitoring configuration
monitoring = {
  enable_enhanced_monitoring = true
  cloudwatch_log_retention   = 30
  alarm_email                = "staging-alerts@example.com"
  enable_dashboard           = true
  metric_alarms = {
    cpu_utilization = {
      threshold            = 80
      evaluation_periods   = 3
      period               = 300
      statistic            = "Average"
      comparison_operator  = "GreaterThanThreshold"
      treat_missing_data   = "missing"
    }
    memory_utilization = {
      threshold            = 85
      evaluation_periods   = 3
      period               = 300
      statistic            = "Average"
      comparison_operator  = "GreaterThanThreshold"
      treat_missing_data   = "missing"
    }
    database_connections = {
      threshold            = 80
      evaluation_periods   = 3
      period               = 300
      statistic            = "Average"
      comparison_operator  = "GreaterThanThreshold"
      treat_missing_data   = "missing"
    }
    api_error_rate = {
      threshold            = 2
      evaluation_periods   = 3
      period               = 300
      statistic            = "Average"
      comparison_operator  = "GreaterThanThreshold"
      treat_missing_data   = "missing"
    }
    api_latency = {
      threshold            = 500
      evaluation_periods   = 3
      period               = 300
      statistic            = "p95"
      comparison_operator  = "GreaterThanThreshold"
      treat_missing_data   = "missing"
    }
    molecule_processing_time = {
      threshold            = 30
      evaluation_periods   = 3
      period               = 300
      statistic            = "Average"
      comparison_operator  = "GreaterThanThreshold"
      treat_missing_data   = "missing"
    }
    disk_usage = {
      threshold            = 85
      evaluation_periods   = 3
      period               = 300
      statistic            = "Average"
      comparison_operator  = "GreaterThanThreshold"
      treat_missing_data   = "missing"
    }
    "5xx_errors" = {
      threshold            = 5
      evaluation_periods   = 1
      period               = 60
      statistic            = "Sum"
      comparison_operator  = "GreaterThanThreshold"
      treat_missing_data   = "notBreaching"
    }
  }
}

# Disaster Recovery Configuration
enable_disaster_recovery = true