aws_region          = "us-east-1"
secondary_aws_region = "us-west-2"
environment         = "dev"
project_name        = "molecule-platform-dev"

# Common resource tags
tags = {
  Environment = "dev"
  Project     = "MoleculeFlow"
  ManagedBy   = "Terraform"
  Owner       = "DevOps"
  CostCenter  = "Research-IT"
}

# Networking Configuration
networking = {
  vpc_cidr               = "10.0.0.0/16"
  public_subnet_cidrs    = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs   = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
  availability_zones     = ["us-east-1a", "us-east-1b", "us-east-1c"]
  enable_nat_gateway     = true
  enable_vpc_endpoints   = true
  interface_endpoints    = ["ecr.api", "ecr.dkr", "logs"]
  enable_flow_logs       = true
  flow_log_retention     = 7  # Only retain flow logs for 7 days in dev
}

# Compute Configuration
compute = {
  ecs_cluster_name = "molecule-platform-dev"
  
  # Frontend service configuration - simplified for dev
  frontend_service = {
    name           = "frontend"
    container_port = 80
    host_port      = 80
    cpu            = 0.5  # 0.5 vCPU
    memory         = 1024  # 1GB
    desired_count  = 1
    max_count      = 2
    min_count      = 1
  }
  
  # API service configuration
  api_service = {
    name           = "api"
    container_port = 8000
    host_port      = 8000
    cpu            = 1.0  # 1 vCPU
    memory         = 2048  # 2GB
    desired_count  = 1
    max_count      = 3
    min_count      = 1
  }
  
  # Molecule service configuration
  molecule_service = {
    name           = "molecule"
    container_port = 8001
    host_port      = 8001
    cpu            = 2.0  # 2 vCPU
    memory         = 4096  # 4GB
    desired_count  = 1
    max_count      = 3
    min_count      = 1
  }
  
  # Worker service configuration
  worker_service = {
    name           = "worker"
    container_port = 8002
    host_port      = 8002
    cpu            = 2.0  # 2 vCPU
    memory         = 8192  # 8GB
    desired_count  = 1
    max_count      = 4
    min_count      = 1
  }
  
  # Fargate task sizes
  fargate_cpu = {
    small  = 512   # 0.5 vCPU
    medium = 1024  # 1 vCPU
    large  = 2048  # 2 vCPU
    xlarge = 4096  # 4 vCPU
  }
  
  fargate_memory = {
    small  = 1024   # 1 GB
    medium = 2048   # 2 GB
    large  = 4096   # 4 GB
    xlarge = 8192   # 8 GB
  }
  
  # Auto-scaling settings
  auto_scaling_settings = {
    frontend = {
      cpu_threshold     = 80
      scale_in_cooldown  = 300
      scale_out_cooldown = 180
    }
    api = {
      cpu_threshold     = 80
      scale_in_cooldown  = 300
      scale_out_cooldown = 180
    }
    molecule = {
      cpu_threshold     = 80
      scale_in_cooldown  = 300
      scale_out_cooldown = 180
    }
    worker = {
      queue_threshold   = 200
      scale_in_cooldown  = 300
      scale_out_cooldown = 180
    }
  }
  
  # Load balancer configuration
  load_balancer_config = {
    health_check_path             = "/health"
    health_check_interval         = 30
    health_check_timeout          = 5
    health_check_healthy_threshold   = 2
    health_check_unhealthy_threshold = 3
  }
}

# Database Configuration
database = {
  rds_instance_class          = "db.t3.medium"  # Smaller instance for dev
  rds_engine                  = "postgres"
  rds_engine_version          = "15.0"
  rds_allocated_storage       = 20
  rds_max_allocated_storage   = 100
  rds_multi_az                = false  # No Multi-AZ for development to save costs
  rds_backup_retention_period = 7      # 7 days of backups
  rds_deletion_protection     = false  # Allow deletion in dev environment
  rds_storage_encrypted       = true
  rds_db_name                 = "moleculedb"
  rds_username                = "postgres"
  create_read_replicas        = false  # No read replicas for dev
  read_replica_count          = 0
  
  # ElastiCache configuration
  elasticache_enabled                  = true
  elasticache_node_type                = "cache.t3.small"  # Smaller instance for dev
  elasticache_engine_version           = "7.0"
  elasticache_num_cache_clusters       = 1  # Single node for dev
  elasticache_automatic_failover_enabled = false  # No failover for dev
  elasticache_at_rest_encryption_enabled = true
  elasticache_transit_encryption_enabled = true
  
  create_secrets_manager_secret = true
}

# Storage Configuration
storage = {
  document_bucket_name  = "molecule-platform-dev-documents"
  csv_bucket_name       = "molecule-platform-dev-csv"
  results_bucket_name   = "molecule-platform-dev-results"
  backup_bucket_name    = "molecule-platform-dev-backups"
  enable_versioning     = true
  enable_encryption     = true
  cross_region_replication = false  # No replication for dev environment
  
  # Lifecycle rules for different bucket prefixes
  lifecycle_rules = [
    {
      id                       = "document-transition"
      prefix                   = "documents/"
      enabled                  = true
      transition_days          = 90
      transition_storage_class = "STANDARD_IA"
      expiration_days          = 0  # No expiration
    },
    {
      id                       = "csv-transition"
      prefix                   = "csv/"
      enabled                  = true
      transition_days          = 60
      transition_storage_class = "STANDARD_IA"
      expiration_days          = 0  # No expiration
    },
    {
      id                       = "results-transition"
      prefix                   = "results/"
      enabled                  = true
      transition_days          = 90
      transition_storage_class = "STANDARD_IA"
      expiration_days          = 0  # No expiration
    },
    {
      id                       = "backups-transition"
      prefix                   = "backups/"
      enabled                  = true
      transition_days          = 30
      transition_storage_class = "GLACIER"
      expiration_days          = 365  # Expire after 1 year
    }
  ]
}

# Security Configuration
security = {
  enable_waf       = true
  enable_guardduty = true
  enable_cloudtrail = true
  enable_config     = false  # Disable AWS Config to reduce costs in dev
  kms_key_deletion_window = 7
  cognito_user_pool_name = "molecule-platform-dev-users"
  cognito_identity_pool_name = "molecule-platform-dev-identity"
}

# Monitoring Configuration
monitoring = {
  enable_enhanced_monitoring = false  # Disable enhanced monitoring to reduce costs in dev
  cloudwatch_log_retention   = 7      # Shorter retention for dev
  alarm_email                = "dev-alerts@example.com"
  enable_dashboard           = true
  
  # Basic alarm configurations
  metric_alarms = {
    cpu_utilization = {
      threshold            = 90
      evaluation_periods   = 3
      period               = 300
      statistic            = "Average"
      comparison_operator  = "GreaterThanThreshold"
      treat_missing_data   = "missing"
    }
    memory_utilization = {
      threshold            = 90
      evaluation_periods   = 3
      period               = 300
      statistic            = "Average"
      comparison_operator  = "GreaterThanThreshold"
      treat_missing_data   = "missing"
    }
    api_error_rate = {
      threshold            = 10
      evaluation_periods   = 3
      period               = 300
      statistic            = "Average"
      comparison_operator  = "GreaterThanThreshold"
      treat_missing_data   = "missing"
    }
  }
}

# Disaster Recovery Configuration
enable_disaster_recovery = false  # Disable DR for dev environment