# ECS Cluster outputs
output "cluster_id" {
  description = "The ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_arn" {
  description = "The ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

# ECS Service name outputs
output "frontend_service_name" {
  description = "The name of the frontend ECS service"
  value       = aws_ecs_service.frontend.name
}

output "backend_service_name" {
  description = "The name of the backend API ECS service"
  value       = aws_ecs_service.backend.name
}

output "molecule_service_name" {
  description = "The name of the molecule service ECS service"
  value       = aws_ecs_service.molecule.name
}

output "worker_service_name" {
  description = "The name of the worker ECS service"
  value       = aws_ecs_service.worker.name
}

# ECS Service ARN outputs
output "frontend_service_arn" {
  description = "The ARN of the frontend ECS service"
  value       = aws_ecs_service.frontend.id
}

output "backend_service_arn" {
  description = "The ARN of the backend API ECS service"
  value       = aws_ecs_service.backend.id
}

output "molecule_service_arn" {
  description = "The ARN of the molecule service ECS service"
  value       = aws_ecs_service.molecule.id
}

output "worker_service_arn" {
  description = "The ARN of the worker ECS service"
  value       = aws_ecs_service.worker.id
}

# Application Load Balancer outputs
output "alb_id" {
  description = "The ID of the Application Load Balancer"
  value       = aws_lb.main.id
}

output "alb_arn" {
  description = "The ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "The DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "The Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

# Target Group outputs
output "target_group_arns" {
  description = "Map of service names to target group ARNs"
  value = {
    frontend = aws_lb_target_group.frontend.arn
    backend  = aws_lb_target_group.backend.arn
    molecule = aws_lb_target_group.molecule.arn
  }
}

# CloudWatch Log Group outputs
output "cloudwatch_log_groups" {
  description = "Map of service names to CloudWatch log group names"
  value = {
    frontend = aws_cloudwatch_log_group.frontend.name
    backend  = aws_cloudwatch_log_group.backend.name
    molecule = aws_cloudwatch_log_group.molecule.name
    worker   = aws_cloudwatch_log_group.worker.name
  }
}

# Auto-scaling Target outputs
output "autoscaling_target_ids" {
  description = "Map of service names to auto-scaling target IDs"
  value = {
    frontend = aws_appautoscaling_target.frontend.resource_id
    backend  = aws_appautoscaling_target.backend.resource_id
    molecule = aws_appautoscaling_target.molecule.resource_id
    worker   = aws_appautoscaling_target.worker.resource_id
  }
}