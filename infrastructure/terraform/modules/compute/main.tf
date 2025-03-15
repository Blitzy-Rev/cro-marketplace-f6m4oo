# Terraform configuration for AWS compute resources including ECS, ALB, and auto-scaling
# for the Molecular Data Management and CRO Integration Platform

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

locals {
  # Resource naming patterns
  name_prefix = "${var.project_name}-${var.environment}"
  
  # Common tags for all resources
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "Terraform"
    }
  )
  
  # Log retention periods based on environment
  log_retention_days = {
    dev     = 7
    staging = 14
    prod    = 30
  }
  
  # Service names
  services = toset(keys(var.service_configs))
  
  # Services that need load balancer integration
  lb_services = toset([for svc, config in var.service_configs : svc if contains(keys(var.target_group_configs), svc)])
}

#-----------------------------------------
# ECS Cluster
#-----------------------------------------
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-${var.cluster_name}"
  
  setting {
    name  = "containerInsights"
    value = var.cluster_settings["containerInsights"]
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-cluster"
    }
  )
}

#-----------------------------------------
# CloudWatch Log Groups
#-----------------------------------------
resource "aws_cloudwatch_log_group" "ecs_logs" {
  for_each = local.services
  
  name              = "/ecs/${local.name_prefix}-${each.value}"
  retention_in_days = lookup(local.log_retention_days, var.environment, 7)
  
  tags = merge(
    local.common_tags,
    {
      Name    = "/ecs/${local.name_prefix}-${each.value}"
      Service = each.value
    }
  )
}

#-----------------------------------------
# ECS Task Definitions
#-----------------------------------------
resource "aws_ecs_task_definition" "services" {
  for_each = var.task_definitions
  
  family                   = "${local.name_prefix}-${each.key}"
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  network_mode             = each.value.network_mode
  requires_compatibilities = each.value.requires_compatibilities
  execution_role_arn       = each.value.execution_role_arn
  task_role_arn            = each.value.task_role_arn
  container_definitions    = each.value.container_definitions
  
  dynamic "ephemeral_storage" {
    for_each = each.value.ephemeral_storage != null ? [each.value.ephemeral_storage] : []
    content {
      size_in_gib = ephemeral_storage.value
    }
  }
  
  dynamic "volume" {
    for_each = each.value.volumes
    content {
      name = volume.value.name
      
      dynamic "efs_volume_configuration" {
        for_each = volume.value.efs_volume_configuration != null ? [volume.value.efs_volume_configuration] : []
        content {
          file_system_id     = efs_volume_configuration.value.file_system_id
          root_directory     = efs_volume_configuration.value.root_directory
          transit_encryption = efs_volume_configuration.value.transit_encryption
        }
      }
    }
  }
  
  tags = merge(
    local.common_tags,
    {
      Name    = "${local.name_prefix}-${each.key}-task"
      Service = each.key
    }
  )
}

#-----------------------------------------
# Application Load Balancer
#-----------------------------------------
resource "aws_lb" "main" {
  name                             = "${local.name_prefix}-${var.alb_config.name}"
  internal                         = var.alb_config.internal
  load_balancer_type               = var.alb_config.load_balancer_type
  security_groups                  = [var.security_group_ids["alb"]]
  subnets                          = var.public_subnet_ids
  enable_deletion_protection       = var.alb_config.enable_deletion_protection
  idle_timeout                     = var.alb_config.idle_timeout
  enable_http2                     = var.alb_config.enable_http2
  enable_cross_zone_load_balancing = var.alb_config.enable_cross_zone_load_balancing
  
  dynamic "access_logs" {
    for_each = var.alb_config.access_logs.enabled ? [var.alb_config.access_logs] : []
    content {
      bucket  = access_logs.value.bucket
      prefix  = access_logs.value.prefix
      enabled = true
    }
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-alb"
    }
  )
}

#-----------------------------------------
# Target Groups
#-----------------------------------------
resource "aws_lb_target_group" "services" {
  for_each = var.target_group_configs
  
  name                 = "${local.name_prefix}-${each.key}-tg"
  port                 = each.value.port
  protocol             = each.value.protocol
  vpc_id               = var.vpc_id
  target_type          = each.value.target_type
  deregistration_delay = each.value.deregistration_delay
  slow_start           = each.value.slow_start
  
  health_check {
    enabled             = each.value.health_check.enabled
    path                = each.value.health_check.path
    port                = each.value.health_check.port
    protocol            = each.value.health_check.protocol
    healthy_threshold   = each.value.health_check.healthy_threshold
    unhealthy_threshold = each.value.health_check.unhealthy_threshold
    timeout             = each.value.health_check.timeout
    interval            = each.value.health_check.interval
    matcher             = each.value.health_check.matcher
  }
  
  dynamic "stickiness" {
    for_each = each.value.stickiness.enabled ? [each.value.stickiness] : []
    content {
      type            = stickiness.value.type
      cookie_duration = stickiness.value.cookie_duration
      enabled         = true
    }
  }
  
  tags = merge(
    local.common_tags,
    {
      Name    = "${local.name_prefix}-${each.key}-tg"
      Service = each.key
    }
  )
  
  lifecycle {
    create_before_destroy = true
  }
}

#-----------------------------------------
# ALB Listeners
#-----------------------------------------
resource "aws_lb_listener" "listeners" {
  for_each = var.listener_configs
  
  load_balancer_arn = aws_lb.main.arn
  port              = each.value.port
  protocol          = each.value.protocol
  ssl_policy        = each.value.protocol == "HTTPS" ? each.value.ssl_policy : null
  certificate_arn   = each.value.protocol == "HTTPS" ? each.value.certificate_arn : null
  
  default_action {
    type = each.value.default_action.type
    
    dynamic "redirect" {
      for_each = each.value.default_action.type == "redirect" ? [each.value.default_action.redirect] : []
      content {
        port        = redirect.value.port
        protocol    = redirect.value.protocol
        status_code = redirect.value.status_code
      }
    }
    
    dynamic "forward" {
      for_each = each.value.default_action.type == "forward" ? [1] : []
      content {
        target_group {
          arn = aws_lb_target_group.services[each.value.default_action.target_group_key].arn
        }
      }
    }
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-${each.key}-listener"
    }
  )
}

#-----------------------------------------
# ALB Listener Rules
#-----------------------------------------
resource "aws_lb_listener_rule" "rules" {
  for_each = {
    for idx, rule in flatten([
      for listener_key, listener in var.listener_configs : [
        for rule_idx, rule in lookup(listener, "rules", []) : {
          key              = "${listener_key}-${rule_idx}"
          listener_key     = listener_key
          priority         = rule.priority
          conditions       = rule.conditions
          actions          = rule.actions
        }
      ]
    ]) : rule.key => rule
  }
  
  listener_arn = aws_lb_listener.listeners[each.value.listener_key].arn
  priority     = each.value.priority
  
  dynamic "condition" {
    for_each = each.value.conditions
    content {
      dynamic "path_pattern" {
        for_each = lookup(condition.value, "path_pattern", null) != null ? [condition.value.path_pattern] : []
        content {
          values = path_pattern.value
        }
      }
      
      dynamic "host_header" {
        for_each = lookup(condition.value, "host_header", null) != null ? [condition.value.host_header] : []
        content {
          values = host_header.value
        }
      }
      
      dynamic "http_header" {
        for_each = lookup(condition.value, "http_header", null) != null ? [condition.value.http_header] : []
        content {
          http_header_name = http_header.value.name
          values           = http_header.value.values
        }
      }
      
      dynamic "query_string" {
        for_each = lookup(condition.value, "query_string", null) != null ? [condition.value.query_string] : []
        content {
          key   = lookup(query_string.value, "key", null)
          value = query_string.value.value
        }
      }
    }
  }
  
  dynamic "action" {
    for_each = each.value.actions
    content {
      type = action.value.type
      
      dynamic "forward" {
        for_each = action.value.type == "forward" ? [1] : []
        content {
          target_group {
            arn = aws_lb_target_group.services[action.value.target_group_key].arn
          }
        }
      }
    }
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-${each.key}-rule"
    }
  )
}

#-----------------------------------------
# ECS Services
#-----------------------------------------
resource "aws_ecs_service" "services" {
  for_each = var.service_configs
  
  name                               = "${local.name_prefix}-${each.value.name}"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.services[each.key].arn
  desired_count                      = each.value.desired_count
  deployment_maximum_percent         = each.value.deployment_maximum_percent
  deployment_minimum_healthy_percent = each.value.deployment_minimum_healthy_percent
  health_check_grace_period_seconds  = contains(local.lb_services, each.key) ? each.value.health_check_grace_period_seconds : null
  launch_type                        = each.value.launch_type
  scheduling_strategy                = each.value.scheduling_strategy
  force_new_deployment               = each.value.force_new_deployment
  wait_for_steady_state              = each.value.wait_for_steady_state
  enable_execute_command             = each.value.enable_execute_command
  propagate_tags                     = each.value.propagate_tags
  
  # Only add load balancer integration if this service has a target group
  dynamic "load_balancer" {
    for_each = contains(local.lb_services, each.key) ? [1] : []
    content {
      target_group_arn = aws_lb_target_group.services[each.key].arn
      container_name   = each.key
      container_port   = var.target_group_configs[each.key].port
    }
  }
  
  # Configure deployment controller
  deployment_controller {
    type = each.value.deployment_controller_type
  }
  
  # Configure circuit breaker if specified
  dynamic "deployment_circuit_breaker" {
    for_each = each.value.deployment_circuit_breaker != null ? [each.value.deployment_circuit_breaker] : []
    content {
      enable   = deployment_circuit_breaker.value.enable
      rollback = deployment_circuit_breaker.value.rollback
    }
  }
  
  # Configure placement strategies if specified
  dynamic "ordered_placement_strategy" {
    for_each = each.value.ordered_placement_strategy != null ? each.value.ordered_placement_strategy : []
    content {
      type  = ordered_placement_strategy.value.type
      field = ordered_placement_strategy.value.field
    }
  }
  
  # Network configuration for Fargate
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.security_group_ids[each.key]]
    assign_public_ip = false
  }
  
  tags = merge(
    local.common_tags,
    {
      Name    = "${local.name_prefix}-${each.value.name}-service"
      Service = each.key
    }
  )
  
  # Prevent changes in task definition from affecting the service if using CodeDeploy
  lifecycle {
    ignore_changes = each.value.deployment_controller_type == "CODE_DEPLOY" ? [task_definition] : []
  }
}

#-----------------------------------------
# Auto-scaling
#-----------------------------------------
resource "aws_appautoscaling_target" "ecs_targets" {
  for_each = var.scaling_targets
  
  service_namespace  = "ecs"
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.services[each.key].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  min_capacity       = each.value.min_capacity
  max_capacity       = each.value.max_capacity
}

resource "aws_appautoscaling_policy" "ecs_policies" {
  for_each = var.scaling_policies
  
  name               = "${local.name_prefix}-${each.key}-scaling-policy"
  policy_type        = each.value.policy_type
  resource_id        = aws_appautoscaling_target.ecs_targets[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_targets[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_targets[each.key].service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = each.value.predefined_metric_type
    }
    
    target_value       = each.value.target_value
    scale_in_cooldown  = each.value.scale_in_cooldown
    scale_out_cooldown = each.value.scale_out_cooldown
    disable_scale_in   = each.value.disable_scale_in
  }
}

# Scheduled auto-scaling actions
resource "aws_appautoscaling_scheduled_action" "scheduled_actions" {
  for_each = {
    for idx, action in flatten([
      for service_key, service in var.scaling_policies : [
        for action in lookup(service, "scheduled_actions", []) : {
          key           = "${service_key}-${action.name}"
          service_key   = service_key
          name          = action.name
          schedule      = action.schedule
          min_capacity  = lookup(action, "min_capacity", null)
          max_capacity  = lookup(action, "max_capacity", null)
          desired_count = lookup(action, "desired_count", null)
        }
      ]
    ]) : action.key => action
  }
  
  name               = each.value.name
  resource_id        = aws_appautoscaling_target.ecs_targets[each.value.service_key].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_targets[each.value.service_key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_targets[each.value.service_key].service_namespace
  schedule           = each.value.schedule
  
  scalable_target_action {
    min_capacity = each.value.min_capacity
    max_capacity = each.value.max_capacity
  }
}

#-----------------------------------------
# CloudWatch Alarms
#-----------------------------------------
resource "aws_cloudwatch_metric_alarm" "service_alarms" {
  for_each = var.alarm_configs
  
  alarm_name                = "${local.name_prefix}-${each.key}"
  comparison_operator       = each.value.comparison_operator
  evaluation_periods        = each.value.evaluation_periods
  metric_name               = each.value.metric_name
  namespace                 = each.value.namespace
  period                    = each.value.period
  statistic                 = each.value.statistic
  threshold                 = each.value.threshold
  alarm_description         = each.value.alarm_description
  alarm_actions             = each.value.alarm_actions
  insufficient_data_actions = each.value.insufficient_data_actions
  dimensions                = each.value.dimensions
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-${each.key}-alarm"
    }
  )
}

#-----------------------------------------
# Outputs
#-----------------------------------------
output "cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "frontend_service_name" {
  description = "Name of the frontend ECS service"
  value       = aws_ecs_service.services["frontend"].name
}

output "backend_service_name" {
  description = "Name of the backend API ECS service"
  value       = aws_ecs_service.services["api"].name
}

output "molecule_service_name" {
  description = "Name of the molecule service ECS service"
  value       = aws_ecs_service.services["molecule"].name
}

output "worker_service_name" {
  description = "Name of the worker ECS service"
  value       = aws_ecs_service.services["worker"].name
}

output "frontend_service_arn" {
  description = "ARN of the frontend ECS service"
  value       = aws_ecs_service.services["frontend"].id
}

output "backend_service_arn" {
  description = "ARN of the backend API ECS service"
  value       = aws_ecs_service.services["api"].id
}

output "molecule_service_arn" {
  description = "ARN of the molecule service ECS service"
  value       = aws_ecs_service.services["molecule"].id
}

output "worker_service_arn" {
  description = "ARN of the worker ECS service"
  value       = aws_ecs_service.services["worker"].id
}

output "alb_id" {
  description = "ID of the Application Load Balancer"
  value       = aws_lb.main.id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "target_group_arns" {
  description = "Map of service names to target group ARNs"
  value       = { for key, tg in aws_lb_target_group.services : key => tg.arn }
}

output "cloudwatch_log_groups" {
  description = "Map of service names to CloudWatch log group names"
  value       = { for key, log_group in aws_cloudwatch_log_group.ecs_logs : key => log_group.name }
}

output "autoscaling_target_ids" {
  description = "Map of service names to auto-scaling target IDs"
  value       = { for key, target in aws_appautoscaling_target.ecs_targets : key => target.resource_id }
}