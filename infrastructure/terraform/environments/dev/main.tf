# Molecular Data Management and CRO Integration Platform
# Development Environment Infrastructure Configuration

# Define local variables for environment-specific configuration
locals {
  # Environment naming and tagging
  env_suffix    = "-${var.environment}"
  resource_tags = merge(var.tags, { Environment = var.environment })
  
  # Cognito configuration
  cognito_identity_pool_name = "${var.security.cognito_identity_pool_name}"
  callback_urls = [
    "http://localhost:3000/callback",
    "https://dev-molecule-platform.example.com/callback"
  ]
  logout_urls = [
    "http://localhost:3000",
    "https://dev-molecule-platform.example.com"
  ]
  password_policy = {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }
  
  # Security group references for module dependencies
  security_group_ids = {
    alb     = module.security.security_group_ids["alb"]
    ecs     = module.security.security_group_ids["ecs"]
    efs     = module.security.security_group_ids["efs"]
    bastion = module.security.security_group_ids["bastion"]
  }
  
  database_security_group_ids = [
    module.security.security_group_ids["database"]
  ]
  
  # S3 bucket ARNs for IAM policies
  s3_bucket_arns = [
    module.storage.s3_bucket_arns["documents"],
    module.storage.s3_bucket_arns["csv"],
    module.storage.s3_bucket_arns["results"],
    module.storage.s3_bucket_arns["backup"]
  ]
  
  # Task definitions for ECS services
  task_definitions = {
    frontend = {
      name           = var.compute.frontend_service.name
      cpu            = var.compute.fargate_cpu["frontend"]
      memory         = var.compute.fargate_memory["frontend"]
      container_port = var.compute.frontend_service.port
      host_port      = var.compute.frontend_service.port
      image          = "nginx:alpine" # Placeholder - will be overridden by CI/CD
    }
    api = {
      name           = var.compute.api_service.name
      cpu            = var.compute.fargate_cpu["api"]
      memory         = var.compute.fargate_memory["api"]
      container_port = var.compute.api_service.port
      host_port      = var.compute.api_service.port
      image          = "python:3.10-slim" # Placeholder - will be overridden by CI/CD
    }
    molecule = {
      name           = var.compute.molecule_service.name
      cpu            = var.compute.fargate_cpu["molecule"]
      memory         = var.compute.fargate_memory["molecule"]
      container_port = var.compute.molecule_service.port
      host_port      = var.compute.molecule_service.port
      image          = "python:3.10-slim" # Placeholder - will be overridden by CI/CD
    }
    worker = {
      name           = var.compute.worker_service.name
      cpu            = var.compute.fargate_cpu["worker"]
      memory         = var.compute.fargate_memory["worker"]
      container_port = 80 # Workers don't expose ports, but need a value
      host_port      = 80 # Workers don't expose ports, but need a value
      image          = "python:3.10-slim" # Placeholder - will be overridden by CI/CD
    }
  }
  
  # Service configurations for ECS services
  service_configs = {
    frontend = {
      name         = var.compute.frontend_service.name
      desired_count = var.compute.frontend_service.desired_count
      port         = var.compute.frontend_service.port
      expose_to_public = true
      health_check_path = "/"
    }
    api = {
      name         = var.compute.api_service.name
      desired_count = var.compute.api_service.desired_count
      port         = var.compute.api_service.port
      expose_to_public = true
      health_check_path = "/health"
    }
    molecule = {
      name         = var.compute.molecule_service.name
      desired_count = var.compute.molecule_service.desired_count
      port         = var.compute.molecule_service.port
      expose_to_public = false
      health_check_path = "/health"
    }
    worker = {
      name         = var.compute.worker_service.name
      desired_count = var.compute.worker_service.desired_count
      port         = 80 # Workers don't expose ports, but need a value
      expose_to_public = false
      health_check_path = "/health"
    }
  }
}

# Networking module - provisions VPC, subnets, NAT gateway, and VPC endpoints
module "networking" {
  source = "../../modules/networking"
  
  vpc_cidr             = var.networking.vpc_cidr
  public_subnet_cidrs  = var.networking.public_subnet_cidrs
  private_subnet_cidrs = var.networking.private_subnet_cidrs
  availability_zones   = var.networking.availability_zones
  enable_nat_gateway   = var.networking.enable_nat_gateway
  enable_vpc_endpoints = var.networking.enable_vpc_endpoints
  interface_endpoints  = var.networking.interface_endpoints
  enable_flow_logs     = var.networking.enable_flow_logs
  flow_log_retention   = var.networking.flow_log_retention
  
  environment  = var.environment
  project_name = var.project_name
  tags         = var.tags
}

# Compute module - provisions ECS cluster, services, and load balancer
module "compute" {
  source = "../../modules/compute"
  
  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
  private_subnet_ids = module.networking.private_subnet_ids
  security_group_ids = local.security_group_ids
  
  cluster_name     = var.compute.ecs_cluster_name
  task_definitions = local.task_definitions
  service_configs  = local.service_configs
  alb_config       = var.compute.load_balancer_config
  scaling_targets  = var.compute.auto_scaling_settings
  
  environment  = var.environment
  project_name = var.project_name
  tags         = var.tags
  
  depends_on = [module.networking, module.security]
}

# Database module - provisions RDS PostgreSQL and ElastiCache Redis
module "database" {
  source = "../../modules/database"
  
  subnet_ids          = module.networking.private_subnet_ids
  security_group_ids  = local.database_security_group_ids
  
  instance_class             = var.database.rds_instance_class
  engine                     = var.database.rds_engine
  engine_version             = var.database.rds_engine_version
  allocated_storage          = var.database.rds_allocated_storage
  max_allocated_storage      = var.database.rds_max_allocated_storage
  multi_az                   = var.database.rds_multi_az
  backup_retention_period    = var.database.rds_backup_retention_period
  create_read_replicas       = var.database.create_read_replicas
  read_replica_count         = var.database.read_replica_count
  
  elasticache_node_type      = var.database.elasticache_node_type
  elasticache_engine_version = var.database.elasticache_engine_version
  
  kms_key_id   = module.security.kms_key_id
  environment  = var.environment
  project_name = var.project_name
  tags         = var.tags
  
  depends_on = [module.networking, module.security]
}

# Storage module - provisions S3 buckets for documents, CSV files, results, and backups
module "storage" {
  source = "../../modules/storage"
  
  document_bucket_name     = var.storage.document_bucket_name
  csv_bucket_name          = var.storage.csv_bucket_name
  results_bucket_name      = var.storage.results_bucket_name
  backup_bucket_name       = var.storage.backup_bucket_name
  
  enable_versioning        = var.storage.enable_versioning
  enable_encryption        = var.storage.enable_encryption
  lifecycle_rules          = var.storage.lifecycle_rules
  cross_region_replication = var.storage.cross_region_replication
  replication_region       = var.secondary_aws_region
  
  kms_key_id   = module.security.kms_key_id
  environment  = var.environment
  project_name = var.project_name
  tags         = var.tags
  
  depends_on = [module.security]
}

# Security module - provisions KMS keys, Cognito user pool, and security features
module "security" {
  source = "../../modules/security"
  
  vpc_id = module.networking.vpc_id
  
  enable_waf         = var.security.enable_waf
  enable_guardduty   = var.security.enable_guardduty
  enable_cloudtrail  = var.security.enable_cloudtrail
  enable_config      = var.security.enable_config
  
  enable_key_rotation      = true
  kms_key_deletion_window  = var.security.kms_key_deletion_window
  
  cognito_user_pool_name     = var.security.cognito_user_pool_name
  cognito_identity_pool_name = local.cognito_identity_pool_name
  password_policy            = local.password_policy
  enable_mfa                 = false # Disabled for development environment
  
  callback_urls = local.callback_urls
  logout_urls   = local.logout_urls
  
  s3_bucket_arns = local.s3_bucket_arns
  
  environment  = var.environment
  project_name = var.project_name
  tags         = var.tags
  
  depends_on = [module.networking]
}

# Monitoring module - provisions CloudWatch alarms, logs, and dashboards
module "monitoring" {
  source = "../../modules/monitoring"
  
  environment = var.environment
  region      = var.aws_region
  tags        = var.tags
  monitoring  = var.monitoring
  
  compute_outputs  = module.compute
  database_outputs = module.database
  storage_outputs  = module.storage
  
  depends_on = [
    module.compute,
    module.database,
    module.storage
  ]
}

# Outputs for use by other modules or scripts
output "vpc_id" {
  description = "ID of the VPC created for the development environment"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of public subnets created for the development environment"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of private subnets created for the development environment"
  value       = module.networking.private_subnet_ids
}

output "security_group_ids" {
  description = "Map of security group IDs created for the development environment"
  value       = module.security.security_group_ids
}

output "ecs_cluster_id" {
  description = "ID of the ECS cluster created for the development environment"
  value       = module.compute.ecs_cluster_id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer for the development environment"
  value       = module.compute.alb_dns_name
}

output "rds_endpoint" {
  description = "Endpoint of the RDS PostgreSQL instance for the development environment"
  value       = module.database.rds_endpoint
}

output "elasticache_endpoint" {
  description = "Endpoint of the ElastiCache Redis cluster for the development environment"
  value       = module.database.elasticache_endpoint
}

output "s3_bucket_ids" {
  description = "Map of S3 bucket IDs created for the development environment"
  value       = module.storage.s3_bucket_ids
}

output "cognito_user_pool_id" {
  description = "ID of the Cognito user pool created for the development environment"
  value       = module.security.cognito_user_pool_id
}

output "cognito_user_pool_client_id" {
  description = "ID of the Cognito user pool client created for the development environment"
  value       = module.security.cognito_user_pool_client_id
}

output "kms_key_id" {
  description = "ID of the KMS key created for the development environment"
  value       = module.security.kms_key_id
}

output "cloudwatch_dashboard_urls" {
  description = "URLs for CloudWatch dashboards created for the development environment"
  value       = module.monitoring.dashboard_urls
}