# Main Terraform configuration file for the Molecular Data Management and CRO Integration Platform
# This file orchestrates the deployment of all infrastructure components required for the platform.

terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  
  backend "s3" {
    # These values will be provided at init time or via environment variables
    # bucket         = "moleculeflow-terraform-state"
    # key            = "terraform/state/moleculeflow"
    # region         = "us-east-1"
    # dynamodb_table = "moleculeflow-terraform-locks"
    # encrypt        = true
  }
}

# Primary AWS Provider configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = local.common_tags
  }
}

# Secondary AWS Provider for disaster recovery region
provider "aws" {
  alias  = "dr_region"
  region = var.dr_region
  
  default_tags {
    tags = local.common_tags
  }
}

# Local variables for resource naming, tagging, and configuration
locals {
  # Environment naming and tagging
  environment = var.environment
  name_prefix = "${var.project_name}-${local.environment}"
  
  # Common tags for all resources
  common_tags = {
    Project     = var.project_name
    Environment = local.environment
    ManagedBy   = "terraform"
    Owner       = var.owner
    Application = "MoleculeFlow"
    Compliance  = "21CFR-Part11"
  }
  
  # Network configuration
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs
  
  # Security and compliance configuration
  enable_encryption = true
  enable_logging    = true
  
  # Database configuration
  db_instance_class = var.db_instance_class
  db_storage_size   = var.db_storage_size
  
  # Container configuration
  container_cpu    = var.container_cpu
  container_memory = var.container_memory
}

# VPC and Network Infrastructure
module "vpc" {
  source = "./modules/vpc"
  
  name_prefix         = local.name_prefix
  vpc_cidr            = local.vpc_cidr
  availability_zones  = local.availability_zones
  private_subnet_cidrs = local.private_subnet_cidrs
  public_subnet_cidrs  = local.public_subnet_cidrs
  database_subnet_cidrs = local.database_subnet_cidrs
  
  # Enable VPC endpoints for secure service access
  enable_s3_endpoint = true
  enable_dynamodb_endpoint = true
  
  tags = local.common_tags
}

# Security Groups
module "security_groups" {
  source = "./modules/security"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  
  # Allow traffic only from necessary sources with least privilege
  alb_ingress_cidr_blocks = var.allowed_ip_ranges
  
  tags = local.common_tags
}

# KMS Keys for encryption
module "kms" {
  source = "./modules/kms"
  
  name_prefix = local.name_prefix
  key_administrators = var.key_administrators
  key_users = var.key_users
  
  tags = local.common_tags
}

# Database - RDS PostgreSQL with Multi-AZ
module "database" {
  source = "./modules/database"
  
  name_prefix          = local.name_prefix
  db_subnet_group_name = module.vpc.database_subnet_group_name
  db_instance_class    = local.db_instance_class
  db_storage_size      = local.db_storage_size
  security_group_id    = module.security_groups.database_security_group_id
  kms_key_id           = module.kms.rds_key_id
  
  # High availability and security configurations
  engine_version       = "15.3"
  multi_az             = true
  storage_encrypted    = local.enable_encryption
  deletion_protection  = true
  backup_retention_period = 30
  enable_performance_insights = true
  
  # Database parameters for chemical structure support
  parameter_group_family = "postgres15"
  parameters = var.database_parameters
  
  tags = local.common_tags
}

# Redis ElastiCache for caching and queuing
module "redis" {
  source = "./modules/redis"
  
  name_prefix          = local.name_prefix
  subnet_group_name    = module.vpc.elasticache_subnet_group_name
  security_group_id    = module.security_groups.redis_security_group_id
  redis_node_type      = var.redis_node_type
  
  # High availability configuration
  redis_version        = "7.0"
  num_cache_nodes      = 3
  automatic_failover_enabled = true
  at_rest_encryption_enabled = local.enable_encryption
  transit_encryption_enabled = true
  
  tags = local.common_tags
}

# S3 Buckets for document and data storage
module "s3" {
  source = "./modules/s3"
  
  name_prefix       = local.name_prefix
  
  # Bucket configuration
  document_bucket_name = "${local.name_prefix}-documents"
  data_bucket_name = "${local.name_prefix}-data"
  logs_bucket_name = "${local.name_prefix}-logs"
  
  # Security and compliance
  enable_encryption = local.enable_encryption
  kms_key_id        = module.kms.s3_key_id
  block_public_access = true
  
  # Lifecycle rules for cost optimization
  lifecycle_rules   = var.s3_lifecycle_rules
  
  # CORS for frontend access
  cors_rules        = var.s3_cors_rules
  
  tags = local.common_tags
}

# S3 Cross-Region Replication for disaster recovery
module "s3_replication" {
  source = "./modules/s3_replication"
  
  providers = {
    aws.source = aws
    aws.destination = aws.dr_region
  }
  
  source_bucket      = module.s3.document_bucket_id
  destination_region = var.dr_region
  kms_key_id         = module.kms.s3_key_id
  
  tags = local.common_tags
  
  depends_on = [module.s3]
}

# AWS Cognito for authentication and authorization
module "cognito" {
  source = "./modules/cognito"
  
  name_prefix     = local.name_prefix
  user_pool_name  = "${local.name_prefix}-users"
  
  # Security configurations
  enable_mfa      = true
  mfa_configuration = "OPTIONAL"
  
  # Password policy compliant with 21 CFR Part 11
  password_policy = {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
    temporary_password_validity_days = 7
  }
  
  # Advanced security features
  advanced_security_mode = "ENFORCED"
  
  # Custom attributes for user roles and permissions
  schema_attributes = var.cognito_schema_attributes
  
  # App clients for different application components
  app_clients = var.cognito_app_clients
  
  tags = local.common_tags
}

# IAM Roles and Policies
module "iam" {
  source = "./modules/iam"
  
  name_prefix     = local.name_prefix
  
  # Resource ARNs for policy attachments
  s3_bucket_arns  = module.s3.bucket_arns
  kms_key_arns    = module.kms.key_arns
  
  # IAM roles for services
  create_ecs_execution_role = true
  create_ecs_task_role = true
  create_lambda_execution_role = true
  
  tags = local.common_tags
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.public_subnet_ids
  security_group_id  = module.security_groups.alb_security_group_id
  
  # HTTPS configuration
  ssl_certificate_arn = var.ssl_certificate_arn
  ssl_policy          = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  
  # WAF and logging
  enable_waf         = true
  enable_deletion_protection = true
  enable_access_logs = local.enable_logging
  access_logs_bucket = module.s3.logs_bucket_id
  
  tags = local.common_tags
}

# WAF Web ACL for application protection
module "waf" {
  source = "./modules/waf"
  
  name_prefix   = local.name_prefix
  alb_arn       = module.alb.alb_arn
  
  # WAF rules for OWASP Top 10 protection
  enable_sql_injection_protection = true
  enable_xss_protection = true
  enable_rate_limiting = true
  
  # IP blocking and allowlisting
  ip_block_list = var.ip_block_list
  ip_allow_list = var.ip_allow_list
  
  tags = local.common_tags
  
  depends_on = [module.alb]
}

# ECS Cluster and Services
module "ecs" {
  source = "./modules/ecs"
  
  name_prefix            = local.name_prefix
  vpc_id                 = module.vpc.vpc_id
  subnet_ids             = module.vpc.private_subnet_ids
  security_group_id      = module.security_groups.ecs_security_group_id
  
  # ECS cluster configuration
  cluster_name           = "${local.name_prefix}-cluster"
  capacity_providers     = ["FARGATE", "FARGATE_SPOT"]
  
  # IAM roles
  execution_role_arn     = module.iam.ecs_execution_role_arn
  task_role_arn          = module.iam.ecs_task_role_arn
  
  # Load balancer configuration
  load_balancer_arn      = module.alb.alb_arn
  target_group_arns      = module.alb.target_group_arns
  
  # Service definitions
  services = {
    frontend = {
      name          = "frontend"
      container_definitions = var.frontend_container_definition
      cpu           = local.container_cpu.frontend
      memory        = local.container_memory.frontend
      desired_count = var.desired_count.frontend
      min_capacity  = var.min_capacity.frontend
      max_capacity  = var.max_capacity.frontend
    },
    api = {
      name          = "api"
      container_definitions = var.api_container_definition
      cpu           = local.container_cpu.api
      memory        = local.container_memory.api
      desired_count = var.desired_count.api
      min_capacity  = var.min_capacity.api
      max_capacity  = var.max_capacity.api
    },
    molecule_service = {
      name          = "molecule-service"
      container_definitions = var.molecule_service_container_definition
      cpu           = local.container_cpu.molecule_service
      memory        = local.container_memory.molecule_service
      desired_count = var.desired_count.molecule_service
      min_capacity  = var.min_capacity.molecule_service
      max_capacity  = var.max_capacity.molecule_service
    },
    worker = {
      name          = "worker"
      container_definitions = var.worker_container_definition
      cpu           = local.container_cpu.worker
      memory        = local.container_memory.worker
      desired_count = var.desired_count.worker
      min_capacity  = var.min_capacity.worker
      max_capacity  = var.max_capacity.worker
    }
  }
  
  tags = local.common_tags
}

# SQS Queues for asynchronous messaging
module "sqs" {
  source = "./modules/sqs"
  
  name_prefix     = local.name_prefix
  
  # Queue configurations
  queues = {
    molecule_processing = {
      name          = "${local.name_prefix}-molecule-processing"
      fifo_queue    = false
      delay_seconds = 0
      visibility_timeout_seconds = 300
      message_retention_seconds  = 604800  # 7 days
      enable_dlq    = true
    },
    ai_prediction = {
      name          = "${local.name_prefix}-ai-prediction"
      fifo_queue    = false
      delay_seconds = 0
      visibility_timeout_seconds = 600
      message_retention_seconds  = 604800
      enable_dlq    = true
    },
    cro_communication = {
      name          = "${local.name_prefix}-cro-communication"
      fifo_queue    = true
      content_based_deduplication = true
      delay_seconds = 0
      visibility_timeout_seconds = 300
      message_retention_seconds  = 1209600  # 14 days
      enable_dlq    = true
    }
  }
  
  # KMS encryption
  kms_key_id     = module.kms.sqs_key_id
  
  tags = local.common_tags
}

# CloudWatch Logs, Metrics, and Alarms
module "monitoring" {
  source = "./modules/monitoring"
  
  name_prefix      = local.name_prefix
  
  # Log configuration
  enable_logging   = local.enable_logging
  log_retention    = var.log_retention_days
  
  # Resources to monitor
  rds_instance_id   = module.database.rds_instance_id
  ecs_cluster_name  = module.ecs.cluster_name
  ecs_service_names = module.ecs.service_names
  alb_arn           = module.alb.alb_arn
  
  # Alarm thresholds
  alarm_thresholds = {
    cpu_utilization_threshold = 80
    memory_utilization_threshold = 80
    database_connections_threshold = 80
    alb_5xx_threshold = 5
    api_latency_threshold = 500
  }
  
  # SNS for alerting
  create_sns_topic = true
  sns_topic_name   = "${local.name_prefix}-alarms"
  sns_subscription_emails = var.alert_emails
  
  tags = local.common_tags
}

# CloudTrail for audit logging
module "cloudtrail" {
  source = "./modules/cloudtrail"
  
  name_prefix     = local.name_prefix
  trail_name      = "${local.name_prefix}-audit-trail"
  s3_bucket_name  = module.s3.logs_bucket_id
  
  # Compliance configurations
  enable_logging  = local.enable_logging
  enable_log_file_validation = true
  include_global_service_events = true
  is_multi_region_trail = true
  
  # KMS encryption for logs
  kms_key_id      = module.kms.cloudtrail_key_id
  
  tags = local.common_tags
  
  depends_on = [module.s3]
}

# Route 53 for DNS management
module "route53" {
  source = "./modules/route53"
  
  domain_name   = var.domain_name
  create_zone   = var.create_route53_zone
  
  # DNS records
  records = [
    {
      name    = var.domain_name
      type    = "A"
      alias = {
        name                   = module.alb.alb_dns_name
        zone_id                = module.alb.alb_zone_id
        evaluate_target_health = true
      }
    },
    {
      name    = "*.${var.domain_name}"
      type    = "A"
      alias = {
        name                   = module.alb.alb_dns_name
        zone_id                = module.alb.alb_zone_id
        evaluate_target_health = true
      }
    }
  ]
  
  tags = local.common_tags
  
  depends_on = [module.alb]
}

# Lambda functions for serverless processing
module "lambda" {
  source = "./modules/lambda"
  
  name_prefix     = local.name_prefix
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids
  security_group_id = module.security_groups.lambda_security_group_id
  execution_role_arn = module.iam.lambda_execution_role_arn
  
  # Function definitions
  functions = var.lambda_functions
  
  # Environment variables
  environment_variables = {
    REGION = var.aws_region
    DOCUMENT_BUCKET = module.s3.document_bucket_id
    SQS_AI_PREDICTION_QUEUE = module.sqs.queue_urls["ai_prediction"]
  }
  
  # Lambda logging
  enable_logging = local.enable_logging
  log_retention = var.log_retention_days
  
  tags = local.common_tags
}

# API Gateway for API management
module "api_gateway" {
  source = "./modules/api_gateway"
  
  name_prefix     = local.name_prefix
  api_name        = "${local.name_prefix}-api"
  
  # API Gateway configuration
  endpoint_type   = "REGIONAL"
  
  # Security
  security_policy = "TLS_1_2"
  enable_waf      = true
  waf_acl_arn     = module.waf.waf_acl_arn
  
  # Throttling and quota
  throttling_rate_limit  = 1000
  throttling_burst_limit = 2000
  
  # Integration with Lambda functions
  lambda_function_arns = module.lambda.function_arns
  
  # Logging and monitoring
  enable_access_logs = local.enable_logging
  access_log_destination_arn = module.s3.logs_bucket_arn
  access_log_format = var.api_gateway_log_format
  
  tags = local.common_tags
  
  depends_on = [module.lambda, module.waf]
}

# Outputs for important resource information
output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "database_endpoint" {
  description = "The endpoint of the RDS database"
  value       = module.database.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "The endpoint of the Redis cluster"
  value       = module.redis.endpoint
  sensitive   = true
}

output "s3_bucket_names" {
  description = "The names of the created S3 buckets"
  value       = module.s3.bucket_names
}

output "cognito_user_pool_id" {
  description = "The ID of the Cognito User Pool"
  value       = module.cognito.user_pool_id
}

output "alb_dns_name" {
  description = "The DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "cloudtrail_arn" {
  description = "The ARN of the CloudTrail trail for auditing"
  value       = module.cloudtrail.cloudtrail_arn
}

output "api_gateway_invoke_url" {
  description = "The URL to invoke the API Gateway"
  value       = module.api_gateway.invoke_url
}

output "sqs_queue_urls" {
  description = "The URLs of the SQS queues"
  value       = module.sqs.queue_urls
}