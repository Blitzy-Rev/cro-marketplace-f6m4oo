# ---------------------------------------------------------------------------------------------------------------------
# Molecular Data Management and CRO Integration Platform - Production Environment
# ---------------------------------------------------------------------------------------------------------------------
# This Terraform configuration deploys the production environment infrastructure with high availability,
# security, and compliance features required for regulated pharmaceutical environments.
# ---------------------------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------------------------------
# Local variables for environment configuration
# ---------------------------------------------------------------------------------------------------------------------
locals {
  # Environment and naming
  environment  = "prod"
  project_name = "molecule-platform"
  
  # Common tags to apply to all resources
  common_tags = {
    Environment = local.environment
    Project     = local.project_name
    ManagedBy   = "Terraform"
    Application = "Molecular Data Management Platform"
    Compliance  = "21CFR-Part-11"
  }
  
  # Domain configuration
  domain_name = "moleculeflow.example.com"
  
  # AWS regions for primary deployment and disaster recovery
  primary_region   = "us-east-1"
  secondary_region = "us-west-2"
}

# ---------------------------------------------------------------------------------------------------------------------
# Networking Module - VPC, Subnets, Security Groups
# ---------------------------------------------------------------------------------------------------------------------
module "networking" {
  source = "../../../modules/networking"
  
  # VPC configuration
  vpc_cidr             = "10.0.0.0/16"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
  availability_zones   = ["${local.primary_region}a", "${local.primary_region}b", "${local.primary_region}c"]
  
  # Production-specific networking features
  enable_nat_gateway   = true   # Required for private subnet internet access
  enable_vpc_endpoints = true   # For secure AWS service access
  enable_flow_logs     = true   # For security monitoring and compliance
  flow_log_retention   = 90     # 90 days retention for compliance requirements
  
  # Production environments need access to these AWS services without internet exposure
  interface_endpoints = [
    "ecr.api", "ecr.dkr", "logs", "secretsmanager", "ssm",
    "sqs", "sns", "monitoring", "elasticache"
  ]
  
  # General configuration
  environment  = local.environment
  project_name = local.project_name
  tags         = local.common_tags
}

# ---------------------------------------------------------------------------------------------------------------------
# Compute Module - ECS Cluster, Services, Load Balancer
# ---------------------------------------------------------------------------------------------------------------------
module "compute" {
  source = "../../../modules/compute"
  
  # Network configuration
  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
  private_subnet_ids = module.networking.private_subnet_ids
  security_group_ids = {
    alb     = module.networking.security_group_alb
    app     = module.networking.security_group_app
    frontend = module.networking.security_group_app
    api     = module.networking.security_group_app
    molecule = module.networking.security_group_app
    worker  = module.networking.security_group_app
  }
  
  # Cluster configuration
  cluster_name = "${local.project_name}-cluster"
  cluster_settings = {
    "containerInsights" = "enabled" # Enable detailed monitoring
  }
  
  # Service configurations - Production requires higher instance counts for high availability
  service_configs = {
    frontend = {
      name                               = "frontend"
      desired_count                      = 3  # 3 instances for high availability
      deployment_maximum_percent         = 200
      deployment_minimum_healthy_percent = 100
      health_check_grace_period_seconds  = 60
      deployment_controller_type         = "ECS"
      enable_execute_command             = true
      launch_type                        = "FARGATE"
      scheduling_strategy                = "REPLICA"
      force_new_deployment               = true
      wait_for_steady_state              = true
      propagate_tags                     = "SERVICE"
      deployment_circuit_breaker = {
        enable   = true
        rollback = true
      }
    }
    api = {
      name                               = "api"
      desired_count                      = 3  # 3 instances for high availability
      deployment_maximum_percent         = 200
      deployment_minimum_healthy_percent = 100
      health_check_grace_period_seconds  = 60
      deployment_controller_type         = "CODE_DEPLOY"  # Blue/green deployments
      enable_execute_command             = true
      launch_type                        = "FARGATE"
      scheduling_strategy                = "REPLICA"
      force_new_deployment               = true
      wait_for_steady_state              = true
      propagate_tags                     = "SERVICE"
    }
    molecule = {
      name                               = "molecule"
      desired_count                      = 3  # 3 instances for high availability
      deployment_maximum_percent         = 200
      deployment_minimum_healthy_percent = 100
      health_check_grace_period_seconds  = 60
      deployment_controller_type         = "CODE_DEPLOY"  # Blue/green deployments
      enable_execute_command             = true
      launch_type                        = "FARGATE"
      scheduling_strategy                = "REPLICA"
      force_new_deployment               = true
      wait_for_steady_state              = true
      propagate_tags                     = "SERVICE"
    }
    worker = {
      name                               = "worker"
      desired_count                      = 3  # 3 instances for high availability
      deployment_maximum_percent         = 200
      deployment_minimum_healthy_percent = 100
      health_check_grace_period_seconds  = 30
      deployment_controller_type         = "ECS"
      enable_execute_command             = true
      launch_type                        = "FARGATE"
      scheduling_strategy                = "REPLICA"
      force_new_deployment               = true
      wait_for_steady_state              = true
      propagate_tags                     = "SERVICE"
      deployment_circuit_breaker = {
        enable   = true
        rollback = true
      }
    }
  }
  
  # Task definitions with appropriate CPU and memory allocations
  task_definitions = {
    frontend = {
      cpu                      = "512"   # 0.5 vCPU
      memory                   = "1024"  # 1 GB RAM
      requires_compatibilities = ["FARGATE"]
      network_mode             = "awsvpc"
      execution_role_arn       = "arn:aws:iam::123456789012:role/ecsTaskExecutionRole" # Replace with actual role ARN
      task_role_arn            = "arn:aws:iam::123456789012:role/ecsTaskRole"         # Replace with actual role ARN
      container_definitions    = file("../../../container-definitions/frontend-prod.json")
      ephemeral_storage        = 20  # 20 GB storage
      volumes                  = []
    }
    api = {
      cpu                      = "1024"  # 1 vCPU
      memory                   = "2048"  # 2 GB RAM
      requires_compatibilities = ["FARGATE"]
      network_mode             = "awsvpc"
      execution_role_arn       = "arn:aws:iam::123456789012:role/ecsTaskExecutionRole" # Replace with actual role ARN
      task_role_arn            = "arn:aws:iam::123456789012:role/ecsTaskRole"         # Replace with actual role ARN
      container_definitions    = file("../../../container-definitions/api-prod.json")
      ephemeral_storage        = 20  # 20 GB storage
      volumes                  = []
    }
    molecule = {
      cpu                      = "2048"  # 2 vCPU
      memory                   = "4096"  # 4 GB RAM
      requires_compatibilities = ["FARGATE"]
      network_mode             = "awsvpc"
      execution_role_arn       = "arn:aws:iam::123456789012:role/ecsTaskExecutionRole" # Replace with actual role ARN
      task_role_arn            = "arn:aws:iam::123456789012:role/ecsTaskRole"         # Replace with actual role ARN
      container_definitions    = file("../../../container-definitions/molecule-prod.json")
      ephemeral_storage        = 50  # 50 GB storage for molecular data
      volumes                  = []
    }
    worker = {
      cpu                      = "2048"  # 2 vCPU
      memory                   = "8192"  # 8 GB RAM
      requires_compatibilities = ["FARGATE"]
      network_mode             = "awsvpc"
      execution_role_arn       = "arn:aws:iam::123456789012:role/ecsTaskExecutionRole" # Replace with actual role ARN
      task_role_arn            = "arn:aws:iam::123456789012:role/ecsTaskRole"         # Replace with actual role ARN
      container_definitions    = file("../../../container-definitions/worker-prod.json")
      ephemeral_storage        = 50  # 50 GB storage for batch processing
      volumes                  = []
    }
  }
  
  # Load balancer configuration
  alb_config = {
    name                             = "${local.project_name}-alb"
    internal                         = false
    load_balancer_type               = "application"
    enable_deletion_protection       = true  # Prevent accidental deletion in production
    idle_timeout                     = 60
    enable_http2                     = true
    enable_cross_zone_load_balancing = true
    access_logs = {
      enabled = true
      bucket  = "${local.project_name}-${local.environment}-logs"
      prefix  = "alb-logs"
    }
  }
  
  # Target group configuration for services
  target_group_configs = {
    frontend = {
      port                 = 80
      protocol             = "HTTP"
      target_type          = "ip"
      deregistration_delay = 300
      slow_start           = 30
      health_check = {
        enabled             = true
        path                = "/"
        port                = "traffic-port"
        protocol            = "HTTP"
        healthy_threshold   = 3
        unhealthy_threshold = 3
        timeout             = 5
        interval            = 30
        matcher             = "200-299"
      }
      stickiness = {
        enabled         = false
        type            = "lb_cookie"
        cookie_duration = 86400
      }
    }
    api = {
      port                 = 8000
      protocol             = "HTTP"
      target_type          = "ip"
      deregistration_delay = 300
      slow_start           = 30
      health_check = {
        enabled             = true
        path                = "/api/health"
        port                = "traffic-port"
        protocol            = "HTTP"
        healthy_threshold   = 3
        unhealthy_threshold = 3
        timeout             = 5
        interval            = 30
        matcher             = "200-299"
      }
      stickiness = {
        enabled         = false
        type            = "lb_cookie"
        cookie_duration = 86400
      }
    }
    molecule = {
      port                 = 8000
      protocol             = "HTTP"
      target_type          = "ip"
      deregistration_delay = 300
      slow_start           = 30
      health_check = {
        enabled             = true
        path                = "/molecules/health"
        port                = "traffic-port"
        protocol            = "HTTP"
        healthy_threshold   = 3
        unhealthy_threshold = 3
        timeout             = 5
        interval            = 30
        matcher             = "200-299"
      }
      stickiness = {
        enabled         = false
        type            = "lb_cookie"
        cookie_duration = 86400
      }
    }
  }
  
  # HTTPS Listener with appropriate routing rules
  listener_configs = {
    http = {
      port     = 80
      protocol = "HTTP"
      default_action = {
        type = "redirect"
        redirect = {
          port        = "443"
          protocol    = "HTTPS"
          status_code = "HTTP_301"
        }
      }
    }
    https = {
      port            = 443
      protocol        = "HTTPS"
      ssl_policy      = "ELBSecurityPolicy-TLS-1-2-2017-01"
      certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/abcdef-1234-5678-abcd-123456789012" # Replace with actual certificate ARN
      default_action = {
        type             = "forward"
        target_group_key = "frontend"
      }
      rules = [
        {
          priority = 100
          conditions = [
            {
              path_pattern = ["/api/*"]
            }
          ]
          actions = [
            {
              type             = "forward"
              target_group_key = "api"
            }
          ]
        },
        {
          priority = 200
          conditions = [
            {
              path_pattern = ["/molecules/*"]
            }
          ]
          actions = [
            {
              type             = "forward"
              target_group_key = "molecule"
            }
          ]
        }
      ]
    }
  }
  
  # Auto-scaling configuration - Production has higher minimums
  scaling_targets = {
    frontend = {
      min_capacity = 3
      max_capacity = 10
    }
    api = {
      min_capacity = 3
      max_capacity = 20
    }
    molecule = {
      min_capacity = 3
      max_capacity = 20
    }
    worker = {
      min_capacity = 3
      max_capacity = 50
    }
  }
  
  # Auto-scaling policies with appropriate triggers
  scaling_policies = {
    frontend = {
      policy_type            = "TargetTrackingScaling"
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
      target_value           = 70
      scale_in_cooldown      = 300
      scale_out_cooldown     = 180
      disable_scale_in       = false
      scheduled_actions = [
        {
          name         = "business-hours-scale-up"
          schedule     = "cron(0 8 ? * MON-FRI *)"
          min_capacity = 5
          max_capacity = 10
        },
        {
          name         = "after-hours-scale-down"
          schedule     = "cron(0 18 ? * MON-FRI *)"
          min_capacity = 3
          max_capacity = 5
        }
      ]
    }
    api = {
      policy_type            = "TargetTrackingScaling"
      predefined_metric_type = "ALBRequestCountPerTarget"
      target_value           = 1000
      scale_in_cooldown      = 300
      scale_out_cooldown     = 180
      disable_scale_in       = false
    }
    molecule = {
      policy_type            = "TargetTrackingScaling"
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
      target_value           = 60
      scale_in_cooldown      = 300
      scale_out_cooldown     = 180
      disable_scale_in       = false
    }
    worker = {
      policy_type            = "TargetTrackingScaling"
      predefined_metric_type = "SQSNumberOfMessagesVisible"
      target_value           = 100
      scale_in_cooldown      = 300
      scale_out_cooldown     = 180
      disable_scale_in       = false
      scheduled_actions = [
        {
          name         = "batch-processing-scale-up"
          schedule     = "cron(0 2 * * ? *)"
          min_capacity = 10
          max_capacity = 50
        }
      ]
    }
  }
  
  # General configuration
  environment  = local.environment
  project_name = local.project_name
  tags         = local.common_tags
}

# ---------------------------------------------------------------------------------------------------------------------
# Database Module - RDS PostgreSQL and ElastiCache Redis
# ---------------------------------------------------------------------------------------------------------------------
module "database" {
  source = "../../../modules/database"
  
  # Network configuration
  subnet_ids       = module.networking.private_subnet_ids
  security_group_ids = [module.networking.security_group_db, module.networking.security_group_redis]
  
  # RDS PostgreSQL Configuration - Production grade
  rds_instance_class         = "db.r5.2xlarge"  # High-performance instance
  rds_engine                 = "postgres"
  rds_engine_version         = "15.0"
  rds_allocated_storage      = 500  # 500 GB initial storage
  rds_max_allocated_storage  = 2000  # 2 TB max storage
  rds_multi_az               = true  # Multi-AZ for high availability
  rds_backup_retention_period = 30  # 30 days of backups
  
  # Read replicas for scaling read operations
  create_read_replicas = true
  read_replica_count   = 2  # Two read replicas for production
  
  # ElastiCache Redis Configuration
  elasticache_node_type      = "cache.m5.large"
  elasticache_engine_version = "7.0"
  elasticache_parameter_group_name = "default.redis7"
  
  # General configuration
  environment  = local.environment
  project_name = local.project_name
  tags         = local.common_tags
}

# ---------------------------------------------------------------------------------------------------------------------
# Security Module - WAF, GuardDuty, CloudTrail, and IAM
# ---------------------------------------------------------------------------------------------------------------------
module "security" {
  source = "../../../modules/security"
  
  # VPC ID for security groups
  vpc_id = module.networking.vpc_id
  
  # Security features - all enabled for production
  enable_waf          = true
  enable_guardduty    = true
  enable_cloudtrail   = true
  enable_config       = true
  
  # KMS configuration
  kms_key_deletion_window = 30  # 30 day waiting period (maximum)
  
  # Cognito configuration 
  cognito_user_pool_name     = "${local.project_name}-users"
  cognito_identity_pool_name = "${local.project_name}-identity"
  
  # Password policy for 21 CFR Part 11 compliance
  password_policy = {
    minimum_length                   = 12
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }
  
  # MFA is required for production
  enable_mfa = true
  
  # General configuration
  environment  = local.environment
  project_name = local.project_name
  tags         = local.common_tags
}

# ---------------------------------------------------------------------------------------------------------------------
# Monitoring Module - CloudWatch Dashboards, Alarms, Logs
# ---------------------------------------------------------------------------------------------------------------------
module "monitoring" {
  source = "../../../modules/monitoring"
  
  # Region
  region = local.primary_region
  
  # Monitoring configuration
  monitoring = {
    # CloudWatch settings
    alarm_email                = "alerts@example.com"  # Replace with actual email
    dashboard_name_prefix      = local.project_name
    log_retention_days         = 90  # 90 days for production compliance
    enable_detailed_monitoring = true
    metric_namespace           = "MoleculePlatform"
    alarm_evaluation_periods   = 3
    alarm_period_seconds       = 60
    
    # Advanced monitoring (if used)
    enable_prometheus          = true
    prometheus_version         = "2.45.0"
    prometheus_retention_days  = 15
    scrape_interval_seconds    = 30
    
    enable_grafana             = true
    grafana_version            = "9.5.1"
    grafana_admin_password     = "ChangeMe123!"  # Use secrets manager in real production
    
    enable_alertmanager        = true
    alertmanager_version       = "0.25.0"
    slack_webhook_url          = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"  # Replace with actual webhook
    pagerduty_service_key      = "00000000000000000000000000000000"  # Replace with actual key
  }
  
  # Module dependencies - these outputs come from other modules
  compute_outputs = {
    cluster_id              = module.compute.cluster_id
    frontend_service_name   = module.compute.frontend_service_name
    backend_service_name    = module.compute.backend_service_name
    molecule_service_name   = module.compute.molecule_service_name
    worker_service_name     = module.compute.worker_service_name
    alb_arn                 = module.compute.alb_arn
    cloudwatch_log_groups   = module.compute.cloudwatch_log_groups
  }
  
  database_outputs = {
    rds_instance_id              = module.database.rds_instance_id
    rds_read_replica_ids         = module.database.rds_read_replica_ids
    elasticache_replication_group_id = module.database.elasticache_replication_group_id
  }
  
  storage_outputs = {
    document_bucket_id = "${local.project_name}-${local.environment}-documents"
    csv_bucket_id      = "${local.project_name}-${local.environment}-csv"
    results_bucket_id  = "${local.project_name}-${local.environment}-results"
    backup_bucket_id   = "${local.project_name}-${local.environment}-backups"
  }
  
  # General configuration
  environment = local.environment
  tags        = local.common_tags
}

# ---------------------------------------------------------------------------------------------------------------------
# Route 53 DNS Configuration
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_route53_record" "app" {
  zone_id = "Z1234567890ABC"  # Replace with actual hosted zone ID
  name    = local.domain_name
  type    = "A"
  
  alias {
    name                   = module.compute.alb_dns_name
    zone_id                = module.compute.alb_zone_id
    evaluate_target_health = true
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------------------------------------------------
output "vpc_id" {
  description = "ID of the VPC created for the production environment"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs created for the production environment"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of private subnet IDs created for the production environment"
  value       = module.networking.private_subnet_ids
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer for the production environment"
  value       = module.compute.alb_dns_name
}

output "alb_zone_id" {
  description = "Route 53 zone ID of the Application Load Balancer for the production environment"
  value       = module.compute.alb_zone_id
}

output "rds_endpoint" {
  description = "Endpoint of the RDS PostgreSQL instance for the production environment"
  value       = module.database.rds_instance_endpoint
}

output "elasticache_endpoint" {
  description = "Endpoint of the ElastiCache Redis cluster for the production environment"
  value       = module.database.elasticache_endpoint
}

output "cognito_user_pool_id" {
  description = "ID of the Cognito user pool for the production environment"
  value       = module.security.cognito_user_pool_id
}

output "cognito_identity_pool_id" {
  description = "ID of the Cognito identity pool for the production environment"
  value       = module.security.cognito_identity_pool_id
}

output "kms_key_id" {
  description = "ID of the KMS key for encryption in the production environment"
  value       = module.security.kms_key_id
}

output "dashboard_url" {
  description = "URL of the CloudWatch dashboard for the production environment"
  value       = module.monitoring.dashboard_urls.system_overview
}

output "alarm_topic_arn" {
  description = "ARN of the SNS topic for CloudWatch alarms in the production environment"
  value       = module.monitoring.alarm_topic_arn
}

output "app_domain" {
  description = "Domain name of the application in the production environment"
  value       = aws_route53_record.app.fqdn
}