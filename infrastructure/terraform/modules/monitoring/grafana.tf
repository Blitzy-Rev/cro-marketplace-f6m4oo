# Grafana configuration for Molecular Data Management and CRO Integration Platform

locals {
  name_prefix = "${var.environment}-grafana"
  
  grafana_tags = merge(var.tags, {
    Component = "Monitoring"
    Service   = "Grafana"
  })
  
  # Grafana container configuration
  grafana_container_port = 3000
  grafana_cpu            = 1024  # 1 vCPU
  grafana_memory         = 2048  # 2 GB
  
  # Dashboard paths
  system_health_dashboard_path     = "/grafana/d/system-health"
  molecule_processing_dashboard_path = "/grafana/d/molecule-processing"
  cro_integration_dashboard_path   = "/grafana/d/cro-integration"
  
  # EFS mount path for Grafana data
  grafana_data_dir = "/var/lib/grafana"
}

# IAM Roles and Policies for Grafana

# Execution role for ECS
resource "aws_iam_role" "grafana_execution_role" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  name = "${local.name_prefix}-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
  
  tags = local.grafana_tags
}

# Task role for Grafana to access AWS resources
resource "aws_iam_role" "grafana_task_role" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  name = "${local.name_prefix}-task-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
  
  tags = local.grafana_tags
}

# Policy for CloudWatch metrics access
resource "aws_iam_policy" "grafana_cloudwatch_policy" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  name        = "${local.name_prefix}-cloudwatch-policy"
  description = "Policy for Grafana to access CloudWatch metrics"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "cloudwatch:DescribeAlarmsForMetric",
          "cloudwatch:DescribeAlarmHistory",
          "cloudwatch:DescribeAlarms",
          "cloudwatch:ListMetrics",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:GetMetricData"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
  
  tags = local.grafana_tags
}

# Policy for ECS task execution
resource "aws_iam_policy" "grafana_execution_policy" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  name        = "${local.name_prefix}-execution-policy"
  description = "Policy for Grafana ECS task execution"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ssm:GetParameters",
          "secretsmanager:GetSecretValue"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
  
  tags = local.grafana_tags
}

# Policy for Prometheus access
resource "aws_iam_policy" "grafana_prometheus_policy" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  name        = "${local.name_prefix}-prometheus-policy"
  description = "Policy for Grafana to access Prometheus"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "aps:QueryMetrics",
          "aps:GetSeries",
          "aps:GetLabels",
          "aps:GetMetricMetadata"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
  
  tags = local.grafana_tags
}

# Attach policies to roles
resource "aws_iam_role_policy_attachment" "grafana_cloudwatch_attachment" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  role       = aws_iam_role.grafana_task_role[0].name
  policy_arn = aws_iam_policy.grafana_cloudwatch_policy[0].arn
}

resource "aws_iam_role_policy_attachment" "grafana_prometheus_attachment" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  role       = aws_iam_role.grafana_task_role[0].name
  policy_arn = aws_iam_policy.grafana_prometheus_policy[0].arn
}

resource "aws_iam_role_policy_attachment" "grafana_execution_attachment" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  role       = aws_iam_role.grafana_execution_role[0].name
  policy_arn = aws_iam_policy.grafana_execution_policy[0].arn
}

# Security Group for Grafana
resource "aws_security_group" "grafana_sg" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  name        = "${local.name_prefix}-sg"
  description = "Security group for Grafana ECS service"
  vpc_id      = data.aws_ecs_cluster.main.vpc_id

  ingress {
    description     = "Grafana UI"
    from_port       = local.grafana_container_port
    to_port         = local.grafana_container_port
    protocol        = "tcp"
    security_groups = [data.aws_lb.alb.security_groups[0]]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.grafana_tags
}

# Fetch cluster and load balancer information
data "aws_ecs_cluster" "main" {
  cluster_name = var.compute_outputs.cluster_id
}

data "aws_lb" "alb" {
  arn = data.aws_ecs_cluster.main.load_balancer_arns[0]
}

data "aws_lb_listener" "https" {
  load_balancer_arn = data.aws_lb.alb.arn
  port              = 443
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_ecs_cluster.main.vpc_id]
  }
  filter {
    name   = "tag:Name"
    values = ["*private*"]
  }
}

# EFS File System for Grafana data persistence
resource "aws_efs_file_system" "grafana_data" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  creation_token = "${local.name_prefix}-data"
  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"
  
  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }
  
  tags = local.grafana_tags
}

# EFS Security Group
resource "aws_security_group" "efs_sg" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  name        = "${local.name_prefix}-efs-sg"
  description = "Security group for Grafana EFS mount points"
  vpc_id      = data.aws_ecs_cluster.main.vpc_id

  ingress {
    description     = "NFS from Grafana"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.grafana_sg[0].id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.grafana_tags
}

# EFS Mount Targets in each subnet
resource "aws_efs_mount_target" "grafana_mount_target" {
  count = var.monitoring.enable_grafana ? length(data.aws_subnets.private.ids) : 0
  
  file_system_id = aws_efs_file_system.grafana_data[0].id
  subnet_id      = data.aws_subnets.private.ids[count.index]
  security_groups = [aws_security_group.efs_sg[0].id]
}

# CloudWatch Log Group for Grafana
resource "aws_cloudwatch_log_group" "grafana_logs" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = var.monitoring.log_retention_days
  
  tags = local.grafana_tags
}

# ALB Target Group for Grafana
resource "aws_lb_target_group" "grafana" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  name        = "${local.name_prefix}-tg"
  port        = local.grafana_container_port
  protocol    = "HTTP"
  vpc_id      = data.aws_ecs_cluster.main.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    interval            = 30
    path                = "/api/health"
    port                = "traffic-port"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    matcher             = "200"
  }
  
  tags = local.grafana_tags
}

# ALB Listener Rule for Grafana
resource "aws_lb_listener_rule" "grafana" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  listener_arn = data.aws_lb_listener.https.arn
  priority     = 100
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.grafana[0].arn
  }
  
  condition {
    path_pattern {
      values = ["/grafana*"]
    }
  }
  
  tags = local.grafana_tags
}

# Store Grafana admin password in SSM Parameter Store
resource "aws_ssm_parameter" "grafana_admin_password" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  name        = "/${var.environment}/grafana/admin_password"
  description = "Grafana admin password"
  type        = "SecureString"
  value       = var.monitoring.grafana_admin_password
  
  tags = local.grafana_tags
}

# Grafana Container Definition
locals {
  grafana_container_definition = var.monitoring.enable_grafana ? jsonencode([
    {
      name      = "grafana"
      image     = "grafana/grafana:${var.monitoring.grafana_version}"
      essential = true
      
      portMappings = [
        {
          containerPort = local.grafana_container_port
          hostPort      = local.grafana_container_port
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "GF_SERVER_ROOT_URL"
          value = "%(protocol)s://%(domain)s/grafana"
        },
        {
          name  = "GF_SERVER_SERVE_FROM_SUB_PATH"
          value = "true"
        },
        {
          name  = "GF_SECURITY_ADMIN_USER"
          value = "admin"
        },
        {
          name  = "GF_INSTALL_PLUGINS"
          value = "grafana-piechart-panel,grafana-worldmap-panel,grafana-clock-panel,grafana-cloudwatch-datasource"
        },
        {
          name  = "GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH"
          value = "/etc/grafana/dashboards/system_health.json"
        },
        {
          name  = "GF_PATHS_DATA"
          value = local.grafana_data_dir
        },
        {
          name  = "GF_PATHS_PROVISIONING"
          value = "/etc/grafana/provisioning"
        },
        {
          name  = "GF_AUTH_DISABLE_LOGIN_FORM"
          value = "false"
        },
        {
          name  = "GF_AUTH_ANONYMOUS_ENABLED"
          value = "false"
        },
        {
          name  = "GF_FEATURE_TOGGLES_ENABLE"
          value = "transformations newPanelChromeUI"
        },
        {
          name  = "AWS_REGION"
          value = var.region
        }
      ]
      
      secrets = [
        {
          name      = "GF_SECURITY_ADMIN_PASSWORD"
          valueFrom = aws_ssm_parameter.grafana_admin_password[0].arn
        }
      ]
      
      mountPoints = [
        {
          sourceVolume  = "grafana-data"
          containerPath = local.grafana_data_dir
          readOnly      = false
        },
        {
          sourceVolume  = "grafana-provisioning"
          containerPath = "/etc/grafana/provisioning"
          readOnly      = false
        },
        {
          sourceVolume  = "grafana-dashboards"
          containerPath = "/etc/grafana/dashboards"
          readOnly      = false
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.grafana_logs[0].name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "grafana"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "wget -q --spider http://localhost:${local.grafana_container_port}/api/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ]) : "[]"
  
  # Grafana provisioning files
  datasources_yaml = <<-EOT
apiVersion: 1
datasources:
  - name: CloudWatch
    type: cloudwatch
    access: proxy
    jsonData:
      authType: default
      defaultRegion: ${var.region}
    version: 1
    editable: false

  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus.${var.environment}:9090
    isDefault: true
    version: 1
    editable: false
EOT

  dashboards_yaml = <<-EOT
apiVersion: 1
providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: true
    updateIntervalSeconds: 30
    allowUiUpdates: false
    options:
      path: /etc/grafana/dashboards
EOT

  system_health_dashboard = <<-EOT
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": 1,
  "links": [],
  "panels": [
    {
      "collapsed": false,
      "datasource": null,
      "gridPos": {
        "h": 1,
        "w": 24,
        "x": 0,
        "y": 0
      },
      "id": 12,
      "panels": [],
      "title": "System Status",
      "type": "row"
    },
    {
      "datasource": "CloudWatch",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "percent"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 0,
        "y": 1
      },
      "id": 2,
      "options": {
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "showThresholdLabels": false,
        "showThresholdMarkers": true,
        "text": {}
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "alias": "",
          "dimensions": {
            "ClusterName": "${var.compute_outputs.cluster_id}"
          },
          "expression": "",
          "id": "",
          "matchExact": true,
          "metricName": "CPUUtilization",
          "namespace": "AWS/ECS",
          "period": "",
          "refId": "A",
          "region": "${var.region}",
          "statistic": "Average"
        }
      ],
      "title": "ECS CPU Utilization",
      "type": "gauge"
    },
    {
      "datasource": "CloudWatch",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "percent"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 6,
        "y": 1
      },
      "id": 4,
      "options": {
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "showThresholdLabels": false,
        "showThresholdMarkers": true,
        "text": {}
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "alias": "",
          "dimensions": {
            "ClusterName": "${var.compute_outputs.cluster_id}"
          },
          "expression": "",
          "id": "",
          "matchExact": true,
          "metricName": "MemoryUtilization",
          "namespace": "AWS/ECS",
          "period": "",
          "refId": "A",
          "region": "${var.region}",
          "statistic": "Average"
        }
      ],
      "title": "ECS Memory Utilization",
      "type": "gauge"
    },
    {
      "datasource": "CloudWatch",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "percent"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 12,
        "y": 1
      },
      "id": 6,
      "options": {
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "showThresholdLabels": false,
        "showThresholdMarkers": true,
        "text": {}
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "alias": "",
          "dimensions": {
            "DBInstanceIdentifier": "${var.database_outputs.rds_instance_id}"
          },
          "expression": "",
          "id": "",
          "matchExact": true,
          "metricName": "CPUUtilization",
          "namespace": "AWS/RDS",
          "period": "",
          "refId": "A",
          "region": "${var.region}",
          "statistic": "Average"
        }
      ],
      "title": "RDS CPU Utilization",
      "type": "gauge"
    },
    {
      "datasource": "CloudWatch",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          },
          "unit": "percent"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 18,
        "y": 1
      },
      "id": 8,
      "options": {
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "showThresholdLabels": false,
        "showThresholdMarkers": true,
        "text": {}
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "alias": "",
          "dimensions": {
            "CacheClusterId": "${var.database_outputs.elasticache_replication_group_id}"
          },
          "expression": "",
          "id": "",
          "matchExact": true,
          "metricName": "CPUUtilization",
          "namespace": "AWS/ElastiCache",
          "period": "",
          "refId": "A",
          "region": "${var.region}",
          "statistic": "Average"
        }
      ],
      "title": "ElastiCache CPU Utilization",
      "type": "gauge"
    },
    {
      "collapsed": false,
      "datasource": null,
      "gridPos": {
        "h": 1,
        "w": 24,
        "x": 0,
        "y": 9
      },
      "id": 10,
      "panels": [],
      "title": "Service Performance",
      "type": "row"
    },
    {
      "datasource": "CloudWatch",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true,
            "stacking": {
              "group": "A",
              "mode": "normal"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 10
      },
      "id": 14,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "alias": "{{ServiceName}}",
          "dimensions": {
            "ClusterName": "${var.compute_outputs.cluster_id}",
            "ServiceName": "${var.compute_outputs.frontend_service_name}"
          },
          "expression": "",
          "id": "",
          "matchExact": true,
          "metricName": "CPUUtilization",
          "namespace": "AWS/ECS",
          "period": "",
          "refId": "A",
          "region": "${var.region}",
          "statistic": "Average"
        },
        {
          "alias": "{{ServiceName}}",
          "dimensions": {
            "ClusterName": "${var.compute_outputs.cluster_id}",
            "ServiceName": "${var.compute_outputs.backend_service_name}"
          },
          "expression": "",
          "id": "",
          "matchExact": true,
          "metricName": "CPUUtilization",
          "namespace": "AWS/ECS",
          "period": "",
          "refId": "B",
          "region": "${var.region}",
          "statistic": "Average"
        },
        {
          "alias": "{{ServiceName}}",
          "dimensions": {
            "ClusterName": "${var.compute_outputs.cluster_id}",
            "ServiceName": "${var.compute_outputs.molecule_service_name}"
          },
          "expression": "",
          "id": "",
          "matchExact": true,
          "metricName": "CPUUtilization",
          "namespace": "AWS/ECS",
          "period": "",
          "refId": "C",
          "region": "${var.region}",
          "statistic": "Average"
        },
        {
          "alias": "{{ServiceName}}",
          "dimensions": {
            "ClusterName": "${var.compute_outputs.cluster_id}",
            "ServiceName": "${var.compute_outputs.worker_service_name}"
          },
          "expression": "",
          "id": "",
          "matchExact": true,
          "metricName": "CPUUtilization",
          "namespace": "AWS/ECS",
          "period": "",
          "refId": "D",
          "region": "${var.region}",
          "statistic": "Average"
        }
      ],
      "title": "CPU Utilization by Service",
      "type": "timeseries"
    },
    {
      "datasource": "CloudWatch",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true,
            "stacking": {
              "group": "A",
              "mode": "normal"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 10
      },
      "id": 16,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "alias": "{{ServiceName}}",
          "dimensions": {
            "ClusterName": "${var.compute_outputs.cluster_id}",
            "ServiceName": "${var.compute_outputs.frontend_service_name}"
          },
          "expression": "",
          "id": "",
          "matchExact": true,
          "metricName": "MemoryUtilization",
          "namespace": "AWS/ECS",
          "period": "",
          "refId": "A",
          "region": "${var.region}",
          "statistic": "Average"
        },
        {
          "alias": "{{ServiceName}}",
          "dimensions": {
            "ClusterName": "${var.compute_outputs.cluster_id}",
            "ServiceName": "${var.compute_outputs.backend_service_name}"
          },
          "expression": "",
          "id": "",
          "matchExact": true,
          "metricName": "MemoryUtilization",
          "namespace": "AWS/ECS",
          "period": "",
          "refId": "B",
          "region": "${var.region}",
          "statistic": "Average"
        },
        {
          "alias": "{{ServiceName}}",
          "dimensions": {
            "ClusterName": "${var.compute_outputs.cluster_id}",
            "ServiceName": "${var.compute_outputs.molecule_service_name}"
          },
          "expression": "",
          "id": "",
          "matchExact": true,
          "metricName": "MemoryUtilization",
          "namespace": "AWS/ECS",
          "period": "",
          "refId": "C",
          "region": "${var.region}",
          "statistic": "Average"
        },
        {
          "alias": "{{ServiceName}}",
          "dimensions": {
            "ClusterName": "${var.compute_outputs.cluster_id}",
            "ServiceName": "${var.compute_outputs.worker_service_name}"
          },
          "expression": "",
          "id": "",
          "matchExact": true,
          "metricName": "MemoryUtilization",
          "namespace": "AWS/ECS",
          "period": "",
          "refId": "D",
          "region": "${var.region}",
          "statistic": "Average"
        }
      ],
      "title": "Memory Utilization by Service",
      "type": "timeseries"
    },
    {
      "datasource": "CloudWatch",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "ms"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 18
      },
      "id": 18,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "alias": "P95",
          "dimensions": {},
          "expression": "SELECT p95(TargetResponseTime) FROM SCHEMA(\"AWS/ApplicationELB\", LoadBalancer)",
          "id": "",
          "matchExact": true,
          "metricName": "TargetResponseTime",
          "namespace": "AWS/ApplicationELB",
          "period": "",
          "refId": "A",
          "region": "${var.region}",
          "statistic": "p95"
        },
        {
          "alias": "P50",
          "dimensions": {},
          "expression": "SELECT p50(TargetResponseTime) FROM SCHEMA(\"AWS/ApplicationELB\", LoadBalancer)",
          "id": "",
          "matchExact": true,
          "metricName": "TargetResponseTime",
          "namespace": "AWS/ApplicationELB",
          "period": "",
          "refId": "B",
          "region": "${var.region}",
          "statistic": "p50"
        }
      ],
      "title": "API Response Time",
      "type": "timeseries"
    },
    {
      "datasource": "CloudWatch",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true,
            "stacking": {
              "group": "A",
              "mode": "normal"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "reqps"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 18
      },
      "id": 20,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "alias": "2xx",
          "dimensions": {},
          "expression": "SELECT SUM(HTTPCode_Target_2XX_Count) FROM SCHEMA(\"AWS/ApplicationELB\", LoadBalancer)",
          "id": "",
          "matchExact": true,
          "metricName": "HTTPCode_Target_2XX_Count",
          "namespace": "AWS/ApplicationELB",
          "period": "",
          "refId": "A",
          "region": "${var.region}",
          "statistic": "Sum"
        },
        {
          "alias": "4xx",
          "dimensions": {},
          "expression": "SELECT SUM(HTTPCode_Target_4XX_Count) FROM SCHEMA(\"AWS/ApplicationELB\", LoadBalancer)",
          "id": "",
          "matchExact": true,
          "metricName": "HTTPCode_Target_4XX_Count",
          "namespace": "AWS/ApplicationELB",
          "period": "",
          "refId": "B",
          "region": "${var.region}",
          "statistic": "Sum"
        },
        {
          "alias": "5xx",
          "dimensions": {},
          "expression": "SELECT SUM(HTTPCode_Target_5XX_Count) FROM SCHEMA(\"AWS/ApplicationELB\", LoadBalancer)",
          "id": "",
          "matchExact": true,
          "metricName": "HTTPCode_Target_5XX_Count",
          "namespace": "AWS/ApplicationELB",
          "period": "",
          "refId": "C",
          "region": "${var.region}",
          "statistic": "Sum"
        }
      ],
      "title": "HTTP Response Codes",
      "type": "timeseries"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 30,
  "style": "dark",
  "tags": [
    "system",
    "infrastructure"
  ],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "System Health Dashboard",
  "uid": "system-health",
  "version": 1
}
EOT

  molecule_processing_dashboard = <<-EOT
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": 2,
  "links": [],
  "panels": [
    {
      "collapsed": false,
      "datasource": null,
      "gridPos": {
        "h": 1,
        "w": 24,
        "x": 0,
        "y": 0
      },
      "id": 16,
      "panels": [],
      "title": "Molecule Processing Overview",
      "type": "row"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 0,
        "y": 1
      },
      "id": 2,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "text": {},
        "textMode": "auto"
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "sum(molecule_upload_total) or vector(0)",
          "interval": "",
          "legendFormat": "",
          "refId": "A"
        }
      ],
      "title": "Total Molecules Uploaded",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 30
              }
            ]
          },
          "unit": "s"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 6,
        "y": 1
      },
      "id": 4,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "text": {},
        "textMode": "auto"
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "avg(molecule_processing_time_seconds) or vector(0)",
          "interval": "",
          "legendFormat": "",
          "refId": "A"
        }
      ],
      "title": "Avg Processing Time per 10K Molecules",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "red",
                "value": null
              },
              {
                "color": "yellow",
                "value": 0.95
              },
              {
                "color": "green",
                "value": 0.98
              }
            ]
          },
          "unit": "percentunit"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 12,
        "y": 1
      },
      "id": 6,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "text": {},
        "textMode": "auto"
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "molecule_upload_success_rate or vector(1)",
          "interval": "",
          "legendFormat": "",
          "refId": "A"
        }
      ],
      "title": "Upload Success Rate",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 18,
        "y": 1
      },
      "id": 8,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "text": {},
        "textMode": "auto"
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "sum(molecule_libraries_total) or vector(0)",
          "interval": "",
          "legendFormat": "",
          "refId": "A"
        }
      ],
      "title": "Total Molecule Libraries",
      "type": "stat"
    },
    {
      "collapsed": false,
      "datasource": null,
      "gridPos": {
        "h": 1,
        "w": 24,
        "x": 0,
        "y": 9
      },
      "id": 18,
      "panels": [],
      "title": "Processing Metrics",
      "type": "row"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 10
      },
      "id": 10,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "sum(rate(molecule_upload_total[5m])) or vector(0)",
          "interval": "",
          "legendFormat": "Upload Rate",
          "refId": "A"
        }
      ],
      "title": "Molecule Upload Rate (5m)",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "s"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 10
      },
      "id": 12,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "molecule_processing_time_seconds or vector(0)",
          "interval": "",
          "legendFormat": "Processing Time",
          "refId": "A"
        }
      ],
      "title": "Molecule Processing Time",
      "type": "timeseries"
    },
    {
      "collapsed": false,
      "datasource": null,
      "gridPos": {
        "h": 1,
        "w": 24,
        "x": 0,
        "y": 18
      },
      "id": 20,
      "panels": [],
      "title": "AI Prediction Metrics",
      "type": "row"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "s"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 19
      },
      "id": 14,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "ai_prediction_time_seconds or vector(0)",
          "interval": "",
          "legendFormat": "Prediction Time",
          "refId": "A"
        }
      ],
      "title": "AI Prediction Time",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "percentunit"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 19
      },
      "id": 22,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "ai_prediction_success_rate or vector(1)",
          "interval": "",
          "legendFormat": "Success Rate",
          "refId": "A"
        }
      ],
      "title": "AI Prediction Success Rate",
      "type": "timeseries"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 30,
  "style": "dark",
  "tags": [
    "molecules",
    "processing"
  ],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "Molecule Processing Dashboard",
  "uid": "molecule-processing",
  "version": 1
}
EOT

  cro_integration_dashboard = <<-EOT
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": 3,
  "links": [],
  "panels": [
    {
      "collapsed": false,
      "datasource": null,
      "gridPos": {
        "h": 1,
        "w": 24,
        "x": 0,
        "y": 0
      },
      "id": 10,
      "panels": [],
      "title": "CRO Overview",
      "type": "row"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 0,
        "y": 1
      },
      "id": 2,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "text": {},
        "textMode": "auto"
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "sum(cro_submission_total) or vector(0)",
          "interval": "",
          "legendFormat": "",
          "refId": "A"
        }
      ],
      "title": "Total CRO Submissions",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 6,
        "y": 1
      },
      "id": 4,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "text": {},
        "textMode": "auto"
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "sum(cro_active_submissions) or vector(0)",
          "interval": "",
          "legendFormat": "",
          "refId": "A"
        }
      ],
      "title": "Active CRO Submissions",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 12,
        "y": 1
      },
      "id": 6,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "text": {},
        "textMode": "auto"
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "sum(cro_results_received_total) or vector(0)",
          "interval": "",
          "legendFormat": "",
          "refId": "A"
        }
      ],
      "title": "Results Received",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "red",
                "value": null
              },
              {
                "color": "orange",
                "value": 0.9
              },
              {
                "color": "green",
                "value": 0.95
              }
            ]
          },
          "unit": "percentunit"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 18,
        "y": 1
      },
      "id": 8,
      "options": {
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "showThresholdLabels": false,
        "showThresholdMarkers": true,
        "text": {}
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "cro_submission_success_rate or vector(1)",
          "interval": "",
          "legendFormat": "",
          "refId": "A"
        }
      ],
      "title": "Submission Success Rate",
      "type": "gauge"
    },
    {
      "collapsed": false,
      "datasource": null,
      "gridPos": {
        "h": 1,
        "w": 24,
        "x": 0,
        "y": 9
      },
      "id": 16,
      "panels": [],
      "title": "CRO Metrics",
      "type": "row"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 10
      },
      "id": 12,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "sum(rate(cro_submission_total[5m])) or vector(0)",
          "interval": "",
          "legendFormat": "Submission Rate",
          "refId": "A"
        }
      ],
      "title": "CRO Submission Rate (5m)",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "h"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 10
      },
      "id": 14,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "cro_time_to_results_hours or vector(0)",
          "interval": "",
          "legendFormat": "Time to Results",
          "refId": "A"
        }
      ],
      "title": "Time to Results",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 9,
        "w": 12,
        "x": 0,
        "y": 18
      },
      "id": 18,
      "options": {
        "displayMode": "gradient",
        "orientation": "horizontal",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "showUnfilled": true,
        "text": {}
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "sum by(status) (cro_submissions_by_status) or vector(0)",
          "interval": "",
          "legendFormat": "{{status}}",
          "refId": "A"
        }
      ],
      "title": "Submissions by Status",
      "type": "bargauge"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "none"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 9,
        "w": 12,
        "x": 12,
        "y": 18
      },
      "id": 20,
      "options": {
        "displayMode": "gradient",
        "orientation": "horizontal",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "showUnfilled": true,
        "text": {}
      },
      "pluginVersion": "8.0.0",
      "targets": [
        {
          "expr": "sum by(service) (cro_submissions_by_service) or vector(0)",
          "interval": "",
          "legendFormat": "{{service}}",
          "refId": "A"
        }
      ],
      "title": "Submissions by Service Type",
      "type": "bargauge"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 30,
  "style": "dark",
  "tags": [
    "cro",
    "integration"
  ],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "CRO Integration Dashboard",
  "uid": "cro-integration",
  "version": 1
}
EOT
}

# Grafana ECS Task Definition
resource "aws_ecs_task_definition" "grafana" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  family                   = "${local.name_prefix}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = local.grafana_cpu
  memory                   = local.grafana_memory
  execution_role_arn       = aws_iam_role.grafana_execution_role[0].arn
  task_role_arn            = aws_iam_role.grafana_task_role[0].arn
  
  container_definitions = local.grafana_container_definition
  
  volume {
    name = "grafana-data"
    
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.grafana_data[0].id
      root_directory     = "/"
      transit_encryption = "ENABLED"
      
      authorization_config {
        iam = "ENABLED"
      }
    }
  }
  
  volume {
    name = "grafana-provisioning"
    
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.grafana_data[0].id
      root_directory     = "/provisioning"
      transit_encryption = "ENABLED"
      
      authorization_config {
        iam = "ENABLED"
      }
    }
  }
  
  volume {
    name = "grafana-dashboards"
    
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.grafana_data[0].id
      root_directory     = "/dashboards"
      transit_encryption = "ENABLED"
      
      authorization_config {
        iam = "ENABLED"
      }
    }
  }
  
  tags = local.grafana_tags
}

# Grafana ECS Service
resource "aws_ecs_service" "grafana" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  name             = "${local.name_prefix}-service"
  cluster          = var.compute_outputs.cluster_id
  task_definition  = aws_ecs_task_definition.grafana[0].arn
  launch_type      = "FARGATE"
  platform_version = "LATEST"
  desired_count    = 1
  
  network_configuration {
    subnets          = data.aws_subnets.private.ids
    security_groups  = [aws_security_group.grafana_sg[0].id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.grafana[0].arn
    container_name   = "grafana"
    container_port   = local.grafana_container_port
  }
  
  health_check_grace_period_seconds = 120
  
  deployment_controller {
    type = "ECS"
  }
  
  tags = local.grafana_tags
  
  depends_on = [
    aws_lb_listener_rule.grafana,
    aws_efs_mount_target.grafana_mount_target
  ]
}

# Initialize Grafana dashboards and data sources
resource "null_resource" "grafana_init" {
  count = var.monitoring.enable_grafana ? 1 : 0
  
  triggers = {
    grafana_task_definition = aws_ecs_task_definition.grafana[0].id
    system_dashboard_hash   = md5(local.system_health_dashboard)
    molecule_dashboard_hash = md5(local.molecule_processing_dashboard)
    cro_dashboard_hash      = md5(local.cro_integration_dashboard)
    datasources_hash        = md5(local.datasources_yaml)
  }
  
  provisioner "local-exec" {
    command = <<-EOT
      # Create temporary files
      DATASOURCES_FILE=$(mktemp)
      DASHBOARDS_FILE=$(mktemp)
      SYSTEM_DASHBOARD_FILE=$(mktemp)
      MOLECULE_DASHBOARD_FILE=$(mktemp)
      CRO_DASHBOARD_FILE=$(mktemp)
      
      # Write configurations to files
      echo '${local.datasources_yaml}' > $DATASOURCES_FILE
      echo '${local.dashboards_yaml}' > $DASHBOARDS_FILE
      echo '${local.system_health_dashboard}' > $SYSTEM_DASHBOARD_FILE
      echo '${local.molecule_processing_dashboard}' > $MOLECULE_DASHBOARD_FILE
      echo '${local.cro_integration_dashboard}' > $CRO_DASHBOARD_FILE
      
      # Use AWS CLI to store these files in EFS
      # Use a temporary task to mount EFS and copy files
      aws ecs run-task \
        --cluster ${var.compute_outputs.cluster_id} \
        --task-definition ${aws_ecs_task_definition.grafana[0].arn} \
        --overrides '{ 
          "containerOverrides": [{ 
            "name": "grafana", 
            "command": [
              "/bin/sh", "-c", 
              "mkdir -p /var/lib/grafana/provisioning/datasources && \
               mkdir -p /var/lib/grafana/provisioning/dashboards && \
               mkdir -p /var/lib/grafana/dashboards && \
               cp /tmp/datasources.yaml /var/lib/grafana/provisioning/datasources/ && \
               cp /tmp/dashboards.yaml /var/lib/grafana/provisioning/dashboards/ && \
               cp /tmp/system_health.json /var/lib/grafana/dashboards/ && \
               cp /tmp/molecule_processing.json /var/lib/grafana/dashboards/ && \
               cp /tmp/cro_integration.json /var/lib/grafana/dashboards/"
            ],
            "environment": [{
              "name": "AWS_REGION",
              "value": "${var.region}"
            }]
          }]
        }' \
        --region ${var.region}
      
      # Clean up temporary files
      rm $DATASOURCES_FILE $DASHBOARDS_FILE $SYSTEM_DASHBOARD_FILE $MOLECULE_DASHBOARD_FILE $CRO_DASHBOARD_FILE
    EOT
  }
  
  depends_on = [
    aws_ecs_service.grafana,
    aws_efs_mount_target.grafana_mount_target
  ]
}

# Output values
output "grafana_url" {
  description = "URL for accessing the Grafana UI"
  value       = var.monitoring.enable_grafana ? "/grafana" : null
}

output "grafana_ecs_service_name" {
  description = "Name of the ECS service running Grafana"
  value       = var.monitoring.enable_grafana ? aws_ecs_service.grafana[0].name : null
}

output "grafana_log_group_name" {
  description = "Name of the CloudWatch log group for Grafana logs"
  value       = var.monitoring.enable_grafana ? aws_cloudwatch_log_group.grafana_logs[0].name : null
}

output "grafana_dashboard_urls" {
  description = "URLs for accessing specific Grafana dashboards"
  value = var.monitoring.enable_grafana ? {
    system_health      = local.system_health_dashboard_path
    molecule_processing = local.molecule_processing_dashboard_path
    cro_integration    = local.cro_integration_dashboard_path
  } : null
}