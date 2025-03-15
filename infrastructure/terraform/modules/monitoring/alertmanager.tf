# AlertManager - Terraform configuration for alert management system
# Part of the Molecular Data Management and CRO Integration Platform

# -----------------------------------------------------------------------------
# Data Source - Current AWS Account
# -----------------------------------------------------------------------------
data "aws_caller_identity" "current" {}

# -----------------------------------------------------------------------------
# Local variables
# -----------------------------------------------------------------------------
locals {
  name_prefix = "${var.environment}-alertmanager"
  
  # Common tags for all resources
  common_tags = merge(var.tags, {
    Component = "Monitoring"
    Service   = "AlertManager"
  })
  
  # AlertManager configuration
  alertmanager_port = 9093
  alertmanager_container_name = "alertmanager"
  
  # Alert severity levels and mappings
  alert_severities = {
    p1 = "critical"  # Critical alerts - immediate response required (15 min SLA)
    p2 = "high"      # High priority - prompt attention needed (1 hour SLA)
    p3 = "medium"    # Medium priority - attention during business hours (8 hour SLA)
    p4 = "low"       # Low priority - standard response (Next business day)
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Log Group
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "alertmanager" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = var.monitoring.log_retention_days
  
  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# EFS File System for persistent data
# -----------------------------------------------------------------------------
resource "aws_efs_file_system" "alertmanager" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  creation_token = "${local.name_prefix}-data"
  performance_mode = "generalPurpose"
  throughput_mode = "bursting"
  
  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }
  
  tags = local.common_tags
}

resource "aws_efs_mount_target" "alertmanager" {
  count = var.monitoring.enable_alertmanager ? 3 : 0 # Assuming 3 AZs/subnets
  
  file_system_id = aws_efs_file_system.alertmanager[0].id
  subnet_id      = var.private_subnet_ids[count.index]
  security_groups = [aws_security_group.alertmanager[0].id]
}

# -----------------------------------------------------------------------------
# Security Group
# -----------------------------------------------------------------------------
resource "aws_security_group" "alertmanager" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  name        = "${local.name_prefix}-sg"
  description = "Security group for AlertManager service"
  vpc_id      = var.vpc_id
  
  ingress {
    from_port       = local.alertmanager_port
    to_port         = local.alertmanager_port
    protocol        = "tcp"
    description     = "Allow inbound traffic to AlertManager UI"
    security_groups = [var.alb_security_group_id]
  }
  
  ingress {
    from_port       = local.alertmanager_port
    to_port         = local.alertmanager_port
    protocol        = "tcp"
    description     = "Allow inbound traffic from Prometheus"
    security_groups = [aws_security_group.prometheus[0].id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# IAM Roles and Policies
# -----------------------------------------------------------------------------
# Task execution role - used by ECS to pull container images, write logs, etc.
resource "aws_iam_role" "alertmanager_execution" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  name = "${local.name_prefix}-execution-role"
  
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
  
  tags = local.common_tags
}

# Task role - used by the container itself
resource "aws_iam_role" "alertmanager_task" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  name = "${local.name_prefix}-task-role"
  
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
  
  tags = local.common_tags
}

# Policy for accessing SSM parameters
resource "aws_iam_policy" "alertmanager_ssm" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  name        = "${local.name_prefix}-ssm-policy"
  description = "Policy for AlertManager to access SSM parameters"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter"
        ]
        Effect   = "Allow"
        Resource = [
          "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/alertmanager/*"
        ]
      }
    ]
  })
  
  tags = local.common_tags
}

# Policy for sending SNS notifications
resource "aws_iam_policy" "alertmanager_sns" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  name        = "${local.name_prefix}-sns-policy"
  description = "Policy for AlertManager to publish to SNS topics"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "sns:Publish"
        ]
        Effect   = "Allow"
        Resource = [
          for severity in keys(local.alert_severities) :
          aws_sns_topic.alerts[severity].arn
        ]
      }
    ]
  })
  
  tags = local.common_tags
}

# Policy for sending SES email
resource "aws_iam_policy" "alertmanager_ses" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  name        = "${local.name_prefix}-ses-policy"
  description = "Policy for AlertManager to send emails via SES"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Effect   = "Allow"
        Resource = "*"
        Condition = {
          StringEquals = {
            "ses:FromAddress" = var.monitoring.alarm_email
          }
        }
      }
    ]
  })
  
  tags = local.common_tags
}

# Attach the execution role policy
resource "aws_iam_role_policy_attachment" "alertmanager_execution" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  role       = aws_iam_role.alertmanager_execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Attach the SSM policy to the task role
resource "aws_iam_role_policy_attachment" "alertmanager_ssm" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  role       = aws_iam_role.alertmanager_task[0].name
  policy_arn = aws_iam_policy.alertmanager_ssm[0].arn
}

# Attach the SNS policy to the task role
resource "aws_iam_role_policy_attachment" "alertmanager_sns" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  role       = aws_iam_role.alertmanager_task[0].name
  policy_arn = aws_iam_policy.alertmanager_sns[0].arn
}

# Attach the SES policy to the task role
resource "aws_iam_role_policy_attachment" "alertmanager_ses" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  role       = aws_iam_role.alertmanager_task[0].name
  policy_arn = aws_iam_policy.alertmanager_ses[0].arn
}

# -----------------------------------------------------------------------------
# SNS Topics and Subscriptions
# -----------------------------------------------------------------------------
resource "aws_sns_topic" "alerts" {
  for_each = var.monitoring.enable_alertmanager ? local.alert_severities : {}
  
  name = "${local.name_prefix}-alerts-${each.value}"
  
  tags = merge(local.common_tags, {
    Severity = each.value
  })
}

# Create email subscriptions to the topics
resource "aws_sns_topic_subscription" "email" {
  for_each = var.monitoring.enable_alertmanager && var.monitoring.alarm_email != "" ? {
    p1 = local.alert_severities.p1
    p2 = local.alert_severities.p2
  } : {}
  
  topic_arn = aws_sns_topic.alerts[each.key].arn
  protocol  = "email"
  endpoint  = var.monitoring.alarm_email
}

# Create PagerDuty subscription for critical alerts
resource "aws_sns_topic_subscription" "pagerduty" {
  count = var.monitoring.enable_alertmanager && var.monitoring.pagerduty_service_key != "" ? 1 : 0
  
  topic_arn = aws_sns_topic.alerts["p1"].arn
  protocol  = "https"
  endpoint  = "https://events.pagerduty.com/integration/${var.monitoring.pagerduty_service_key}/enqueue"
}

# Create Slack webhook subscriptions
resource "aws_sns_topic_subscription" "slack" {
  for_each = var.monitoring.enable_alertmanager && var.monitoring.slack_webhook_url != "" ? local.alert_severities : {}
  
  topic_arn = aws_sns_topic.alerts[each.key].arn
  protocol  = "https"
  endpoint  = var.monitoring.slack_webhook_url
}

# -----------------------------------------------------------------------------
# AlertManager Configuration
# -----------------------------------------------------------------------------
data "template_file" "alertmanager_config" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  template = <<EOF
global:
  resolve_timeout: 5m
  smtp_smarthost: 'email-smtp.${var.region}.amazonaws.com:587'
  smtp_from: '${var.monitoring.alarm_email}'
  smtp_require_tls: true

route:
  group_by: ['alertname', 'service', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'slack-notifications'
  routes:
  - match:
      severity: critical
    receiver: 'pagerduty-critical'
    continue: true
    group_wait: 10s
    repeat_interval: 1h
  - match_re:
      service: ^(molecule-service|backend-api|worker)$
      severity: critical
    receiver: 'pagerduty-critical'
    group_wait: 10s
    repeat_interval: 30m
  - match:
      severity: high
    receiver: 'email-team'
    group_wait: 30s
    repeat_interval: 2h
  - match:
      severity: medium
    receiver: 'slack-notifications'
    group_wait: 1m
    repeat_interval: 4h
  - match:
      severity: low
    receiver: 'slack-notifications'
    group_wait: 2m
    repeat_interval: 12h
  # Time-based routing: after hours (weekday nights and weekends)
  - match:
      severity: high
    receiver: 'pagerduty-critical'
    group_wait: 1m
    routes:
    - matchers:
      - weekday=~"(Monday|Tuesday|Wednesday|Thursday|Friday)"
      - hour=~"(9|10|11|12|13|14|15|16|17)"
      receiver: 'email-team'

inhibit_rules:
- source_match:
    severity: critical
  target_match:
    severity: high
  equal: ['alertname', 'service']
- source_match:
    severity: high
  target_match:
    severity: medium
  equal: ['alertname', 'service']
- source_match:
    severity: medium
  target_match:
    severity: low
  equal: ['alertname', 'service']

receivers:
- name: 'pagerduty-critical'
  pagerduty_configs:
  - service_key: '${var.monitoring.pagerduty_service_key}'
    send_resolved: true
    description: '{{ .GroupLabels.alertname }}'
    client: 'AlertManager'
    client_url: 'https://{{ template "alertmanager.externalUrl" . }}'
    details:
      severity: '{{ .GroupLabels.severity }}'
      summary: '{{ .CommonAnnotations.summary }}'
      description: '{{ .CommonAnnotations.description }}'
      service: '{{ .GroupLabels.service }}'

- name: 'email-team'
  email_configs:
  - to: '${var.monitoring.alarm_email}'
    send_resolved: true
    headers:
      subject: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
    html: |
      <h3>{{ .GroupLabels.alertname }}</h3>
      <p><strong>Status:</strong> {{ .Status | toUpper }}</p>
      <p><strong>Severity:</strong> {{ .GroupLabels.severity }}</p>
      <p><strong>Service:</strong> {{ .GroupLabels.service }}</p>
      <p><strong>Summary:</strong> {{ .CommonAnnotations.summary }}</p>
      <p><strong>Description:</strong> {{ .CommonAnnotations.description }}</p>
      <h4>Alerts:</h4>
      <ul>
      {{ range .Alerts }}
        <li>
          <p><strong>Started:</strong> {{ .StartsAt }}</p>
          <p><strong>Details:</strong></p>
          <ul>
            {{ range .Labels.SortedPairs }}
              <li><strong>{{ .Name }}:</strong> {{ .Value }}</li>
            {{ end }}
          </ul>
        </li>
      {{ end }}
      </ul>

- name: 'slack-notifications'
  slack_configs:
  - api_url: '${var.monitoring.slack_webhook_url}'
    channel: '#alerts'
    send_resolved: true
    icon_emoji: ':warning:'
    title: '{{ if eq .Status "firing" }}:red_circle:{{ else }}:green_circle:{{ end }} [{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
    text: >-
      {{ range .Alerts }}
        *Alert:* {{ .Annotations.summary }}
        *Description:* {{ .Annotations.description }}
        *Severity:* {{ .Labels.severity }}
        *Service:* {{ .Labels.service }}
        *Started:* {{ .StartsAt }}
        *Details:*
        {{ range .Labels.SortedPairs }} • *{{ .Name }}:* {{ .Value }}
        {{ end }}
      {{ end }}
EOF
}

# Store AlertManager configuration in SSM Parameter Store
resource "aws_ssm_parameter" "alertmanager_config" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  name        = "/alertmanager/config"
  description = "AlertManager configuration file"
  type        = "SecureString"
  value       = data.template_file.alertmanager_config[0].rendered
  
  tags = local.common_tags
}

# Store sensitive values in SSM Parameter Store
resource "aws_ssm_parameter" "slack_webhook" {
  count = var.monitoring.enable_alertmanager && var.monitoring.slack_webhook_url != "" ? 1 : 0
  
  name        = "/alertmanager/slack-webhook-url"
  description = "Slack webhook URL for AlertManager notifications"
  type        = "SecureString"
  value       = var.monitoring.slack_webhook_url
  
  tags = local.common_tags
}

resource "aws_ssm_parameter" "pagerduty_service_key" {
  count = var.monitoring.enable_alertmanager && var.monitoring.pagerduty_service_key != "" ? 1 : 0
  
  name        = "/alertmanager/pagerduty-service-key"
  description = "PagerDuty service key for AlertManager notifications"
  type        = "SecureString"
  value       = var.monitoring.pagerduty_service_key
  
  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Load Balancer Target Group
# -----------------------------------------------------------------------------
resource "aws_lb_target_group" "alertmanager" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  name     = "${local.name_prefix}-tg"
  port     = local.alertmanager_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  target_type = "ip"
  
  health_check {
    path                = "/-/healthy"
    port                = local.alertmanager_port
    protocol            = "HTTP"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
    matcher             = "200"
  }
  
  tags = local.common_tags
}

# Create a listener rule for the ALB
resource "aws_lb_listener_rule" "alertmanager" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  listener_arn = var.alb_listener_arn
  priority     = 30
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.alertmanager[0].arn
  }
  
  condition {
    path_pattern {
      values = ["/alertmanager/*"]
    }
  }
  
  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# ECS Task Definition and Service
# -----------------------------------------------------------------------------
resource "aws_ecs_task_definition" "alertmanager" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  family                   = local.name_prefix
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.alertmanager_execution[0].arn
  task_role_arn            = aws_iam_role.alertmanager_task[0].arn
  
  container_definitions = jsonencode([{
    name      = local.alertmanager_container_name
    image     = "prom/alertmanager:v${var.monitoring.alertmanager_version}"
    essential = true
    
    portMappings = [{
      containerPort = local.alertmanager_port
      hostPort      = local.alertmanager_port
      protocol      = "tcp"
    }]
    
    environment = [
      {
        name  = "TZ",
        value = "UTC"
      }
    ]
    
    secrets = [
      {
        name      = "ALERTMANAGER_CONFIG",
        valueFrom = aws_ssm_parameter.alertmanager_config[0].arn
      }
    ]
    
    mountPoints = [{
      sourceVolume  = "alertmanager-data"
      containerPath = "/alertmanager"
      readOnly      = false
    }]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.alertmanager[0].name
        "awslogs-region"        = var.region
        "awslogs-stream-prefix" = "ecs"
      }
    }
    
    command = [
      "--config.file=/etc/alertmanager/config.yml",
      "--storage.path=/alertmanager",
      "--web.external-url=/alertmanager"
    ]
  }])
  
  volume {
    name = "alertmanager-data"
    
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.alertmanager[0].id
      root_directory = "/"
    }
  }
  
  tags = local.common_tags
}

resource "aws_ecs_service" "alertmanager" {
  count = var.monitoring.enable_alertmanager ? 1 : 0
  
  name            = local.name_prefix
  cluster         = var.compute_outputs.cluster_id
  task_definition = aws_ecs_task_definition.alertmanager[0].arn
  desired_count   = 1
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.alertmanager[0].id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.alertmanager[0].arn
    container_name   = local.alertmanager_container_name
    container_port   = local.alertmanager_port
  }
  
  # Ignore changes to desired_count because we'll manage that with autoscaling
  lifecycle {
    ignore_changes = [desired_count]
  }
  
  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "alertmanager_url" {
  description = "URL for accessing the AlertManager UI"
  value       = var.monitoring.enable_alertmanager ? "/alertmanager" : ""
}

output "alertmanager_ecs_service_name" {
  description = "Name of the ECS service running AlertManager"
  value       = var.monitoring.enable_alertmanager ? aws_ecs_service.alertmanager[0].name : ""
}

output "alertmanager_log_group_name" {
  description = "Name of the CloudWatch log group for AlertManager logs"
  value       = var.monitoring.enable_alertmanager ? aws_cloudwatch_log_group.alertmanager[0].name : ""
}

output "alertmanager_security_group_id" {
  description = "ID of the security group for AlertManager service"
  value       = var.monitoring.enable_alertmanager ? aws_security_group.alertmanager[0].id : ""
}

output "alertmanager_efs_id" {
  description = "ID of the EFS file system for AlertManager data"
  value       = var.monitoring.enable_alertmanager ? aws_efs_file_system.alertmanager[0].id : ""
}

output "alert_topic_arns" {
  description = "ARNs of the SNS topics for different alert severities"
  value       = var.monitoring.enable_alertmanager ? {
    for severity, name in local.alert_severities : severity => aws_sns_topic.alerts[severity].arn
  } : {}
}