# Network infrastructure variables
variable "vpc_id" {
  description = "ID of the VPC where compute resources will be created"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for the load balancer"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS services"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Map of security group IDs for different services"
  type        = map(string)
}

# ECS Cluster variables
variable "cluster_name" {
  description = "Name of the ECS cluster to create"
  type        = string
  default     = "moleculeflow-cluster"
}

variable "cluster_settings" {
  description = "Map of ECS cluster settings"
  type        = map(string)
  default = {
    "containerInsights" = "enabled"
  }
}

# Task definition variables
variable "task_definitions" {
  description = "Map of task definitions for each service"
  type = map(object({
    cpu                      = string
    memory                   = string
    requires_compatibilities = list(string)
    network_mode             = string
    execution_role_arn       = string
    task_role_arn            = string
    container_definitions    = string
    ephemeral_storage        = optional(number, null)
    volumes = optional(list(object({
      name = string
      efs_volume_configuration = optional(object({
        file_system_id     = string
        root_directory     = optional(string)
        transit_encryption = optional(string)
      }))
    })), [])
  }))
  default = {
    frontend = {
      cpu                      = "512"
      memory                   = "1024"
      requires_compatibilities = ["FARGATE"]
      network_mode             = "awsvpc"
      execution_role_arn       = ""
      task_role_arn            = ""
      container_definitions    = ""
      ephemeral_storage        = 20
    }
    api = {
      cpu                      = "1024"
      memory                   = "2048"
      requires_compatibilities = ["FARGATE"]
      network_mode             = "awsvpc"
      execution_role_arn       = ""
      task_role_arn            = ""
      container_definitions    = ""
      ephemeral_storage        = 20
    }
    molecule = {
      cpu                      = "2048"
      memory                   = "4096"
      requires_compatibilities = ["FARGATE"]
      network_mode             = "awsvpc"
      execution_role_arn       = ""
      task_role_arn            = ""
      container_definitions    = ""
      ephemeral_storage        = 50
    }
    worker = {
      cpu                      = "2048"
      memory                   = "8192"
      requires_compatibilities = ["FARGATE"]
      network_mode             = "awsvpc"
      execution_role_arn       = ""
      task_role_arn            = ""
      container_definitions    = ""
      ephemeral_storage        = 50
    }
  }
}

# Service configuration variables
variable "service_configs" {
  description = "Map of service configurations"
  type = map(object({
    name                               = string
    desired_count                      = number
    deployment_maximum_percent         = number
    deployment_minimum_healthy_percent = number
    health_check_grace_period_seconds  = number
    deployment_controller_type         = string
    enable_execute_command             = bool
    launch_type                        = string
    scheduling_strategy                = string
    force_new_deployment               = bool
    wait_for_steady_state              = bool
    propagate_tags                     = string
    ordered_placement_strategy = optional(list(object({
      type  = string
      field = string
    })), [])
    deployment_circuit_breaker = optional(object({
      enable   = bool
      rollback = bool
    }), null)
  }))
  default = {
    frontend = {
      name                               = "frontend"
      desired_count                      = 2
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
      desired_count                      = 2
      deployment_maximum_percent         = 200
      deployment_minimum_healthy_percent = 100
      health_check_grace_period_seconds  = 60
      deployment_controller_type         = "CODE_DEPLOY"
      enable_execute_command             = true
      launch_type                        = "FARGATE"
      scheduling_strategy                = "REPLICA"
      force_new_deployment               = true
      wait_for_steady_state              = true
      propagate_tags                     = "SERVICE"
    }
    molecule = {
      name                               = "molecule"
      desired_count                      = 2
      deployment_maximum_percent         = 200
      deployment_minimum_healthy_percent = 100
      health_check_grace_period_seconds  = 60
      deployment_controller_type         = "CODE_DEPLOY"
      enable_execute_command             = true
      launch_type                        = "FARGATE"
      scheduling_strategy                = "REPLICA"
      force_new_deployment               = true
      wait_for_steady_state              = true
      propagate_tags                     = "SERVICE"
    }
    worker = {
      name                               = "worker"
      desired_count                      = 2
      deployment_maximum_percent         = 200
      deployment_minimum_healthy_percent = 100
      health_check_grace_period_seconds  = 0
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
}

# Load balancer variables
variable "alb_config" {
  description = "Configuration for the Application Load Balancer"
  type = object({
    name                       = string
    internal                   = bool
    load_balancer_type         = string
    enable_deletion_protection = bool
    idle_timeout               = number
    enable_http2               = bool
    enable_cross_zone_load_balancing = bool
    access_logs = object({
      enabled = bool
      bucket  = string
      prefix  = string
    })
  })
  default = {
    name                       = "moleculeflow-alb"
    internal                   = false
    load_balancer_type         = "application"
    enable_deletion_protection = false
    idle_timeout               = 60
    enable_http2               = true
    enable_cross_zone_load_balancing = true
    access_logs = {
      enabled = false
      bucket  = ""
      prefix  = ""
    }
  }
}

variable "target_group_configs" {
  description = "Configuration for target groups"
  type = map(object({
    port                 = number
    protocol             = string
    target_type          = string
    deregistration_delay = number
    slow_start           = number
    health_check = object({
      enabled             = bool
      path                = string
      port                = string
      protocol            = string
      healthy_threshold   = number
      unhealthy_threshold = number
      timeout             = number
      interval            = number
      matcher             = string
    })
    stickiness = object({
      enabled         = bool
      type            = string
      cookie_duration = number
    })
  }))
  default = {
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
}

variable "listener_configs" {
  description = "Configuration for ALB listeners"
  type = map(object({
    port            = number
    protocol        = string
    ssl_policy      = optional(string)
    certificate_arn = optional(string)
    default_action = object({
      type             = string
      target_group_key = optional(string)
      redirect = optional(object({
        port        = string
        protocol    = string
        status_code = string
      }))
    })
    rules = optional(list(object({
      priority   = number
      conditions = list(map(any))
      actions = list(object({
        type             = string
        target_group_key = optional(string)
      }))
    })), [])
  }))
  default = {
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
      certificate_arn = null # Must be provided
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
}

# Auto-scaling variables
variable "scaling_targets" {
  description = "Configuration for auto-scaling targets"
  type = map(object({
    min_capacity = number
    max_capacity = number
  }))
  default = {
    frontend = {
      min_capacity = 2
      max_capacity = 10
    }
    api = {
      min_capacity = 2
      max_capacity = 20
    }
    molecule = {
      min_capacity = 2
      max_capacity = 20
    }
    worker = {
      min_capacity = 2
      max_capacity = 50
    }
  }
}

variable "scaling_policies" {
  description = "Configuration for auto-scaling policies"
  type = map(object({
    policy_type               = string
    predefined_metric_type    = string
    target_value              = number
    scale_in_cooldown         = number
    scale_out_cooldown        = number
    disable_scale_in          = bool
    scheduled_actions = optional(list(object({
      name                  = string
      schedule              = string
      min_capacity          = optional(number)
      max_capacity          = optional(number)
      desired_count         = optional(number)
    })), [])
  }))
  default = {
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
          min_capacity = 2
          max_capacity = 10
          desired_count = 5
        },
        {
          name         = "after-hours-scale-down"
          schedule     = "cron(0 18 ? * MON-FRI *)"
          min_capacity = 2
          max_capacity = 5
          desired_count = 2
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
          min_capacity = 5
          max_capacity = 50
          desired_count = 10
        }
      ]
    }
  }
}

variable "alarm_configs" {
  description = "Configuration for CloudWatch alarms"
  type = map(object({
    comparison_operator       = string
    evaluation_periods        = number
    metric_name               = string
    namespace                 = string
    period                    = number
    statistic                 = string
    threshold                 = number
    alarm_description         = string
    alarm_actions             = list(string)
    insufficient_data_actions = list(string)
    dimensions                = map(string)
  }))
  default = {}
}

# General variables
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  description = "Name of the project for resource naming"
  type        = string
  default     = "moleculeflow"
}

variable "tags" {
  description = "Map of tags to apply to all resources"
  type        = map(string)
  default     = {}
}