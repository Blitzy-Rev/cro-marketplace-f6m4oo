# Global variables
aws_region           = "us-east-1"
secondary_aws_region = "us-west-2"
environment          = "prod"
project_name         = "molecule-platform"

# Common tags for all resources
tags = {
  Environment = "prod"
  Project     = "MoleculeFlow"
  ManagedBy   = "Terraform"
  Owner       = "DevOps"
  CostCenter  = "Research-IT"
  Compliance  = "21CFRPart11"
}

# Networking configuration
networking = {
  vpc_cidr              = "10.0.0.0/16"
  public_subnet_cidrs   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs  = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
  availability_zones    = ["us-east-1a", "us-east-1b", "us-east-1c"]
  enable_nat_gateway    = true
  enable_vpc_endpoints  = true
  interface_endpoints   = ["ecr.api", "ecr.dkr", "logs", "secretsmanager", "ssm", "elasticache", "rds", "s3"]
  enable_flow_logs      = true
  flow_log_retention    = 90
}

# Compute configuration
compute = {
  ecs_cluster_name = "molecule-platform-prod"
  
  frontend_service = {
    name           = "frontend"
    container_port = 80
    host_port      = 80
    cpu            = 0.5
    memory         = 1024
    desired_count  = 3
    max_count      = 10
    min_count      = 3
  }
  
  api_service = {
    name           = "api"
    container_port = 8000
    host_port      = 8000
    cpu            = 1.0
    memory         = 2048
    desired_count  = 3
    max_count      = 20
    min_count      = 3
  }
  
  molecule_service = {
    name           = "molecule"
    container_port = 8001
    host_port      = 8001
    cpu            = 2.0
    memory         = 4096
    desired_count  = 3
    max_count      = 20
    min_count      = 3
  }
  
  worker_service = {
    name           = "worker"
    container_port = 8002
    host_port      = 8002
    cpu            = 2.0
    memory         = 8192
    desired_count  = 3
    max_count      = 50
    min_count      = 3
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
      cpu_threshold     = 60
      scale_in_cooldown  = 300
      scale_out_cooldown = 180
    }
    molecule = {
      cpu_threshold     = 60
      scale_in_cooldown  = 300
      scale_out_cooldown = 180
    }
    worker = {
      queue_threshold   = 100
      scale_in_cooldown  = 300
      scale_out_cooldown = 180
    }
  }
  
  load_balancer_config = {
    health_check_path               = "/health"
    health_check_interval           = 30
    health_check_timeout            = 5
    health_check_healthy_threshold   = 2
    health_check_unhealthy_threshold = 3
    enable_access_logs              = true
    access_logs_retention           = 90
    enable_waf                      = true
    ssl_policy                      = "ELBSecurityPolicy-TLS-1-2-2017-01"
  }
}

# Database configuration
database = {
  rds_instance_class                   = "db.r5.2xlarge"
  rds_engine                           = "postgres"
  rds_engine_version                   = "15.0"
  rds_allocated_storage               = 100
  rds_max_allocated_storage           = 500
  rds_multi_az                         = true
  rds_backup_retention_period         = 30
  rds_deletion_protection              = true
  rds_storage_encrypted                = true
  rds_db_name                          = "moleculedb"
  rds_username                         = "postgres"
  create_read_replicas                = true
  read_replica_count                  = 2
  elasticache_enabled                 = true
  elasticache_node_type               = "cache.m5.large"
  elasticache_engine_version           = "7.0"
  elasticache_num_cache_clusters      = 3
  elasticache_automatic_failover_enabled = true
  elasticache_at_rest_encryption_enabled = true
  elasticache_transit_encryption_enabled = true
  create_secrets_manager_secret       = true
  performance_insights_enabled        = true
  performance_insights_retention_period = 7
  monitoring_interval                 = 30
  monitoring_role_arn                 = "arn:aws:iam::123456789012:role/rds-monitoring-role"
}

# Storage configuration
storage = {
  document_bucket_name    = "molecule-platform-prod-documents"
  csv_bucket_name         = "molecule-platform-prod-csv"
  results_bucket_name     = "molecule-platform-prod-results"
  backup_bucket_name      = "molecule-platform-prod-backups"
  enable_versioning       = true
  enable_encryption       = true
  cross_region_replication = true
  
  lifecycle_rules = [
    {
      id = "document-transition"
      prefix = "documents/"
      enabled = true
      transition_days = 90
      transition_storage_class = "STANDARD_IA"
      expiration_days = 0
    },
    {
      id = "csv-transition"
      prefix = "csv/"
      enabled = true
      transition_days = 60
      transition_storage_class = "STANDARD_IA"
      expiration_days = 0
    },
    {
      id = "results-transition"
      prefix = "results/"
      enabled = true
      transition_days = 90
      transition_storage_class = "STANDARD_IA"
      expiration_days = 0
    },
    {
      id = "backups-transition"
      prefix = "backups/"
      enabled = true
      transition_days = 30
      transition_storage_class = "GLACIER"
      expiration_days = 2555
    }
  ]
  
  enable_object_lock = true
  object_lock_retention_days = 90
}

# Security configuration
security = {
  enable_waf              = true
  enable_guardduty        = true
  enable_cloudtrail       = true
  enable_config           = true
  kms_key_deletion_window = 30
  cognito_user_pool_name  = "molecule-platform-prod-users"
  cognito_identity_pool_name = "molecule-platform-prod-identity"
  mfa_configuration       = "ON"
  
  password_policy = {
    minimum_length               = 12
    require_lowercase            = true
    require_uppercase            = true
    require_numbers              = true
    require_symbols              = true
    temporary_password_validity_days = 3
  }
  
  waf_rules = [
    "AWSManagedRulesCommonRuleSet",
    "AWSManagedRulesKnownBadInputsRuleSet",
    "AWSManagedRulesSQLiRuleSet",
    "AWSManagedRulesLinuxRuleSet"
  ]
  
  security_group_ingress_cidr = "0.0.0.0/0"
  enable_securityhub          = true
  enable_inspector            = true
}

# Monitoring configuration
monitoring = {
  enable_enhanced_monitoring = true
  cloudwatch_log_retention   = 90
  alarm_email                = "prod-alerts@example.com"
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
      threshold            = 1
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
      threshold            = 1
      evaluation_periods   = 1
      period               = 60
      statistic            = "Sum"
      comparison_operator  = "GreaterThanThreshold"
      treat_missing_data   = "notBreaching"
    }
  }
  
  enable_prometheus     = true
  enable_grafana        = true
  enable_xray           = true
  enable_alarm_actions  = true
  alarm_actions         = [
    "arn:aws:sns:us-east-1:123456789012:prod-alerts",
    "arn:aws:sns:us-east-1:123456789012:pagerduty-integration"
  ]
}

# Disaster recovery configuration
enable_disaster_recovery = true

# Domain configuration
domain_name = "moleculeflow.com"
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/abcdef12-3456-7890-abcd-ef1234567890"