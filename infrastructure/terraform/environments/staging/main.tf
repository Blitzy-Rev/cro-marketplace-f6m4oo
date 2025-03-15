# =============================================================================
# Terraform Configuration for Staging Environment
# Molecular Data Management and CRO Integration Platform
# =============================================================================

terraform {
  # Configure the backend for storing Terraform state
  backend "s3" {
    bucket         = "molecule-platform-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "molecule-platform-terraform-locks"
  }
}

# =============================================================================
# Local Values
# =============================================================================

locals {
  # Environment-specific naming and tagging
  environment = var.environment
  project_name = var.project_name
  name_prefix = "${var.project_name}-${var.environment}"
  
  # Security group configurations for services
  security_group_ids = {
    alb = module.networking.security_group_ids["alb"]
    ecs = module.networking.security_group_ids["ecs"]
    efs = module.networking.security_group_ids["efs"]
  }
  
  # Database security group configurations
  database_security_group_ids = {
    rds = module.networking.security_group_ids["rds"]
    elasticache = module.networking.security_group_ids["elasticache"]
  }
  
  # S3 bucket ARNs for IAM policies
  s3_bucket_arns = [
    "arn:aws:s3:::${var.storage.document_bucket_name}",
    "arn:aws:s3:::${var.storage.document_bucket_name}/*",
    "arn:aws:s3:::${var.storage.csv_bucket_name}",
    "arn:aws:s3:::${var.storage.csv_bucket_name}/*",
    "arn:aws:s3:::${var.storage.results_bucket_name}",
    "arn:aws:s3:::${var.storage.results_bucket_name}/*",
    "arn:aws:s3:::${var.storage.backup_bucket_name}",
    "arn:aws:s3:::${var.storage.backup_bucket_name}/*"
  ]
  
  # Cognito configuration
  cognito_identity_pool_name = "${var.security.cognito_identity_pool_name}-${random_string.suffix.result}"
  callback_urls = [
    "https://staging.moleculeflow.example.com/callback",
    "http://localhost:3000/callback"  # For local development against staging
  ]
  logout_urls = [
    "https://staging.moleculeflow.example.com",
    "http://localhost:3000"  # For local development against staging
  ]
  
  # Password policy for Cognito (production-like for staging)
  password_policy = {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
    temporary_password_validity_days = 7
  }
  
  # ECS task definitions for services
  task_definitions = {
    frontend = {
      name          = "${var.compute.frontend_service.name}"
      cpu           = var.compute.frontend_service.cpu * 1024  # Convert to CPU units
      memory        = var.compute.frontend_service.memory
      container_definitions = templatefile("../../templates/container_definitions/frontend.json.tpl", {
        name         = var.compute.frontend_service.name
        image        = "#{AWS::AccountId}.dkr.ecr.${var.aws_region}.amazonaws.com/molecule-platform-staging-frontend:latest"
        container_port = var.compute.frontend_service.container_port
        host_port    = var.compute.frontend_service.host_port
        cpu          = var.compute.frontend_service.cpu * 1024
        memory       = var.compute.frontend_service.memory
        environment  = var.environment
        region       = var.aws_region
        log_group    = "/ecs/${var.environment}/frontend"
      })
    },
    api = {
      name          = "${var.compute.api_service.name}"
      cpu           = var.compute.api_service.cpu * 1024
      memory        = var.compute.api_service.memory
      container_definitions = templatefile("../../templates/container_definitions/api.json.tpl", {
        name         = var.compute.api_service.name
        image        = "#{AWS::AccountId}.dkr.ecr.${var.aws_region}.amazonaws.com/molecule-platform-staging-api:latest"
        container_port = var.compute.api_service.container_port
        host_port    = var.compute.api_service.host_port
        cpu          = var.compute.api_service.cpu * 1024
        memory       = var.compute.api_service.memory
        environment  = var.environment
        region       = var.aws_region
        log_group    = "/ecs/${var.environment}/api"
      })
    },
    molecule = {
      name          = "${var.compute.molecule_service.name}"
      cpu           = var.compute.molecule_service.cpu * 1024
      memory        = var.compute.molecule_service.memory
      container_definitions = templatefile("../../templates/container_definitions/molecule.json.tpl", {
        name         = var.compute.molecule_service.name
        image        = "#{AWS::AccountId}.dkr.ecr.${var.aws_region}.amazonaws.com/molecule-platform-staging-molecule:latest"
        container_port = var.compute.molecule_service.container_port
        host_port    = var.compute.molecule_service.host_port
        cpu          = var.compute.molecule_service.cpu * 1024
        memory       = var.compute.molecule_service.memory
        environment  = var.environment
        region       = var.aws_region
        log_group    = "/ecs/${var.environment}/molecule"
      })
    },
    worker = {
      name          = "${var.compute.worker_service.name}"
      cpu           = var.compute.worker_service.cpu * 1024
      memory        = var.compute.worker_service.memory
      container_definitions = templatefile("../../templates/container_definitions/worker.json.tpl", {
        name         = var.compute.worker_service.name
        image        = "#{AWS::AccountId}.dkr.ecr.${var.aws_region}.amazonaws.com/molecule-platform-staging-worker:latest"
        container_port = var.compute.worker_service.container_port
        host_port    = var.compute.worker_service.host_port
        cpu          = var.compute.worker_service.cpu * 1024
        memory       = var.compute.worker_service.memory
        environment  = var.environment
        region       = var.aws_region
        log_group    = "/ecs/${var.environment}/worker"
      })
    }
  }
  
  # ECS service configurations
  service_configs = {
    frontend = {
      name            = var.compute.frontend_service.name
      task_definition = "${var.compute.frontend_service.name}"
      desired_count   = var.compute.frontend_service.desired_count
      deployment_type = var.compute.frontend_service.deployment_type
      container_name  = var.compute.frontend_service.name
      container_port  = var.compute.frontend_service.container_port
      health_check_path = var.compute.frontend_service.health_check_path
      health_check_timeout = var.compute.frontend_service.health_check_timeout
      health_check_interval = var.compute.frontend_service.health_check_interval
    },
    api = {
      name            = var.compute.api_service.name
      task_definition = "${var.compute.api_service.name}"
      desired_count   = var.compute.api_service.desired_count
      deployment_type = var.compute.api_service.deployment_type
      container_name  = var.compute.api_service.name
      container_port  = var.compute.api_service.container_port
      health_check_path = var.compute.api_service.health_check_path
      health_check_timeout = var.compute.api_service.health_check_timeout
      health_check_interval = var.compute.api_service.health_check_interval
    },
    molecule = {
      name            = var.compute.molecule_service.name
      task_definition = "${var.compute.molecule_service.name}"
      desired_count   = var.compute.molecule_service.desired_count
      deployment_type = var.compute.molecule_service.deployment_type
      container_name  = var.compute.molecule_service.name
      container_port  = var.compute.molecule_service.container_port
      health_check_path = var.compute.molecule_service.health_check_path
      health_check_timeout = var.compute.molecule_service.health_check_timeout
      health_check_interval = var.compute.molecule_service.health_check_interval
    },
    worker = {
      name            = var.compute.worker_service.name
      task_definition = "${var.compute.worker_service.name}"
      desired_count   = var.compute.worker_service.desired_count
      deployment_type = var.compute.worker_service.deployment_type
      container_name  = var.compute.worker_service.name
      container_port  = var.compute.worker_service.container_port
      health_check_path = "/health"  # Default health check path for worker
      health_check_timeout = 5
      health_check_interval = 30
    }
  }
}

# =============================================================================
# Random String for Unique Resource Naming
# =============================================================================

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# =============================================================================
# Networking Module
# =============================================================================

module "networking" {
  source = "../../modules/networking"
  
  vpc_cidr               = var.networking.vpc_cidr
  public_subnet_cidrs    = var.networking.public_subnet_cidrs
  private_subnet_cidrs   = var.networking.private_subnet_cidrs
  availability_zones     = var.networking.availability_zones
  enable_nat_gateway     = var.networking.enable_nat_gateway
  enable_vpc_endpoints   = var.networking.enable_vpc_endpoints
  interface_endpoints    = var.networking.interface_endpoints
  enable_flow_logs       = var.networking.enable_flow_logs
  flow_log_retention     = var.networking.flow_log_retention
  
  environment = var.environment
  project_name = var.project_name
  tags = var.tags
}

# =============================================================================
# Security Module
# =============================================================================

module "security" {
  source = "../../modules/security"
  
  vpc_id                   = module.networking.vpc_id
  enable_waf               = var.security.enable_waf
  enable_guardduty         = var.security.enable_guardduty
  enable_cloudtrail        = var.security.enable_cloudtrail
  enable_config            = var.security.enable_config
  enable_key_rotation      = true
  kms_key_deletion_window  = var.security.kms_key_deletion_window
  
  cognito_user_pool_name   = var.security.cognito_user_pool_name
  cognito_identity_pool_name = local.cognito_identity_pool_name
  password_policy          = local.password_policy
  enable_mfa               = true  # Enable MFA for staging to test security
  
  callback_urls            = local.callback_urls
  logout_urls              = local.logout_urls
  s3_bucket_arns           = local.s3_bucket_arns
  
  environment  = var.environment
  project_name = var.project_name
  tags         = var.tags
}

# =============================================================================
# Storage Module
# =============================================================================

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
  
  kms_key_id               = module.security.kms_key_id
  
  environment  = var.environment
  project_name = var.project_name
  tags         = var.tags
}

# =============================================================================
# Database Module
# =============================================================================

module "database" {
  source = "../../modules/database"
  
  subnet_ids               = module.networking.private_subnet_ids
  security_group_ids       = local.database_security_group_ids
  
  # RDS PostgreSQL configuration
  instance_class           = var.database.rds_instance_class
  engine                   = var.database.rds_engine
  engine_version           = var.database.rds_engine_version
  allocated_storage        = var.database.rds_allocated_storage
  max_allocated_storage    = var.database.rds_max_allocated_storage
  multi_az                 = var.database.rds_multi_az
  backup_retention_period  = var.database.rds_backup_retention_period
  
  # Read replicas configuration
  create_read_replicas     = var.database.create_read_replicas
  read_replica_count       = var.database.read_replica_count
  
  # ElastiCache Redis configuration
  elasticache_node_type    = var.database.elasticache_node_type
  elasticache_engine_version = var.database.elasticache_engine_version
  
  # Encryption
  kms_key_id               = module.security.kms_key_id
  
  environment  = var.environment
  project_name = var.project_name
  tags         = var.tags
}

# =============================================================================
# Compute Module
# =============================================================================

module "compute" {
  source = "../../modules/compute"
  
  # Network configuration
  vpc_id                   = module.networking.vpc_id
  public_subnet_ids        = module.networking.public_subnet_ids
  private_subnet_ids       = module.networking.private_subnet_ids
  security_group_ids       = local.security_group_ids
  
  # ECS configuration
  cluster_name             = var.compute.ecs_cluster_name
  task_definitions         = local.task_definitions
  service_configs          = local.service_configs
  
  # Load balancer configuration
  alb_config               = var.compute.load_balancer_config
  
  # Auto-scaling configuration
  scaling_targets          = var.compute.auto_scaling_settings
  
  environment  = var.environment
  project_name = var.project_name
  tags         = var.tags
}

# =============================================================================
# Monitoring Module
# =============================================================================

module "monitoring" {
  source = "../../modules/monitoring"
  
  environment              = var.environment
  region                   = var.aws_region
  tags                     = var.tags
  
  # Monitoring configuration
  monitoring               = var.monitoring
  
  # Resources to monitor
  compute_outputs          = module.compute
  database_outputs         = module.database
  storage_outputs          = module.storage
}

# =============================================================================
# Outputs
# =============================================================================

output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "The IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "The IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

output "security_group_ids" {
  description = "The IDs of the security groups"
  value       = module.networking.security_group_ids
}

output "ecs_cluster_id" {
  description = "The ID of the ECS cluster"
  value       = module.compute.ecs_cluster_id
}

output "alb_dns_name" {
  description = "The DNS name of the ALB"
  value       = module.compute.alb_dns_name
}

output "rds_endpoint" {
  description = "The endpoint of the RDS instance"
  value       = module.database.rds_endpoint
}

output "elasticache_endpoint" {
  description = "The endpoint of the ElastiCache cluster"
  value       = module.database.elasticache_endpoint
}

output "s3_bucket_ids" {
  description = "The IDs of the S3 buckets"
  value       = module.storage.s3_bucket_ids
}

output "cognito_user_pool_id" {
  description = "The ID of the Cognito user pool"
  value       = module.security.cognito_user_pool_id
}

output "cognito_user_pool_client_id" {
  description = "The ID of the Cognito user pool client"
  value       = module.security.cognito_user_pool_client_id
}

output "kms_key_id" {
  description = "The ID of the KMS key"
  value       = module.security.kms_key_id
}

output "cloudwatch_dashboard_urls" {
  description = "The URLs of the CloudWatch dashboards"
  value       = module.monitoring.dashboard_urls
}