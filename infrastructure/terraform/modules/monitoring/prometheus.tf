# ----------------------------------------------------------------------------------------------------------------------
# Prometheus Monitoring Configuration
# ----------------------------------------------------------------------------------------------------------------------

# This Terraform file sets up Prometheus monitoring for the Molecular Data Management and CRO Integration Platform
# It configures an ECS service running Prometheus with appropriate scraping configurations for all system components

# ----------------------------------------------------------------------------------------------------------------------
# Local Variables
# ----------------------------------------------------------------------------------------------------------------------

locals {
  # Resource naming with environment prefix
  prometheus_name = "${var.environment}-prometheus"
  
  # Resource allocations
  prometheus_cpu    = 1024  # 1 vCPU
  prometheus_memory = 2048  # 2 GB RAM
  prometheus_port   = 9090  # Default Prometheus port
  
  # Storage configuration
  prometheus_data_dir = "/prometheus"
  
  # Tags for all Prometheus resources
  prometheus_tags = merge(var.tags, {
    Component = "Monitoring"
    Service   = "Prometheus"
  })
}

# ----------------------------------------------------------------------------------------------------------------------
# CloudWatch Log Group for Prometheus
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "prometheus" {
  count = var.monitoring.enable_prometheus ? 1 : 0
  
  name              = "/ecs/${local.prometheus_name}"
  retention_in_days = var.monitoring.log_retention_days
  
  tags = local.prometheus_tags
}

# ----------------------------------------------------------------------------------------------------------------------
# IAM Roles and Policies for Prometheus
# ----------------------------------------------------------------------------------------------------------------------

# Execution role for the ECS task
resource "aws_iam_role" "prometheus_execution" {
  count = var.monitoring.enable_prometheus ? 1 : 0
  
  name = "${local.prometheus_name}-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.prometheus_tags
}

# Task role for the Prometheus container
resource "aws_iam_role" "prometheus_task" {
  count = var.monitoring.enable_prometheus ? 1 : 0
  
  name = "${local.prometheus_name}-task-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.prometheus_tags
}

# Policy for ECS execution permissions
resource "aws_iam_policy" "prometheus_execution_policy" {
  count = var.monitoring.enable_prometheus ? 1 : 0
  
  name        = "${local.prometheus_name}-execution-policy"
  description = "Allows ECS tasks to pull images and write logs for Prometheus"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.prometheus[0].arn}:*"
      }
    ]
  })
  
  tags = local.prometheus_tags
}

# Policy for ECS service discovery
resource "aws_iam_policy" "prometheus_ecs_discovery" {
  count = var.monitoring.enable_prometheus ? 1 : 0
  
  name        = "${local.prometheus_name}-ecs-discovery-policy"
  description = "Allows Prometheus to discover ECS tasks"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:ListClusters",
          "ecs:ListServices",
          "ecs:ListTasks",
          "ecs:DescribeTaskDefinition",
          "ecs:DescribeTasks",
          "ecs:DescribeClusters",
          "ecs:DescribeServices"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = local.prometheus_tags
}

# Policy for CloudWatch metrics access
resource "aws_iam_policy" "prometheus_cloudwatch_metrics" {
  count = var.monitoring.enable_prometheus ? 1 : 0
  
  name        = "${local.prometheus_name}-cloudwatch-metrics-policy"
  description = "Allows Prometheus to get CloudWatch metrics"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:ListMetrics",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:GetMetricData"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = local.prometheus_tags
}

# Attach policies to roles
resource "aws_iam_role_policy_attachment" "prometheus_execution_policy_attachment" {
  count = var.monitoring.enable_prometheus ? 1 : 0
  
  role       = aws_iam_role.prometheus_execution[0].name
  policy_arn = aws_iam_policy.prometheus_execution_policy[0].arn
}

resource "aws_iam_role_policy_attachment" "prometheus_ecs_discovery_attachment" {
  count = var.monitoring.enable_prometheus ? 1 : 0
  
  role       = aws_iam_role.prometheus_task[0].name
  policy_arn = aws_iam_policy.prometheus_ecs_discovery[0].arn
}

resource "aws_iam_role_policy_attachment" "prometheus_cloudwatch_metrics_attachment" {
  count = var.monitoring.enable_prometheus ? 1 : 0
  
  role       = aws_iam_role.prometheus_task[0].name
  policy_arn = aws_iam_policy.prometheus_cloudwatch_metrics[0].arn
}

# ----------------------------------------------------------------------------------------------------------------------
# EFS File System for Prometheus Data
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_efs_file_system" "prometheus" {
  count = var.monitoring.enable_prometheus ? 1 : 0
  
  creation_token = "${local.prometheus_name}-data"
  
  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"
  
  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }
  
  tags = local.prometheus_tags
}

# Note: In a complete implementation, EFS mount targets would be created here,
# but they require VPC and subnet information that would need to be provided as inputs.

# ----------------------------------------------------------------------------------------------------------------------
# Security Group for Prometheus
# ----------------------------------------------------------------------------------------------------------------------

# Note: In a complete implementation, security groups would be created here,
# but they require VPC information that would need to be provided as inputs.

# ----------------------------------------------------------------------------------------------------------------------
# Prometheus Configuration
# ----------------------------------------------------------------------------------------------------------------------

data "template_file" "prometheus_config" {
  count = var.monitoring.enable_prometheus ? 1 : 0
  
  template = <<-EOF
  global:
    scrape_interval: ${var.monitoring.scrape_interval_seconds}s
    evaluation_interval: 15s
    external_labels:
      environment: ${var.environment}

  # Storage retention settings
  storage:
    tsdb:
      retention.time: ${var.monitoring.prometheus_retention_days * 24}h

  # Scrape configurations
  scrape_configs:
    # Self-monitoring
    - job_name: 'prometheus'
      static_configs:
        - targets: ['localhost:9090']

    # ECS services monitoring - Frontend
    - job_name: 'ecs-frontend'
      ecs_sd_configs:
        - region: ${var.region}
          cluster_arn: ${compute_outputs.cluster_id}
          service_name: ${compute_outputs.frontend_service_name}
      relabel_configs:
        - source_labels: [__meta_ecs_container_name]
          regex: .*frontend.*
          action: keep
        - source_labels: [__meta_ecs_container_name]
          target_label: container_name
        - source_labels: [__meta_ecs_cluster]
          target_label: cluster

    # ECS services monitoring - Backend
    - job_name: 'ecs-backend'
      ecs_sd_configs:
        - region: ${var.region}
          cluster_arn: ${compute_outputs.cluster_id}
          service_name: ${compute_outputs.backend_service_name}
      relabel_configs:
        - source_labels: [__meta_ecs_container_name]
          regex: .*backend.*
          action: keep
        - source_labels: [__meta_ecs_container_name]
          target_label: container_name
        - source_labels: [__meta_ecs_cluster]
          target_label: cluster

    # ECS services monitoring - Molecule Service
    - job_name: 'ecs-molecule'
      ecs_sd_configs:
        - region: ${var.region}
          cluster_arn: ${compute_outputs.cluster_id}
          service_name: ${compute_outputs.molecule_service_name}
      relabel_configs:
        - source_labels: [__meta_ecs_container_name]
          regex: .*molecule.*
          action: keep
        - source_labels: [__meta_ecs_container_name]
          target_label: container_name
        - source_labels: [__meta_ecs_cluster]
          target_label: cluster

    # ECS services monitoring - Worker
    - job_name: 'ecs-worker'
      ecs_sd_configs:
        - region: ${var.region}
          cluster_arn: ${compute_outputs.cluster_id}
          service_name: ${compute_outputs.worker_service_name}
      relabel_configs:
        - source_labels: [__meta_ecs_container_name]
          regex: .*worker.*
          action: keep
        - source_labels: [__meta_ecs_container_name]
          target_label: container_name
        - source_labels: [__meta_ecs_cluster]
          target_label: cluster

    # RDS monitoring
    - job_name: 'rds'
      static_configs:
        - targets: ['rds-exporter:9187']
      metrics_path: /metrics
      params:
        instance: ['${database_outputs.rds_instance_id}']

    # RDS Read Replicas monitoring
    - job_name: 'rds-replicas'
      static_configs:
        - targets: ['rds-exporter:9187']
      metrics_path: /metrics
      params:
        instance: ${jsonencode(database_outputs.rds_read_replica_ids)}

    # ElastiCache monitoring
    - job_name: 'redis'
      static_configs:
        - targets: ['redis-exporter:9121']
      metrics_path: /metrics
      params:
        instance: ['${database_outputs.elasticache_replication_group_id}']

    # Application-specific metrics - Performance metrics collection
    - job_name: 'api-performance'
      metrics_path: /metrics
      scrape_interval: 15s
      scheme: http
      static_configs:
        - targets:
          - 'frontend:8080'
          - 'backend:8000'
          - 'molecule-service:8000'
          labels:
            metrics_type: 'api_performance'
            
    # Business metrics collection
    - job_name: 'business-metrics'
      metrics_path: /metrics/business
      scrape_interval: 60s
      scheme: http
      static_configs:
        - targets:
          - 'molecule-service:8000'
          - 'worker:8000'
          labels:
            metrics_type: 'business'
            
    # Molecule processing metrics
    - job_name: 'molecule-processing'
      metrics_path: /metrics/processing
      scrape_interval: 30s
      scheme: http
      static_configs:
        - targets:
          - 'molecule-service:8000'
          labels:
            metrics_type: 'processing'
            
    # Infrastructure metrics
    - job_name: 'infrastructure'
      metrics_path: /metrics/infra
      scrape_interval: 30s
      scheme: http
      static_configs:
        - targets:
          - 'node-exporter:9100'
          labels:
            metrics_type: 'infrastructure'
            
    # OpenTelemetry collector for distributed tracing metrics
    - job_name: 'otel-collector'
      scrape_interval: 15s
      static_configs:
        - targets: ['otel-collector:8889']
  EOF
}

# ----------------------------------------------------------------------------------------------------------------------
# ECS Task Definition for Prometheus
# ----------------------------------------------------------------------------------------------------------------------

resource "aws_ecs_task_definition" "prometheus" {
  count = var.monitoring.enable_prometheus ? 1 : 0
  
  family                   = local.prometheus_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = local.prometheus_cpu
  memory                   = local.prometheus_memory
  execution_role_arn       = aws_iam_role.prometheus_execution[0].arn
  task_role_arn            = aws_iam_role.prometheus_task[0].arn
  
  container_definitions = jsonencode([
    {
      name      = "prometheus"
      image     = "prom/prometheus:${var.monitoring.prometheus_version}"
      essential = true
      
      portMappings = [
        {
          containerPort = local.prometheus_port
          hostPort      = local.prometheus_port
          protocol      = "tcp"
        }
      ]
      
      command = [
        "--config.file=/etc/prometheus/prometheus.yml",
        "--storage.tsdb.path=${local.prometheus_data_dir}",
        "--web.console.libraries=/usr/share/prometheus/console_libraries",
        "--web.console.templates=/usr/share/prometheus/consoles",
        "--web.enable-lifecycle",
        "--web.route-prefix=/prometheus"
      ]
      
      mountPoints = [
        {
          sourceVolume  = "prometheus-data"
          containerPath = local.prometheus_data_dir
          readOnly      = false
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.prometheus[0].name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "prometheus"
        }
      }
      
      # In production, this would be mounted as a file rather than an environment variable
      environment = [
        {
          name  = "PROMETHEUS_CONFIG_CONTENT"
          value = data.template_file.prometheus_config[0].rendered
        }
      ]
      
      healthCheck = {
        command     = ["CMD-SHELL", "wget -q --spider http://localhost:9090/-/healthy || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 30
      }
    }
  ])
  
  volume {
    name = "prometheus-data"
    
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.prometheus[0].id
      root_directory     = "/"
      transit_encryption = "ENABLED"
    }
  }
  
  tags = local.prometheus_tags
}

# Note: In a complete implementation, the following resources would also be created:
# 1. ECS Service for Prometheus
# 2. Load Balancer Target Group
# 3. Load Balancer Listener Rule
# These require additional inputs like VPC ID, subnet IDs, and ALB listener ARN.

# ----------------------------------------------------------------------------------------------------------------------
# Output Values
# ----------------------------------------------------------------------------------------------------------------------

output "prometheus_url" {
  description = "URL for accessing the Prometheus UI"
  value       = var.monitoring.enable_prometheus ? "/prometheus" : ""
}

output "prometheus_ecs_service_name" {
  description = "Name of the ECS service running Prometheus"
  value       = var.monitoring.enable_prometheus ? local.prometheus_name : ""
}

output "prometheus_log_group_name" {
  description = "Name of the CloudWatch log group for Prometheus logs"
  value       = var.monitoring.enable_prometheus ? aws_cloudwatch_log_group.prometheus[0].name : ""
}

output "prometheus_security_group_id" {
  description = "ID of the security group for Prometheus service"
  value       = var.monitoring.enable_prometheus ? "would-be-created-with-vpc-input" : ""
}

output "prometheus_efs_id" {
  description = "ID of the EFS file system for Prometheus data"
  value       = var.monitoring.enable_prometheus ? aws_efs_file_system.prometheus[0].id : ""
}